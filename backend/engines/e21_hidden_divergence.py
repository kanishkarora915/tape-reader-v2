"""
E21 — Hidden Divergence Engine (Tier 4: Big Move)
Tracks 4 streams: price, OI, delta, volume for divergences.
  - Price new high + OI falling = bearish divergence
  - Price new high + volume declining = weak move
  - Triple divergence (all 3 streams disagree with price) = EXTREME reversal signal
"""

import numpy as np
from .base import BaseEngine, EngineResult


class HiddenDivergenceEngine(BaseEngine):
    name = "Hidden Divergence"
    tier = 4
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._lookback = 10  # Bars to check for highs/lows

    def _is_new_high(self, data: list, lookback: int) -> bool:
        """Check if latest value is highest in lookback period."""
        if len(data) < lookback:
            return False
        window = data[-lookback:]
        return window[-1] >= max(window[:-1]) if len(window) > 1 else False

    def _is_new_low(self, data: list, lookback: int) -> bool:
        """Check if latest value is lowest in lookback period."""
        if len(data) < lookback:
            return False
        window = data[-lookback:]
        return window[-1] <= min(window[:-1]) if len(window) > 1 else False

    def _is_declining(self, data: list, periods: int = 3) -> bool:
        """Check if values are declining over recent periods."""
        if len(data) < periods + 1:
            return False
        recent = data[-(periods + 1):]
        return all(recent[i] >= recent[i + 1] for i in range(len(recent) - 1))

    def _is_rising(self, data: list, periods: int = 3) -> bool:
        """Check if values are rising over recent periods."""
        if len(data) < periods + 1:
            return False
        recent = data[-(periods + 1):]
        return all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

    def _check_divergence(self, price_data: list, indicator_data: list,
                           indicator_name: str) -> dict:
        """Check for divergence between price and an indicator."""
        if len(price_data) < self._lookback or len(indicator_data) < self._lookback:
            return {"active": False, "type": "NONE", "indicator": indicator_name}

        price_new_high = self._is_new_high(price_data, self._lookback)
        price_new_low = self._is_new_low(price_data, self._lookback)
        ind_declining = self._is_declining(indicator_data)
        ind_rising = self._is_rising(indicator_data)
        ind_new_high = self._is_new_high(indicator_data, self._lookback)
        ind_new_low = self._is_new_low(indicator_data, self._lookback)

        div_type = "NONE"
        direction = "NEUTRAL"
        strength = 0

        # Bearish divergence: price new high but indicator declining/not confirming
        if price_new_high and (ind_declining or not ind_new_high):
            div_type = "BEARISH"
            direction = "BEARISH"
            strength = 70 if ind_declining else 50

        # Bullish divergence: price new low but indicator rising/not confirming
        elif price_new_low and (ind_rising or not ind_new_low):
            div_type = "BULLISH"
            direction = "BULLISH"
            strength = 70 if ind_rising else 50

        return {
            "active": div_type != "NONE",
            "type": div_type,
            "indicator": indicator_name,
            "direction": direction,
            "strength": strength,
            "price_new_high": price_new_high,
            "price_new_low": price_new_low,
            "indicator_declining": ind_declining,
            "indicator_rising": ind_rising,
        }

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        closes = candles.get("close", [])
        volumes = candles.get("volume", [])
        oi_values = candles.get("oi", []) or candles.get("total_oi", [])

        # Delta from previous engine results
        prev_results = ctx.get("previous_results", {})
        e14 = prev_results.get("e14", {})
        e14_data = e14.get("data", {}) if isinstance(e14, dict) else {}
        if hasattr(e14, "data"):
            e14_data = e14.data

        # Build delta series from context or use OI as proxy
        delta_values = ctx.get("delta_series", [])
        if not delta_values and oi_values:
            # Use OI change as delta proxy
            delta_values = [0] + [oi_values[i] - oi_values[i - 1]
                                   for i in range(1, len(oi_values))]

        divergences = []

        # Check price vs OI divergence
        if oi_values:
            oi_div = self._check_divergence(closes, oi_values, "OI")
            if oi_div["active"]:
                divergences.append(oi_div)

        # Check price vs volume divergence
        if volumes:
            vol_div = self._check_divergence(closes, volumes, "Volume")
            if vol_div["active"]:
                divergences.append(vol_div)

        # Check price vs delta divergence
        if delta_values and len(delta_values) >= self._lookback:
            delta_div = self._check_divergence(closes, delta_values, "Delta")
            if delta_div["active"]:
                divergences.append(delta_div)

        num_divergences = len(divergences)
        triple = num_divergences >= 3

        # Determine overall direction
        bearish = sum(1 for d in divergences if d["direction"] == "BEARISH")
        bullish = sum(1 for d in divergences if d["direction"] == "BULLISH")
        direction = "BEARISH" if bearish > bullish else ("BULLISH" if bullish > bearish else "NEUTRAL")

        # Strength: triple divergence = EXTREME
        strength = "NONE"
        if triple:
            strength = "EXTREME"
        elif num_divergences == 2:
            strength = "STRONG"
        elif num_divergences == 1:
            strength = "MODERATE"

        confidence = 15 + num_divergences * 25
        if triple:
            confidence = 90

        verdict = "PASS" if num_divergences >= 2 else (
            "PARTIAL" if num_divergences == 1 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "divergences": divergences,
                "type": strength,
                "strength": strength,
                "direction": direction,
                "triple_divergence": triple,
                "count": num_divergences,
            }
        )
