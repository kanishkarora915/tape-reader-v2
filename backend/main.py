"""
BuyBy Trading System — FastAPI Application
Routes: OAuth login/callback, engine data, signals, option chain, WebSocket.
Serves React frontend static build in production.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config import (
    KITE_API_KEY, KITE_API_SECRET, IS_PROD, PORT, FRONTEND_DIST, INDEX_CONFIG,
)
from auth import AuthManager
from ws_manager import WSManager
from db import init_db, close_db, fetch
from market_engine import MarketEngine
from trade_tracker import TradeTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("buyby")

# ── Global State ────────────────────────────────────────────────────────

auth_manager: AuthManager | None = None
ws_manager: WSManager | None = None
market_engine: MarketEngine | None = None
trade_tracker: TradeTracker | None = None


# ── Lifespan ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global auth_manager, ws_manager, trade_tracker
    await init_db()
    auth_manager = AuthManager()
    ws_manager = WSManager()
    trade_tracker = TradeTracker()
    logger.info("[BUYBY] Backend started")
    # Start demo broadcaster (sends data to WS clients when no live engine)
    from demo_data import run_demo_broadcast
    asyncio.create_task(run_demo_broadcast(
        ws_manager,
        is_live_fn=lambda: market_engine is not None,
        engine_has_data_fn=lambda: bool(market_engine and market_engine.engine_results and any(
            r.get("verdict") != "NEUTRAL" for r in market_engine.engine_results.values() if isinstance(r, dict)
        )),
    ))
    logger.info("[BUYBY] Demo data broadcaster started")
    yield
    if market_engine:
        market_engine.stop()
    await close_db()
    logger.info("[BUYBY] Backend shutdown")


app = FastAPI(title="BuyBy Trading System", lifespan=lifespan)

# ── CORS ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ──────────────────────────────────────────────────────────────

def get_frontend_url(request: Request) -> str:
    if IS_PROD:
        return str(request.base_url).rstrip("/")
    return "http://localhost:5173"


# ── Auth Routes ─────────────────────────────────────────────────────────

@app.post("/api/login")
async def login():
    """Create a Kite login session using env credentials."""
    api_key = KITE_API_KEY
    api_secret = KITE_API_SECRET

    if not api_key or not api_secret:
        return JSONResponse(
            {"error": "KITE_API_KEY and KITE_API_SECRET not configured"},
            status_code=400,
        )

    session_id, login_url = auth_manager.create_session(api_key, api_secret)
    response = JSONResponse({"login_url": login_url, "session_id": session_id})
    response.set_cookie("buyby_session", session_id, httponly=True, samesite="lax", secure=IS_PROD, max_age=86400)
    return response


@app.get("/api/callback")
async def callback(
    request: Request,
    request_token: str = Query(...),
    session_id: str = Query(None),
    buyby_session: str = Cookie(None),
):
    """Complete Kite OAuth callback."""
    global market_engine
    fe_url = get_frontend_url(request)
    sid = session_id or buyby_session

    # Fallback: if no session_id from cookie/param, use the most recent session
    if not sid and auth_manager.sessions:
        sid = list(auth_manager.sessions.keys())[-1]
        logger.info(f"[AUTH] Using last session: {sid[:8]}...")

    if not sid:
        return RedirectResponse(f"{fe_url}/?auth=failed&reason=no_session")

    try:
        access_token = auth_manager.complete_login(sid, request_token)
        sess = auth_manager.get_session(sid)
        logger.info(f"[AUTH] Login OK. Token: {access_token[:8]}...")

        # Give kite instance to last-session fetcher for real data
        from demo_data import fetcher
        fetcher.set_kite(sess["kite"])

        # Start market engine
        from engines import engine_registry
        market_engine = MarketEngine(
            kite=sess["kite"],
            ws_manager=ws_manager,
            engine_registry=engine_registry,
            trade_tracker=trade_tracker,
        )
        await market_engine.start()

        response = RedirectResponse(f"{fe_url}/?auth=success")
        response.set_cookie("buyby_session", sid, httponly=True, samesite="lax", secure=IS_PROD, max_age=86400)
        return response

    except Exception as e:
        logger.error(f"[AUTH] Login failed: {e}")
        return RedirectResponse(f"{fe_url}/?auth=failed&reason={str(e)}")


@app.get("/api/dev-login")
async def dev_login(response: Response):
    """Dev-only: bypass OAuth for dashboard preview."""
    global market_engine
    # Stop stale engine so demo broadcaster takes over
    if market_engine:
        market_engine.stop()
        market_engine = None
        logger.info("[DEV] Stopped stale market engine for demo mode")
    sid = auth_manager.create_dev_session()
    response = RedirectResponse("/")
    response.set_cookie("buyby_session", sid, httponly=True, samesite="lax", secure=IS_PROD, max_age=86400)
    return response


@app.get("/api/status")
async def get_status(buyby_session: str = Cookie(None)):
    """Check authentication and engine status."""
    sess = auth_manager.get_session(buyby_session) if buyby_session else None
    authenticated = sess is not None and sess.get("access_token") is not None

    return {
        "authenticated": authenticated,
        "user": sess.get("user_name", "Trader") if authenticated else None,
        "instruments": list(INDEX_CONFIG.keys()) if authenticated else [],
        "engine_running": market_engine is not None,
        "ws_clients": ws_manager.client_count if ws_manager else 0,
    }


@app.post("/api/logout")
async def logout(buyby_session: str = Cookie(None)):
    """Logout and clean up session."""
    global market_engine

    if market_engine:
        market_engine.stop()
        market_engine = None

    if buyby_session:
        auth_manager.remove_session(buyby_session)

    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie("buyby_session")
    return response


# ── Data Routes ─────────────────────────────────────────────────────────

@app.get("/api/debug")
async def debug_info():
    """Debug endpoint — shows engine internals."""
    if not market_engine:
        return {"engine": None}
    return {
        "engine_running": market_engine._running,
        "prices_count": len(market_engine.prices),
        "chains_count": {k: len(v) for k, v in market_engine.chains.items()},
        "instruments_count": len(market_engine.instruments),
        "engine_results_count": len(market_engine.engine_results),
        "candle_count": len(market_engine._candle_history),
        "has_ticker": market_engine._ticker is not None,
        "sample_prices": {k: v.get("last_price", 0) for k, v in list(market_engine.prices.items())[:3]},
    }


@app.get("/api/engines")
async def get_engines():
    """Return all 24 engine states."""
    if not market_engine:
        return JSONResponse({"error": "Engine not running"}, status_code=503)
    try:
        # Ensure all values are JSON-serializable
        import json
        safe_results = {}
        for eid, result in market_engine.engine_results.items():
            if isinstance(result, dict):
                safe_results[eid] = result
            else:
                safe_results[eid] = {"name": str(eid), "tier": 0, "verdict": "NEUTRAL", "direction": "NEUTRAL", "confidence": 0, "data": {}}
        return {"engines": safe_results}
    except Exception as e:
        logger.error(f"[API] /api/engines error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/signals")
async def get_signals():
    """Return recent signals from database."""
    rows = await fetch(
        "SELECT * FROM signals ORDER BY created_at DESC LIMIT 50"
    )
    return {"signals": rows}


@app.get("/api/chain/{index}")
async def get_chain(index: str):
    """Return current option chain for an index."""
    if not market_engine:
        return JSONResponse({"error": "Engine not running"}, status_code=503)

    idx = index.upper()
    chain = market_engine.chains.get(idx, {})
    return {"index": idx, "chain": chain}


# ── Trade Routes ───────────────────────────────────────────────────────

@app.get("/api/trades")
async def get_trades():
    """Get today's trade log."""
    return {"trades": trade_tracker.get_today_trades()}


@app.get("/api/trade-stats")
async def get_trade_stats():
    """Get trade statistics and learning insights."""
    return trade_tracker.get_stats()


# ── WebSocket ───────────────────────────────────────────────────────────

@app.websocket("/ws/buyby")
async def websocket_buyby(ws: WebSocket):
    """Main WebSocket endpoint for real-time data."""
    await ws_manager.connect(ws)
    logger.info("[WS] Client connected")

    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"[WS] Error: {e}")
    finally:
        ws_manager.disconnect(ws)


# ── Static File Serving (Production) ────────────────────────────────────

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return JSONResponse({"error": "Not found"}, status_code=404)

        # Try to serve the exact file first
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))

        # SPA fallback
        return FileResponse(str(FRONTEND_DIST / "index.html"))


# ── Run ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=not IS_PROD)
