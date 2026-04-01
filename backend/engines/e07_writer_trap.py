"""
E07 — Writer Trap Engine (Tier 2: Direction)
Monitors each strike for simultaneous OI drop + premium spike.
Call writer trap: CE OI drops >5% AND CE premium rises >3% = BULLISH
Put writer trap: PE OI drops >5% AND PE premium rises >3% = BEARISH
"""

import time
from .base import BaseEngine, EngineResult


class WriterTrapEngine(BaseEngine):
    name = "Writer Trap"
    tier = 2
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._prev_snapshot = {}  # {strike: {ce_oi, pe_oi, ce_ltp, pe_ltp}}
        self._prev_time = 0
        self._active_traps = []   # recent traps (decayed over time)

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", {})
        spot = ctx.get("prices", {}).get("spot", 0)
        now = time.time()

        if not chain or spot == 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain/spot"})

        # Build current snapshot
        current_snapshot = {}
        for key, entry in chain.items():
            if not isinstance(entry, dict):
                continue
            try:
                strike = int(key)
            except (ValueError, TypeError):
                continue

            current_snapshot[strike] = {
                "ce_oi": entry.get("ce_oi", entry.get("call_oi", 0)) or 0,
                "pe_oi": entry.get("pe_oi", entry.get("put_oi", 0)) or 0,
                "ce_ltp": entry.get("ce_ltp", entry.get("call_ltp", 0)) or 0,
                "pe_ltp": entry.get("pe_ltp", entry.get("put_ltp", 0)) or 0,
            }

        # Need previous snapshot for comparison
        if not self._prev_snapshot:
            self._prev_snapshot = current_snapshot
            self._prev_time = now
            return EngineResult(verdict="NEUTRAL", confidence=10,
                                data={"note": "Building baseline snapshot"})

        # Decay old traps (remove traps older than 15 min)
        self._active_traps = [t for t in self._active_traps
                              if now - t.get("timestamp", 0) < 900]

        # Scan each strike for traps
        new_traps = []
        call_traps = 0
        put_traps = 0

        for strike, curr in current_snapshot.items():
            prev = self._prev_snapshot.get(strike)
            if prev is None:
                continue

            # Call writer trap: CE OI drops > 5% AND CE premium rises > 3%
            if prev["ce_oi"] > 100:  # minimum OI threshold
                ce_oi_change_pct = ((curr["ce_oi"] - prev["ce_oi"]) / prev["ce_oi"]) * 100
                ce_ltp_change_pct = 0
                if prev["ce_ltp"] > 0:
                    ce_ltp_change_pct = ((curr["ce_ltp"] - prev["ce_ltp"]) / prev["ce_ltp"]) * 100

                if ce_oi_change_pct < -5 and ce_ltp_change_pct > 3:
                    trap = {
                        "strike": strike,
                        "side": "CALL",
                        "oi_drop": round(ce_oi_change_pct, 2),
                        "premium_change": round(ce_ltp_change_pct, 2),
                        "timestamp": now,
                    }
                    new_traps.append(trap)
                    call_traps += 1

            # Put writer trap: PE OI drops > 5% AND PE premium rises > 3%
            if prev["pe_oi"] > 100:
                pe_oi_change_pct = ((curr["pe_oi"] - prev["pe_oi"]) / prev["pe_oi"]) * 100
                pe_ltp_change_pct = 0
                if prev["pe_ltp"] > 0:
                    pe_ltp_change_pct = ((curr["pe_ltp"] - prev["pe_ltp"]) / prev["pe_ltp"]) * 100

                if pe_oi_change_pct < -5 and pe_ltp_change_pct > 3:
                    trap = {
                        "strike": strike,
                        "side": "PUT",
                        "oi_drop": round(pe_oi_change_pct, 2),
                        "premium_change": round(pe_ltp_change_pct, 2),
                        "timestamp": now,
                    }
                    new_traps.append(trap)
                    put_traps += 1

        # Add new traps to active list
        self._active_traps.extend(new_traps)

        # Update snapshot
        self._prev_snapshot = current_snapshot
        self._prev_time = now

        # Count active traps by side
        active_call_traps = sum(1 for t in self._active_traps if t["side"] == "CALL")
        active_put_traps = sum(1 for t in self._active_traps if t["side"] == "PUT")

        # Determine direction
        direction = "NEUTRAL"
        verdict = "NEUTRAL"
        confidence = 20

        if active_call_traps > 0 and active_call_traps > active_put_traps:
            direction = "BULLISH"  # Call writers being trapped = price going up
            verdict = "PASS"
            confidence = 55 + min(active_call_traps * 10, 35)
        elif active_put_traps > 0 and active_put_traps > active_call_traps:
            direction = "BEARISH"  # Put writers being trapped = price going down
            verdict = "PASS"
            confidence = 55 + min(active_put_traps * 10, 35)
        elif active_call_traps > 0 and active_put_traps > 0:
            # Both sides trapped: chaotic, reduce confidence
            verdict = "PARTIAL"
            confidence = 30

        # Strong signal: multiple strikes on same side
        if active_call_traps >= 3:
            confidence = min(confidence + 10, 95)
        if active_put_traps >= 3:
            confidence = min(confidence + 10, 95)

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "traps": self._active_traps[-10:],  # last 10 traps for display
                "new_traps": new_traps,
                "active_call_traps": active_call_traps,
                "active_put_traps": active_put_traps,
                "direction": direction,
            }
        )
