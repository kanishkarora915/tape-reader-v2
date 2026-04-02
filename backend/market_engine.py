"""
BuyBy Trading System — Market Data Engine
Connects to KiteTicker for real-time data, runs 24 engines in a loop,
and broadcasts results via WebSocket.
"""

import asyncio
import logging
import time
import threading
from datetime import date, datetime, timedelta, timezone

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

        # Candle builder
        self._candle_history = []  # list of OHLCV dicts
        self._current_candle = None
        self._candle_interval = 300  # 5 minutes
        self._last_candle_time = 0

        # Placeholders for future data sources
        self._fii_data = {}

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
        nifty_spot_token = INDEX_CONFIG["NIFTY"]["spot_token"]

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

            # Candle builder for NIFTY spot
            if token == nifty_spot_token:
                ltp = tick.get("last_price", 0)
                now = time.time()
                if self._current_candle is None:
                    self._current_candle = {"open": ltp, "high": ltp, "low": ltp, "close": ltp, "volume": 0, "ts": now}
                    self._last_candle_time = now
                else:
                    self._current_candle["high"] = max(self._current_candle["high"], ltp)
                    self._current_candle["low"] = min(self._current_candle["low"], ltp)
                    self._current_candle["close"] = ltp
                    self._current_candle["volume"] += tick.get("volume_traded", 0)

                    if now - self._last_candle_time >= self._candle_interval:
                        self._candle_history.append(self._current_candle.copy())
                        if len(self._candle_history) > 200:
                            self._candle_history = self._candle_history[-200:]
                        self._current_candle = {"open": ltp, "high": ltp, "low": ltp, "close": ltp, "volume": 0, "ts": now}
                        self._last_candle_time = now

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
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Add spot prices + change data
                for idx_name, cfg in INDEX_CONFIG.items():
                    spot_tick = self.prices.get(cfg["spot_token"], {})
                    ltp = spot_tick.get("last_price", 0)
                    ohlc = spot_tick.get("ohlc", {})
                    prev_close = ohlc.get("close", ltp) or ltp
                    change = ltp - prev_close if ltp and prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close else 0
                    prefix = idx_name.lower()
                    context[f"{prefix}_spot"] = ltp
                    context[f"{prefix}_change"] = round(change, 2)
                    context[f"{prefix}_change_pct"] = round(change_pct, 2)
                    context[f"{prefix}_high"] = ohlc.get("high", ltp)
                    context[f"{prefix}_low"] = ohlc.get("low", ltp)

                # --- Flatten NIFTY chain for engines ---
                flat_chain = {}
                nifty_chain = self.chains.get("NIFTY", {})
                for strike, data in nifty_chain.items():
                    ce = data.get("ce", {})
                    pe = data.get("pe", {})
                    flat_chain[strike] = {
                        "strike": strike,
                        "ce_oi": ce.get("oi", 0),
                        "pe_oi": pe.get("oi", 0),
                        "ce_ltp": ce.get("ltp", 0),
                        "pe_ltp": pe.get("ltp", 0),
                        "ce_chg": ce.get("change_oi", 0),
                        "pe_chg": pe.get("change_oi", 0),
                        "ce_volume": ce.get("volume", 0),
                        "pe_volume": pe.get("volume", 0),
                        "ce_iv": 0,
                        "pe_iv": 0,
                    }

                # Spot price in prices dict (engines expect this)
                nifty_spot = context.get("nifty_spot", 0)
                nifty_tick_data = self.prices.get(INDEX_CONFIG["NIFTY"]["spot_token"], {})
                nifty_ohlc = nifty_tick_data.get("ohlc", {})
                context["prices"]["spot"] = nifty_spot
                context["prices"]["ltp"] = nifty_spot
                context["prices"]["change_pct"] = context.get("nifty_change_pct", 0)
                context["prices"]["prev_close"] = nifty_ohlc.get("close", nifty_spot) or nifty_spot

                # Flat chain
                context["chains"] = flat_chain

                # Previous engine results
                context["previous_results"] = dict(self.engine_results)

                # ATM strike
                gap = 50
                atm = round(nifty_spot / gap) * gap if nifty_spot else 0
                context["atm_strike"] = atm
                context["spot"] = nifty_spot

                # VIX as both float and dict (engines use both formats)
                vix_val = self.prices.get(VIX_TOKEN, {}).get("last_price", 0)
                context["vix"] = vix_val
                context["vix_data"] = {
                    "current": vix_val,
                    "open": self.prices.get(VIX_TOKEN, {}).get("ohlc", {}).get("open", vix_val),
                }

                # Days to expiry (approximate — next Thursday)
                today = date.today()
                days_ahead = (3 - today.weekday()) % 7  # Thursday
                if days_ahead == 0:
                    days_ahead = 0  # It's Thursday
                context["days_to_expiry"] = days_ahead
                context["dte"] = days_ahead

                # Lot sizes
                context["lot_size"] = 25  # NIFTY lot

                # Candles — provide both list format and dict format for engine compat
                candle_list = list(self._candle_history)
                context["candles"] = {
                    "open": [c["open"] for c in candle_list],
                    "high": [c["high"] for c in candle_list],
                    "low": [c["low"] for c in candle_list],
                    "close": [c["close"] for c in candle_list],
                    "volume": [c["volume"] for c in candle_list],
                }
                context["candle_list"] = candle_list  # raw list for engines that want it
                context["candles_15m"] = []
                context["candles_1h"] = []
                context["daily_candles"] = []

                # Depth data — extract from NIFTY spot tick
                nifty_tick = self.prices.get(INDEX_CONFIG["NIFTY"]["spot_token"], {})
                raw_depth = nifty_tick.get("depth", {})
                depth_bids = []
                depth_asks = []
                for b in raw_depth.get("buy", []):
                    if b.get("price", 0) > 0:
                        depth_bids.append({"price": b["price"], "qty": b.get("quantity", 0)})
                for a in raw_depth.get("sell", []):
                    if a.get("price", 0) > 0:
                        depth_asks.append({"price": a["price"], "qty": a.get("quantity", 0)})
                context["depth"] = {"bids": depth_bids, "asks": depth_asks}

                # FII/DII placeholder
                context["fii_dii"] = getattr(self, '_fii_data', {})

                # Cross assets placeholder (engines have VIX fallback)
                context["cross_assets"] = {}

                # Pre-market placeholder (engines have VIX+spot fallback)
                context["premarket"] = {}
                context["global_cues"] = {}  # dict, not list — e23 expects dict

                # Run all engines
                for engine_id, engine_inst in self.engine_registry.items():
                    try:
                        engine_inst.run(context)
                        self.engine_results[engine_id] = engine_inst.get_state()
                    except Exception as e:
                        self.engine_results[engine_id] = {
                            "name": getattr(engine_inst, 'name', engine_id),
                            "tier": getattr(engine_inst, 'tier', 0),
                            "verdict": "NEUTRAL",
                            "direction": "NEUTRAL",
                            "confidence": 0,
                            "data": {"error": str(e)},
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

                # Broadcast option chain as array for frontend
                chain_array = sorted(flat_chain.values(), key=lambda r: r.get("strike", 0))
                # Mark ATM row
                for row in chain_array:
                    row["atm"] = (row.get("strike", 0) == atm)
                if chain_array:
                    # Compute max pain
                    max_pain = atm
                    min_pain_val = float("inf")
                    for row in chain_array:
                        pain = sum(
                            max(0, row["strike"] - r["strike"]) * r.get("pe_oi", 0) +
                            max(0, r["strike"] - row["strike"]) * r.get("ce_oi", 0)
                            for r in chain_array
                        )
                        if pain < min_pain_val:
                            min_pain_val = pain
                            max_pain = row["strike"]

                    await self.ws_manager.broadcast("chain", chain_array, index="NIFTY", max_pain=max_pain)

                    # Also broadcast BANKNIFTY and SENSEX chains if available
                    for idx in ("BANKNIFTY", "SENSEX"):
                        idx_chain = self.chains.get(idx, {})
                        if idx_chain:
                            idx_array = []
                            for strike, data in idx_chain.items():
                                ce = data.get("ce", {})
                                pe = data.get("pe", {})
                                idx_spot = context.get(f"{idx.lower()}_spot", 0)
                                idx_gap = 100
                                idx_atm = round(idx_spot / idx_gap) * idx_gap if idx_spot else 0
                                idx_array.append({
                                    "strike": strike, "atm": (strike == idx_atm),
                                    "ce_oi": ce.get("oi", 0), "pe_oi": pe.get("oi", 0),
                                    "ce_ltp": ce.get("ltp", 0), "pe_ltp": pe.get("ltp", 0),
                                    "ce_chg": ce.get("change_oi", 0), "pe_chg": pe.get("change_oi", 0),
                                    "ce_volume": ce.get("volume", 0), "pe_volume": pe.get("volume", 0),
                                    "ce_iv": 0, "pe_iv": 0,
                                })
                            idx_array.sort(key=lambda r: r.get("strike", 0))
                            await self.ws_manager.broadcast("chain", idx_array, index=idx)

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
