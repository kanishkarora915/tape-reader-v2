"""
E14 — Delta Spike Engine (Tier 3: Amplifier)
Monitors aggregate delta shift across OTM options.
  - Large OTM CE buying = BULLISH
  - Large OTM PE buying = BEARISH
  - Delta-weighted OI shifting from ATM to OTM = big move bet
"""

import numpy as np
from .base import BaseEngine, EngineResult


class DeltaSpikeEngine(BaseEngine):
    name = "Delta Spike"
    tier = 3
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._delta_history = []
        self._max_history = 60

    def _classify_strikes(self, chain: list, spot: float) -> dict:
        """Separate chain into ATM, OTM CE, OTM PE buckets."""
        atm_range = spot * 0.005  # 0.5% around spot = ATM
        otm_ce, otm_pe, atm = [], [], []

        for strike in chain:
            s = strike.get("strike", 0)
            if abs(s - spot) <= atm_range:
                atm.append(strike)
            elif s > spot:
                otm_ce.append(strike)
            else:
                otm_pe.append(strike)
        return {"atm": atm, "otm_ce": otm_ce, "otm_pe": otm_pe}

    def _compute_delta_activity(self, strikes: list, option_type: str) -> dict:
        """Aggregate volume-weighted delta activity for a set of strikes."""
        total_volume = 0
        total_oi_change = 0
        delta_weighted_flow = 0.0

        for s in strikes:
            vol = s.get(f"{option_type}_volume", 0) or 0
            oi_chg = s.get(f"{option_type}_oi_change", 0) or 0
            delta = s.get(f"{option_type}_delta", 0.5) or 0.5
            total_volume += vol
            total_oi_change += oi_chg
            delta_weighted_flow += vol * abs(delta)

        return {
            "total_volume": total_volume,
            "total_oi_change": total_oi_change,
            "delta_weighted_flow": round(delta_weighted_flow, 2),
        }

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", [])
        spot = ctx.get("prices", {}).get("spot", 0) or ctx.get("prices", {}).get("ltp", 0)

        if not chain or spot <= 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain or spot data"})

        buckets = self._classify_strikes(chain, spot)

        otm_ce_activity = self._compute_delta_activity(buckets["otm_ce"], "ce")
        otm_pe_activity = self._compute_delta_activity(buckets["otm_pe"], "pe")
        atm_activity_ce = self._compute_delta_activity(buckets["atm"], "ce")
        atm_activity_pe = self._compute_delta_activity(buckets["atm"], "pe")

        # Delta shift: OTM flow vs ATM flow
        atm_total = atm_activity_ce["delta_weighted_flow"] + atm_activity_pe["delta_weighted_flow"]
        otm_total = otm_ce_activity["delta_weighted_flow"] + otm_pe_activity["delta_weighted_flow"]
        delta_shift = otm_total / atm_total if atm_total > 0 else 0

        # Track history
        ce_pe_ratio = (otm_ce_activity["delta_weighted_flow"] /
                       otm_pe_activity["delta_weighted_flow"]
                       if otm_pe_activity["delta_weighted_flow"] > 0 else 2.0)
        self._delta_history.append(ce_pe_ratio)
        if len(self._delta_history) > self._max_history:
            self._delta_history.pop(0)

        # Direction: CE heavy = BULLISH, PE heavy = BEARISH
        direction = "NEUTRAL"
        if ce_pe_ratio > 1.5:
            direction = "BULLISH"
        elif ce_pe_ratio < 0.67:
            direction = "BEARISH"

        # Confidence based on delta shift magnitude and consistency
        shift_active = delta_shift > 1.5  # OTM flow 1.5x ATM = big move bet
        directional_active = direction != "NEUTRAL"
        confidence = 30
        if shift_active:
            confidence += 25
        if directional_active:
            confidence += 20
        if len(self._delta_history) >= 5:
            recent = self._delta_history[-5:]
            if all(r > 1.3 for r in recent) or all(r < 0.77 for r in recent):
                confidence += 15  # Sustained directional shift

        verdict = "PASS" if shift_active and directional_active else (
            "PARTIAL" if shift_active or directional_active else "NEUTRAL"
        )

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "delta_shift": round(delta_shift, 3),
                "otm_ce_activity": otm_ce_activity,
                "otm_pe_activity": otm_pe_activity,
                "ce_pe_ratio": round(ce_pe_ratio, 3),
                "direction": direction,
                "shift_to_otm": shift_active,
            }
        )
