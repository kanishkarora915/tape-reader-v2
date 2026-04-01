"""
E15 — VWAP Snapback Engine (Tier 3: Amplifier)
Checks if price is stretched > 1.5x ATR from VWAP (rubber band effect).
  - Stretched above VWAP: mean reversion = BEARISH snap-back expected
  - Stretched below VWAP: mean reversion = BULLISH snap-back expected
Provides snap-back probability based on distance/ATR ratio.
"""

import numpy as np
from .base import BaseEngine, EngineResult


class VWAPSnapbackEngine(BaseEngine):
    name = "VWAP Snapback"
    tier = 3
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._atr_period = 14

    def _compute_vwap(self, highs: list, lows: list, closes: list, volumes: list) -> float:
        """Compute VWAP from candle data."""
        if not highs or not volumes or len(highs) != len(volumes):
            return 0.0
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        cum_tp_vol = sum(tp * v for tp, v in zip(typical_prices, volumes))
        cum_vol = sum(volumes)
        return cum_tp_vol / cum_vol if cum_vol > 0 else 0.0

    def _compute_atr(self, highs: list, lows: list, closes: list) -> float:
        """Compute ATR over the configured period."""
        n = len(closes)
        if n < self._atr_period + 1:
            # Fallback: simple range
            if n >= 2:
                return float(np.mean([h - l for h, l in zip(highs[-5:], lows[-5:])]))
            return 0.0

        tr_values = []
        for i in range(1, n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            tr_values.append(tr)

        return float(np.mean(tr_values[-self._atr_period:]))

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        closes = candles.get("close", [])
        highs = candles.get("high", [])
        lows = candles.get("low", [])
        volumes = candles.get("volume", [])

        if len(closes) < 5:
            return EngineResult(verdict="NEUTRAL", data={"error": "Insufficient candle data"})

        vwap = self._compute_vwap(highs, lows, closes, volumes)
        atr = self._compute_atr(highs, lows, closes)
        current_price = closes[-1]

        if vwap <= 0 or atr <= 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "Cannot compute VWAP or ATR"})

        distance = current_price - vwap
        distance_in_atr = abs(distance) / atr

        # Stretched = distance > 1.5x ATR
        stretched = distance_in_atr > 1.5

        # Direction: if stretched above, expect BEARISH snap-back; below = BULLISH
        if stretched:
            direction = "BEARISH" if distance > 0 else "BULLISH"
        else:
            direction = "NEUTRAL"

        # Snap probability increases with stretch
        if distance_in_atr <= 1.0:
            snap_probability = 15
        elif distance_in_atr <= 1.5:
            snap_probability = 35
        elif distance_in_atr <= 2.0:
            snap_probability = 60
        elif distance_in_atr <= 3.0:
            snap_probability = 78
        else:
            snap_probability = 88

        verdict = "PASS" if stretched else ("PARTIAL" if distance_in_atr > 1.0 else "NEUTRAL")
        confidence = snap_probability if stretched else max(int(distance_in_atr * 25), 10)

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "stretched": stretched,
                "distance_from_vwap": round(distance, 2),
                "distance_in_atr": round(distance_in_atr, 3),
                "atr": round(atr, 2),
                "vwap": round(vwap, 2),
                "current_price": current_price,
                "direction": direction,
                "snap_probability": snap_probability,
            }
        )
