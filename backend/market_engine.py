"""
BuyBy Trading System — Market Data Engine
Connects to KiteTicker for real-time data, runs 24 engines in a loop,
and broadcasts results via WebSocket.
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone

from kiteconnect import KiteConnect, KiteTicker

from config import INDEX_CONFIG, VIX_TOKEN
from ws_manager import WSManager
from signal_combiner import SignalCombiner

logger = logging.getLogger("buyby.engine")


class MarketEngine:
    """
    Core market data engine.
    - Connects KiteTicker for spot, VIX, and option chain tokens
    - Runs all 24 engines every 5 seconds
    - Broadcasts results to WebSocket clients
    """

    def __init__(self, kite: KiteConnect, ws_manager: WSManager, engine_registry: dict):
        self.kite = kite
        self.ws_manager = ws_manager
        self.engine_registry = engine_registry  # dict of engine_id -> engine_class
        self.combiner = SignalCombiner()

        # State
        self.prices: dict = {}          # token -> last tick data
        self.chains: dict = {}          # index -> {strike: {ce: ..., pe: ...}}
        self.engine_results: dict = {}  # engine_id -> result dict
        self.instruments: dict = {}     # token -> instrument info

        # Ticker
        self._ticker: KiteTicker | None = None
        self._ticker_thread: threading.Thread | None = None
        self._engine_task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False

    async def start(self) -> None:
        """Start KiteTicker and engine loop."""
        self._loop = asyncio.get_event_loop()
        self._running = True

        # Fetch instrument tokens
        all_tokens = [VIX_TOKEN]
        for idx_name, cfg in INDEX_CONFIG.items():
            all_tokens.append(cfg["spot_token"])
            try:
                chain_tokens = self.get_option_chain_tokens(self.kite, idx_name)
                all_tokens.extend(chain_tokens)
                logger.info(f"[ENGINE] {idx_name}: {len(chain_tokens)} option tokens loaded")
            except Exception as e:
                logger.error(f"[ENGINE] Failed to load {idx_name} tokens: {e}")

        # Start KiteTicker in background thread
        self._start_ticker(all_tokens)

        # Start engine loop
        self._engine_task = asyncio.create_task(self._engine_loop())
        logger.info("[ENGINE] Market engine started")

    def stop(self) -> None:
        """Stop ticker and engine loop."""
        self._running = False

        if self._engine_task:
            self._engine_task.cancel()
            self._engine_task = None

        if self._ticker:
            try:
                self._ticker.close()
            except Exception:
                pass
            self._ticker = None

        logger.info("[ENGINE] Market engine stopped")

    def _start_ticker(self, tokens: list[int]) -> None:
        """Start KiteTicker in a background thread."""
        api_key = self.kite.api_key
        access_token = self.kite.access_token

        self._ticker = KiteTicker(api_key, access_token)
        self._ticker.on_ticks = self._on_ticks
        self._ticker.on_connect = self._on_connect
        self._ticker.on_close = self._on_close

        self._subscribe_tokens = tokens

        self._ticker_thread = threading.Thread(
            target=self._ticker.connect, kwargs={"threaded": True}, daemon=True
        )
        self._ticker_thread.start()

    def _on_connect(self, ws, response) -> None:
        """Subscribe to instrument tokens on connect."""
        logger.info(f"[TICKER] Connected. Subscribing to {len(self._subscribe_tokens)} tokens")
        ws.subscribe(self._subscribe_tokens)
        ws.set_mode(ws.MODE_FULL, self._subscribe_tokens)

    def _on_ticks(self, ws, ticks) -> None:
        """Process incoming ticks — update prices and chains."""
        for tick in ticks:
            token = tick.get("instrument_token")
            if not token:
                continue

            self.prices[token] = tick

            # Update option chain data
            inst = self.instruments.get(token)
            if inst and inst.get("instrument_type") in ("CE", "PE"):
                idx = inst["index"]
                strike = inst["strike"]
                opt_type = inst["instrument_type"].lower()

                if idx not in self.chains:
                    self.chains[idx] = {}
                if strike not in self.chains[idx]:
                    self.chains[idx][strike] = {"strike": strike, "ce": {}, "pe": {}}

                self.chains[idx][strike][opt_type] = {
                    "ltp": tick.get("last_price", 0),
                    "oi": tick.get("oi", 0),
                    "volume": tick.get("volume_traded", 0),
                    "bid": tick.get("depth", {}).get("buy", [{}])[0].get("price", 0),
                    "ask": tick.get("depth", {}).get("sell", [{}])[0].get("price", 0),
                    "change_oi": tick.get("oi_day_high", 0) - tick.get("oi_day_low", 0),
                }

    def _on_close(self, ws, code, reason) -> None:
        """Handle ticker disconnect."""
        logger.warning(f"[TICKER] Closed: {code} — {reason}")

    async def _engine_loop(self) -> None:
        """Run all engines every 5 seconds and broadcast results."""
        while self._running:
            try:
                # Build engine context
                context = {
                    "prices": self.prices.copy(),
                    "chains": dict(self.chains),
                    "vix": self.prices.get(VIX_TOKEN, {}).get("last_price", 0),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Add spot prices
                for idx_name, cfg in INDEX_CONFIG.items():
                    spot_tick = self.prices.get(cfg["spot_token"], {})
                    context[f"{idx_name.lower()}_spot"] = spot_tick.get("last_price", 0)

                # Run all engines
                for engine_id, engine_cls in self.engine_registry.items():
                    try:
                        result = engine_cls.evaluate(context)
                        self.engine_results[engine_id] = result
                    except Exception as e:
                        self.engine_results[engine_id] = {
                            "id": engine_id,
                            "verdict": "ERROR",
                            "error": str(e),
                        }

                # Run signal combiner
                signal = self.combiner.combine(self.engine_results)

                # Broadcast to WebSocket clients
                await self.ws_manager.broadcast("engines", self.engine_results)
                await self.ws_manager.broadcast("tick", {
                    "nifty": {
                        "ltp": context.get("nifty_spot", 0),
                        "change": context.get("nifty_change", 0),
                        "changePct": context.get("nifty_change_pct", 0),
                        "high": context.get("nifty_high", 0),
                        "low": context.get("nifty_low", 0),
                    },
                    "banknifty": {
                        "ltp": context.get("banknifty_spot", 0),
                        "change": context.get("banknifty_change", 0),
                        "changePct": context.get("banknifty_change_pct", 0),
                        "high": context.get("banknifty_high", 0),
                        "low": context.get("banknifty_low", 0),
                    },
                    "sensex": {
                        "ltp": context.get("sensex_spot", 0),
                        "change": context.get("sensex_change", 0),
                        "changePct": context.get("sensex_change_pct", 0),
                        "high": context.get("sensex_high", 0),
                        "low": context.get("sensex_low", 0),
                    },
                    "vix": context.get("vix", 0),
                })

                if signal and signal.get("type") not in ("SKIP", "WAIT"):
                    await self.ws_manager.broadcast("signal", signal)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ENGINE] Loop error: {e}")

            await asyncio.sleep(5)

    def get_option_chain_tokens(self, kite: KiteConnect, index_name: str) -> list[int]:
        """
        Fetch instruments for an index, find nearest 2 expiries,
        return tokens for +/- 10 strikes from ATM.
        """
        cfg = INDEX_CONFIG[index_name]
        exchange = cfg["exchange"]
        strike_gap = cfg["strike_gap"]

        instruments = kite.instruments(exchange)

        # Filter for this index's options
        prefix = index_name if index_name != "SENSEX" else "SENSEX"
        options = [
            i for i in instruments
            if i["name"] == prefix
            and i["instrument_type"] in ("CE", "PE")
        ]

        if not options:
            return []

        # Get nearest 2 expiries
        expiries = sorted(set(i["expiry"] for i in options))
        target_expiries = expiries[:2]

        # Get spot price for ATM calculation
        spot_tick = self.prices.get(cfg["spot_token"], {})
        spot = spot_tick.get("last_price", 0)

        if spot == 0:
            # Use quote as fallback
            try:
                q = kite.quote([f"NSE:{index_name} 50"])
                spot = list(q.values())[0]["last_price"]
            except Exception:
                spot = 0

        if spot == 0:
            # Take all strikes if no spot available
            target_options = [i for i in options if i["expiry"] in target_expiries]
        else:
            # ATM strike
            atm = round(spot / strike_gap) * strike_gap
            low = atm - (10 * strike_gap)
            high = atm + (10 * strike_gap)

            target_options = [
                i for i in options
                if i["expiry"] in target_expiries
                and low <= i["strike"] <= high
            ]

        # Store instrument info and return tokens
        tokens = []
        for inst in target_options:
            token = inst["instrument_token"]
            self.instruments[token] = {
                "index": index_name,
                "strike": int(inst["strike"]),
                "expiry": inst["expiry"],
                "instrument_type": inst["instrument_type"],
                "tradingsymbol": inst["tradingsymbol"],
            }
            tokens.append(token)

        return tokens
