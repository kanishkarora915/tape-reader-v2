"""
E22 — Microstructure Engine (Tier 4: Big Move)
Bid-ask analysis from depth data.
  - Absorption: large sell orders absorbed without price fall = bullish
  - Order book imbalance > 70:30 = directional bias
  - Repeated refills at same level = iceberg order detection
"""

from .base import BaseEngine, EngineResult


class MicrostructureEngine(BaseEngine):
    name = "Microstructure"
    tier = 4
    refresh_seconds = 3

    def __init__(self):
        super().__init__()
        self._level_history = {}  # price_level -> [qty_snapshots]
        self._max_history = 30
        self._absorption_history = []  # track absorbed sell walls

    def _detect_absorption(self, depth: dict, price_change: float) -> dict:
        """Large sell orders absorbed without price fall = bullish.
        Large buy orders absorbed without price rise = bearish."""
        bids = depth.get("bids", [])  # [{price, qty}, ...]
        asks = depth.get("asks", [])

        if not bids or not asks:
            return {"detected": False, "side": "NONE"}

        total_bid_qty = sum(b.get("qty", 0) for b in bids)
        total_ask_qty = sum(a.get("qty", 0) for a in asks)

        # Absorption: heavy selling (large ask qty) but price didn't fall
        sell_pressure = total_ask_qty > total_bid_qty * 1.5
        buy_pressure = total_bid_qty > total_ask_qty * 1.5

        if sell_pressure and price_change >= 0:
            return {
                "detected": True,
                "side": "BULLISH",
                "absorbed_qty": total_ask_qty,
                "note": "Sell orders absorbed without price fall",
            }
        elif buy_pressure and price_change <= 0:
            return {
                "detected": True,
                "side": "BEARISH",
                "absorbed_qty": total_bid_qty,
                "note": "Buy orders absorbed without price rise",
            }

        return {"detected": False, "side": "NONE"}

    def _detect_imbalance(self, depth: dict) -> dict:
        """Order book imbalance > 70:30 = directional bias."""
        bids = depth.get("bids", [])
        asks = depth.get("asks", [])

        if not bids or not asks:
            return {"imbalanced": False, "ratio": 50}

        total_bid = sum(b.get("qty", 0) for b in bids)
        total_ask = sum(a.get("qty", 0) for a in asks)
        total = total_bid + total_ask

        if total <= 0:
            return {"imbalanced": False, "ratio": 50}

        bid_pct = (total_bid / total) * 100
        ask_pct = (total_ask / total) * 100

        imbalanced = max(bid_pct, ask_pct) > 70
        direction = "BULLISH" if bid_pct > ask_pct else "BEARISH"

        return {
            "imbalanced": imbalanced,
            "ratio": round(max(bid_pct, ask_pct), 1),
            "bid_pct": round(bid_pct, 1),
            "ask_pct": round(ask_pct, 1),
            "total_bid": total_bid,
            "total_ask": total_ask,
            "direction": direction if imbalanced else "NEUTRAL",
        }

    def _detect_iceberg(self, depth: dict) -> dict:
        """Repeated refills at same level = iceberg order."""
        bids = depth.get("bids", [])
        asks = depth.get("asks", [])
        all_levels = bids + asks

        iceberg_detected = False
        iceberg_levels = []

        for level in all_levels:
            price = level.get("price", 0)
            qty = level.get("qty", 0)
            if price <= 0:
                continue

            key = round(price, 2)
            if key not in self._level_history:
                self._level_history[key] = []

            self._level_history[key].append(qty)
            if len(self._level_history[key]) > self._max_history:
                self._level_history[key].pop(0)

            hist = self._level_history[key]
            if len(hist) >= 5:
                # Iceberg: qty stays relatively stable despite being "hit"
                # Check if qty dips then refills 3+ times
                refills = 0
                for i in range(1, len(hist)):
                    if hist[i] > hist[i - 1] * 0.8 and hist[i - 1] < hist[max(0, i - 2)] * 0.7:
                        refills += 1

                if refills >= 2:
                    iceberg_detected = True
                    iceberg_levels.append({
                        "price": price,
                        "refill_count": refills,
                        "current_qty": qty,
                    })

        # Prune old levels
        if len(self._level_history) > 200:
            # Keep only levels seen recently
            self._level_history = {k: v for k, v in self._level_history.items()
                                    if len(v) > 0}

        return {
            "detected": iceberg_detected,
            "levels": iceberg_levels[:5],
        }

    def compute(self, ctx: dict) -> EngineResult:
        depth = ctx.get("depth", {})
        candles = ctx.get("candles", {})
        closes = candles.get("close", [])

        price_change = 0
        if len(closes) >= 2:
            price_change = closes[-1] - closes[-2]

        absorption = self._detect_absorption(depth, price_change)
        imbalance = self._detect_imbalance(depth)
        iceberg = self._detect_iceberg(depth)

        # Direction
        signals_dir = []
        if absorption["detected"]:
            signals_dir.append(absorption["side"])
        if imbalance["imbalanced"]:
            signals_dir.append(imbalance.get("direction", "NEUTRAL"))

        bullish = signals_dir.count("BULLISH")
        bearish = signals_dir.count("BEARISH")
        direction = "BULLISH" if bullish > bearish else (
            "BEARISH" if bearish > bullish else "NEUTRAL")

        active_count = sum([
            absorption["detected"],
            imbalance["imbalanced"],
            iceberg["detected"],
        ])

        confidence = 20 + active_count * 22
        if absorption["detected"] and imbalance["imbalanced"]:
            confidence += 10  # Strong confirmation

        verdict = "PASS" if active_count >= 2 else (
            "PARTIAL" if active_count == 1 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "absorption_side": absorption.get("side", "NONE"),
                "absorption": absorption,
                "imbalance_ratio": imbalance.get("ratio", 50),
                "imbalance": imbalance,
                "iceberg_detected": iceberg["detected"],
                "iceberg": iceberg,
                "direction": direction,
                "active_signals": active_count,
            }
        )
