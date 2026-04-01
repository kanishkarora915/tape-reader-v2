"""
E13 — Momentum Ignition Engine (Tier 3: Amplifier)
Detects simultaneous spike in price + volume + OI within the same 5-min candle.
Sub-detectors:
  1. Price move > 0.3% in a single candle
  2. Volume > 2x rolling average
  3. OI change > 1.5x rolling average
  4. 3 consecutive closes in same direction with rising volume
  5. Gap detection: open vs prev close > 0.3%
Fires when price_spike + volume_spike + oi_spike all true, or gap + consecutive bars.
"""

import numpy as np
from .base import BaseEngine, EngineResult


class MomentumIgnitionEngine(BaseEngine):
    name = "Momentum Ignition"
    tier = 3
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._vol_avg_period = 20
        self._oi_avg_period = 20

    def _detect_price_spike(self, closes: list) -> dict:
        """Price move > 0.3% in latest candle."""
        if len(closes) < 2:
            return {"active": False, "change_pct": 0}
        prev, curr = closes[-2], closes[-1]
        if prev <= 0:
            return {"active": False, "change_pct": 0}
        change_pct = ((curr - prev) / prev) * 100
        return {
            "active": abs(change_pct) > 0.3,
            "change_pct": round(change_pct, 3),
            "direction": "BULLISH" if change_pct > 0 else "BEARISH",
        }

    def _detect_volume_spike(self, volumes: list) -> dict:
        """Current volume > 2x rolling average."""
        if len(volumes) < self._vol_avg_period + 1:
            return {"active": False, "ratio": 0}
        avg_vol = np.mean(volumes[-(self._vol_avg_period + 1):-1])
        current_vol = volumes[-1]
        ratio = current_vol / avg_vol if avg_vol > 0 else 0
        return {
            "active": ratio > 2.0,
            "ratio": round(ratio, 2),
            "current": current_vol,
            "avg": round(avg_vol, 2),
        }

    def _detect_oi_spike(self, oi_changes: list) -> dict:
        """OI change > 1.5x rolling average."""
        if len(oi_changes) < self._oi_avg_period + 1:
            return {"active": False, "ratio": 0}
        avg_oi = np.mean(np.abs(oi_changes[-(self._oi_avg_period + 1):-1]))
        current_oi = abs(oi_changes[-1])
        ratio = current_oi / avg_oi if avg_oi > 0 else 0
        return {
            "active": ratio > 1.5,
            "ratio": round(ratio, 2),
            "current_change": oi_changes[-1],
            "avg_abs_change": round(avg_oi, 2),
        }

    def _detect_consecutive_bars(self, closes: list, volumes: list) -> dict:
        """3 consecutive closes in same direction with rising volume."""
        if len(closes) < 4 or len(volumes) < 3:
            return {"active": False, "count": 0}
        changes = [closes[i] - closes[i - 1] for i in range(-3, 0)]
        vols = volumes[-3:]
        all_up = all(c > 0 for c in changes)
        all_down = all(c < 0 for c in changes)
        rising_vol = vols[-1] > vols[-2] > vols[-3] if len(vols) == 3 else False
        same_dir = all_up or all_down
        direction = "BULLISH" if all_up else ("BEARISH" if all_down else "NEUTRAL")
        return {
            "active": same_dir and rising_vol,
            "count": 3 if same_dir else 0,
            "rising_volume": rising_vol,
            "direction": direction,
        }

    def _detect_gap(self, opens: list, closes: list) -> dict:
        """Gap detection: open vs prev close > 0.3%."""
        if len(opens) < 1 or len(closes) < 2:
            return {"active": False, "gap_pct": 0}
        prev_close = closes[-2]
        current_open = opens[-1]
        if prev_close <= 0:
            return {"active": False, "gap_pct": 0}
        gap_pct = ((current_open - prev_close) / prev_close) * 100
        return {
            "active": abs(gap_pct) > 0.3,
            "gap_pct": round(gap_pct, 3),
            "direction": "BULLISH" if gap_pct > 0 else "BEARISH",
        }

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        closes = candles.get("close", [])
        opens = candles.get("open", [])
        volumes = candles.get("volume", [])
        oi_changes = candles.get("oi_change", [])

        price_spike = self._detect_price_spike(closes)
        volume_spike = self._detect_volume_spike(volumes)
        oi_spike = self._detect_oi_spike(oi_changes) if oi_changes else {"active": False, "ratio": 0}
        consecutive = self._detect_consecutive_bars(closes, volumes)
        gap = self._detect_gap(opens, closes)

        # Ignition = all 3 spikes simultaneously, or gap + consecutive
        triple_spike = price_spike["active"] and volume_spike["active"] and oi_spike["active"]
        gap_momentum = gap["active"] and consecutive["active"]
        ignition_detected = triple_spike or gap_momentum

        # Direction from price spike or consecutive bars
        direction = "NEUTRAL"
        if price_spike["active"]:
            direction = price_spike.get("direction", "NEUTRAL")
        elif consecutive["active"]:
            direction = consecutive.get("direction", "NEUTRAL")

        active_count = sum(1 for s in [price_spike, volume_spike, oi_spike, consecutive, gap]
                           if s.get("active", False))
        confidence = min(active_count * 18, 90)
        verdict = "PASS" if ignition_detected else ("PARTIAL" if active_count >= 2 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "ignition_detected": ignition_detected,
                "price_spike": price_spike,
                "volume_spike": volume_spike,
                "oi_spike": oi_spike,
                "consecutive_bars": consecutive,
                "gap": gap,
                "active_sub_signals": active_count,
            }
        )
