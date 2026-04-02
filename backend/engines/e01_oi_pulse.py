"""
E01 — OI Pulse Engine (Tier 1: Core Gate)
Tracks OI changes over rolling 5-min windows for CE/PE at ATM +/- 3 strikes.
Detects writer covering, straddle building, and OI weakness.
"""

import numpy as np
from .base import BaseEngine, EngineResult


class OIPulseEngine(BaseEngine):
    name = "OI Pulse"
    tier = 1
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._oi_history_ce = []  # list of snapshots: [{strike: oi, ...}, ...]
        self._oi_history_pe = []
        self._max_history = 60    # ~5 min at 5s refresh

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", {})
        spot = ctx.get("prices", {}).get("spot", 0)
        if not chain or spot == 0:
            return EngineResult(verdict="NEUTRAL", confidence=0,
                                data={"error": "No chain or spot data"})

        # Determine ATM strike
        strikes = sorted([int(s) for s in chain.keys() if str(s).isdigit()])
        if not strikes:
            # Try alternate chain format: list of dicts
            strikes = sorted(set(r.get("strike", 0) for r in chain if isinstance(r, dict)))
        if not strikes:
            return EngineResult(verdict="NEUTRAL", data={"error": "No strikes in chain"})

        step = strikes[1] - strikes[0] if len(strikes) > 1 else 50
        atm = min(strikes, key=lambda s: abs(s - spot))

        # ATM +/- 3 strikes
        target_strikes = [atm + i * step for i in range(-3, 4)]
        target_strikes = [s for s in target_strikes if s in strikes or s in chain]

        # Extract current OI snapshot
        ce_oi_now = {}
        pe_oi_now = {}
        for s in target_strikes:
            entry = chain.get(s, chain.get(str(s), {}))
            if isinstance(entry, dict):
                ce_oi_now[s] = entry.get("ce_oi", entry.get("call_oi", 0)) or 0
                pe_oi_now[s] = entry.get("pe_oi", entry.get("put_oi", 0)) or 0

        # Push to history
        self._oi_history_ce.append(ce_oi_now)
        self._oi_history_pe.append(pe_oi_now)
        if len(self._oi_history_ce) > self._max_history:
            self._oi_history_ce.pop(0)
            self._oi_history_pe.pop(0)

        # Need at least 2 snapshots for proper delta analysis
        if len(self._oi_history_ce) < 2:
            # First call — use price direction + OI ratio as preliminary signal
            total_ce = sum(ce_oi_now.values()) or 1
            total_pe = sum(pe_oi_now.values()) or 1
            pcr_raw = total_pe / total_ce
            price_chg = ctx.get("nifty_change_pct", 0)
            if price_chg < -0.5 and pcr_raw > 1.1:
                prelim_dir = "BEARISH"
            elif price_chg > 0.5 and pcr_raw < 0.9:
                prelim_dir = "BULLISH"
            else:
                prelim_dir = "NEUTRAL"
            return EngineResult(
                verdict="PARTIAL", direction=prelim_dir, confidence=25,
                data={"writer_signal": "BUILDING_HISTORY", "total_oi_trend": "UNKNOWN",
                      "oi_change_ce": 0, "oi_change_pe": 0, "note": "Preliminary — building OI history"}
            )

        # Compute OI change over available window (oldest vs newest)
        old_ce = self._oi_history_ce[0]
        old_pe = self._oi_history_pe[0]

        total_ce_change = sum(ce_oi_now.get(s, 0) - old_ce.get(s, 0) for s in target_strikes)
        total_pe_change = sum(pe_oi_now.get(s, 0) - old_pe.get(s, 0) for s in target_strikes)
        total_ce_now = sum(ce_oi_now.values())
        total_pe_now = sum(pe_oi_now.values())
        total_oi_now = total_ce_now + total_pe_now

        # Percentage changes (guard div-by-zero)
        old_ce_total = sum(old_ce.values()) or 1
        old_pe_total = sum(old_pe.values()) or 1
        ce_pct = (total_ce_change / old_ce_total) * 100
        pe_pct = (total_pe_change / old_pe_total) * 100

        # Determine writer signal
        writer_signal = "NONE"
        verdict = "NEUTRAL"
        direction = "NEUTRAL"
        confidence = 30

        # Call OI falling + price rising = BULLISH (call writers covering)
        price_change = ctx.get("prices", {}).get("change_pct", 0) or ctx.get("nifty_change_pct", 0)

        if ce_pct < -3 and price_change > 0.1:
            writer_signal = "CALL_WRITERS_COVERING"
            direction = "BULLISH"
            verdict = "PASS"
            confidence = min(70 + abs(int(ce_pct)), 95)

        # Put OI falling + price falling = BEARISH (put writers covering)
        elif pe_pct < -3 and price_change < -0.1:
            writer_signal = "PUT_WRITERS_COVERING"
            direction = "BEARISH"
            verdict = "PASS"
            confidence = min(70 + abs(int(pe_pct)), 95)

        # Both sides OI surging = straddle building = informational, not a block
        elif ce_pct > 5 and pe_pct > 5:
            writer_signal = "STRADDLE_BUILD"
            verdict = "PASS"
            direction = "NEUTRAL"
            confidence = 40

        # Both sides OI flat = weak conviction
        elif abs(ce_pct) < 1 and abs(pe_pct) < 1:
            writer_signal = "FLAT"
            verdict = "PARTIAL"
            direction = "NEUTRAL"
            confidence = 20

        # Directional OI build
        elif ce_pct > 3 and pe_pct < 1:
            writer_signal = "CE_OI_BUILD"
            direction = "BEARISH"
            verdict = "PASS"
            confidence = 55
        elif pe_pct > 3 and ce_pct < 1:
            writer_signal = "PE_OI_BUILD"
            direction = "BULLISH"
            verdict = "PASS"
            confidence = 55
        else:
            verdict = "PARTIAL"
            confidence = 30

        # Total OI trend
        if total_oi_now > 0:
            mid_idx = len(self._oi_history_ce) // 2
            mid_ce = sum(self._oi_history_ce[mid_idx].values()) if mid_idx < len(self._oi_history_ce) else total_ce_now
            mid_pe = sum(self._oi_history_pe[mid_idx].values()) if mid_idx < len(self._oi_history_pe) else total_pe_now
            mid_total = mid_ce + mid_pe
            total_oi_trend = "RISING" if total_oi_now > mid_total * 1.01 else (
                "FALLING" if total_oi_now < mid_total * 0.99 else "FLAT")
        else:
            total_oi_trend = "UNKNOWN"

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "oi_change_ce": round(total_ce_change),
                "oi_change_pe": round(total_pe_change),
                "ce_change_pct": round(ce_pct, 2),
                "pe_change_pct": round(pe_pct, 2),
                "writer_signal": writer_signal,
                "total_oi_trend": total_oi_trend,
                "atm_strike": atm,
                "total_ce_oi": total_ce_now,
                "total_pe_oi": total_pe_now,
            }
        )
