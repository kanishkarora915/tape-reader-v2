"""
E16 — Multi-Timeframe Engine (Tier 3: Amplifier)
Checks 5m, 15m, 1Hr candle trends using EMA crossover.
Only fires when ALL 3 timeframes agree on direction.
"""

import numpy as np
from .base import BaseEngine, EngineResult


class MultiTimeframeEngine(BaseEngine):
    name = "Multi-Timeframe"
    tier = 3
    refresh_seconds = 10

    def __init__(self):
        super().__init__()
        self._fast_ema = 9
        self._slow_ema = 21

    @staticmethod
    def _ema(data: list, period: int) -> float:
        """Compute EMA of the last `period` values, return final value."""
        if len(data) < period:
            return np.mean(data) if data else 0.0
        arr = np.array(data[-period * 3:], dtype=float)  # use 3x period for warm-up
        multiplier = 2 / (period + 1)
        ema_val = arr[0]
        for val in arr[1:]:
            ema_val = (val - ema_val) * multiplier + ema_val
        return float(ema_val)

    def _assess_timeframe(self, closes: list) -> dict:
        """Determine trend for a single timeframe via EMA crossover + candle structure."""
        if len(closes) < self._slow_ema:
            return {"direction": "NEUTRAL", "fast_ema": 0, "slow_ema": 0, "sufficient_data": False}

        fast = self._ema(closes, self._fast_ema)
        slow = self._ema(closes, self._slow_ema)

        # Also check last 3 candles direction
        recent = closes[-3:] if len(closes) >= 3 else closes
        rising = all(recent[i] >= recent[i - 1] for i in range(1, len(recent)))
        falling = all(recent[i] <= recent[i - 1] for i in range(1, len(recent)))

        if fast > slow:
            direction = "BULLISH"
        elif fast < slow:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # Candle confirmation strengthens or weakens
        candle_dir = "BULLISH" if rising else ("BEARISH" if falling else "NEUTRAL")

        return {
            "direction": direction,
            "candle_direction": candle_dir,
            "fast_ema": round(fast, 2),
            "slow_ema": round(slow, 2),
            "sufficient_data": True,
        }

    def compute(self, ctx: dict) -> EngineResult:
        candles_5m = ctx.get("candles", {}).get("close", [])
        candles_15m = ctx.get("candles_15m", {}).get("close", [])
        candles_1h = ctx.get("candles_1h", {}).get("close", [])

        # If multi-TF data not provided, try to resample from 5m
        if not candles_15m and len(candles_5m) >= 63:
            candles_15m = candles_5m[::3]  # approximate 15m from 5m
        if not candles_1h and len(candles_5m) >= 252:
            candles_1h = candles_5m[::12]  # approximate 1h from 5m

        tf_5m = self._assess_timeframe(candles_5m)
        tf_15m = self._assess_timeframe(candles_15m) if candles_15m else {
            "direction": "NEUTRAL", "sufficient_data": False}
        tf_1h = self._assess_timeframe(candles_1h) if candles_1h else {
            "direction": "NEUTRAL", "sufficient_data": False}

        directions = [tf_5m["direction"], tf_15m["direction"], tf_1h["direction"]]
        all_bullish = all(d == "BULLISH" for d in directions)
        all_bearish = all(d == "BEARISH" for d in directions)
        aligned = all_bullish or all_bearish

        direction = "BULLISH" if all_bullish else ("BEARISH" if all_bearish else "NEUTRAL")

        # Count agreeing timeframes
        agree_count = max(
            sum(1 for d in directions if d == "BULLISH"),
            sum(1 for d in directions if d == "BEARISH"),
        )

        confidence = 25
        if agree_count == 2:
            confidence = 55
        if aligned:
            confidence = 80

        verdict = "PASS" if aligned else ("PARTIAL" if agree_count >= 2 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "tf_5m": tf_5m,
                "tf_15m": tf_15m,
                "tf_1h": tf_1h,
                "aligned": aligned,
                "direction": direction,
                "agreeing_timeframes": agree_count,
            }
        )
