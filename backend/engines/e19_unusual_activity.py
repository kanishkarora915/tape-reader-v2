"""
E19 — Unusual Options Activity Engine (Tier 4: Big Move)
HIGH PRIORITY — tracks live OI changes per strike, generates BUY CALL/PUT signals.

Core Feature: OI CHANGE TRACKER
- Every cycle: snapshot current OI per strike (CE + PE)
- Compare with first snapshot: compute OI change (+ or -)
- Show which strikes are building OI (institutional accumulation)
- Show which strikes are cutting OI (short covering / exit)
- Running sums: total CE OI added, total PE OI added
- This data helps capture moves BEFORE they happen

Signal: When OI change pattern shows clear directional intent → BUY CALL/PUT with LTP, Entry, SL, Exit
"""

from .base import BaseEngine, EngineResult
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


class UnusualActivityEngine(BaseEngine):
    name = "Unusual Activity"
    tier = 4
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._first_snapshot = None  # First OI snapshot of the day {strike: {ce_oi, pe_oi}}
        self._prev_snapshot = None   # Previous cycle snapshot
        self._oi_history = {}        # strike_type -> [oi values]
        self._max_history = 30
        self._cycle_count = 0

    def compute(self, ctx: dict) -> EngineResult:
        chain_raw = ctx.get("chains", {})
        spot = ctx.get("nifty_spot", 0) or ctx.get("prices", {}).get("spot", 0)

        if not chain_raw or spot <= 0:
            return EngineResult(verdict="NEUTRAL", confidence=0,
                                data={"status": "No data", "oi_changes": [], "sums": {}})

        # Normalize chain to list
        chain = []
        if isinstance(chain_raw, dict):
            for strike, entry in chain_raw.items():
                if isinstance(entry, dict) and isinstance(strike, (int, float)):
                    row = dict(entry)
                    row["strike"] = int(strike)
                    chain.append(row)
        elif isinstance(chain_raw, list):
            chain = list(chain_raw)

        if not chain:
            return EngineResult(verdict="NEUTRAL", confidence=0,
                                data={"status": "Empty chain", "oi_changes": [], "sums": {}})

        chain.sort(key=lambda r: r.get("strike", 0))
        atm = round(spot / 50) * 50
        self._cycle_count += 1

        # ── Build current OI snapshot ──
        current_snapshot = {}
        for r in chain:
            strike = r.get("strike", 0)
            current_snapshot[strike] = {
                "ce_oi": r.get("ce_oi", 0) or 0,
                "pe_oi": r.get("pe_oi", 0) or 0,
                "ce_ltp": r.get("ce_ltp", 0) or 0,
                "pe_ltp": r.get("pe_ltp", 0) or 0,
                "ce_volume": r.get("ce_volume", 0) or 0,
                "pe_volume": r.get("pe_volume", 0) or 0,
            }

        # Store first snapshot (session start reference)
        if self._first_snapshot is None:
            self._first_snapshot = {k: dict(v) for k, v in current_snapshot.items()}

        # ── Compute OI changes from session start ──
        oi_changes = []
        total_ce_oi_added = 0
        total_ce_oi_removed = 0
        total_pe_oi_added = 0
        total_pe_oi_removed = 0

        for strike in sorted(current_snapshot.keys()):
            curr = current_snapshot[strike]
            first = self._first_snapshot.get(strike, {"ce_oi": 0, "pe_oi": 0})

            ce_change = curr["ce_oi"] - first.get("ce_oi", 0)
            pe_change = curr["pe_oi"] - first.get("pe_oi", 0)

            # Track running sums
            if ce_change > 0:
                total_ce_oi_added += ce_change
            else:
                total_ce_oi_removed += abs(ce_change)

            if pe_change > 0:
                total_pe_oi_added += pe_change
            else:
                total_pe_oi_removed += abs(pe_change)

            # Only include strikes with meaningful OI change
            if abs(ce_change) > 1000 or abs(pe_change) > 1000:
                is_atm = abs(strike - atm) <= 50
                oi_changes.append({
                    "strike": strike,
                    "ce_oi": curr["ce_oi"],
                    "pe_oi": curr["pe_oi"],
                    "ce_change": ce_change,
                    "pe_change": pe_change,
                    "ce_ltp": curr["ce_ltp"],
                    "pe_ltp": curr["pe_ltp"],
                    "ce_volume": curr["ce_volume"],
                    "pe_volume": curr["pe_volume"],
                    "atm": is_atm,
                    "otm_ce": strike > atm,
                    "otm_pe": strike < atm,
                })

        # Sort by absolute OI change (most active first)
        oi_changes.sort(key=lambda r: abs(r["ce_change"]) + abs(r["pe_change"]), reverse=True)

        # ── Compute cycle-over-cycle changes (last 5s) ──
        recent_changes = []
        if self._prev_snapshot:
            for strike in current_snapshot:
                curr = current_snapshot[strike]
                prev = self._prev_snapshot.get(strike, {"ce_oi": 0, "pe_oi": 0})
                ce_delta = curr["ce_oi"] - prev.get("ce_oi", 0)
                pe_delta = curr["pe_oi"] - prev.get("pe_oi", 0)
                if abs(ce_delta) > 500 or abs(pe_delta) > 500:
                    recent_changes.append({
                        "strike": strike, "ce_delta": ce_delta, "pe_delta": pe_delta,
                        "ce_ltp": curr["ce_ltp"], "pe_ltp": curr["pe_ltp"],
                    })
            recent_changes.sort(key=lambda r: abs(r["ce_delta"]) + abs(r["pe_delta"]), reverse=True)

        self._prev_snapshot = {k: dict(v) for k, v in current_snapshot.items()}

        # ── Analyze OI pattern for directional signal ──
        # Call OI cutting (falling) = BULLISH (writers covering)
        # Put OI cutting (falling) = BEARISH (writers covering)
        # Call OI building = BEARISH (writers adding, expecting down)
        # Put OI building = BULLISH (writers adding, expecting up)

        ce_net = total_ce_oi_added - total_ce_oi_removed  # Positive = CE OI building
        pe_net = total_pe_oi_added - total_pe_oi_removed  # Positive = PE OI building

        # Institutional interpretation
        bullish_score = 0
        bearish_score = 0
        interpretations = []

        if total_ce_oi_removed > total_ce_oi_added * 1.3:
            bullish_score += 3
            interpretations.append(f"CE OI cutting -{total_ce_oi_removed:,.0f} — call writers covering = BULLISH")
        elif total_ce_oi_added > total_ce_oi_removed * 1.3:
            bearish_score += 3
            interpretations.append(f"CE OI building +{total_ce_oi_added:,.0f} — call writers adding = BEARISH ceiling")

        if total_pe_oi_removed > total_pe_oi_added * 1.3:
            bearish_score += 3
            interpretations.append(f"PE OI cutting -{total_pe_oi_removed:,.0f} — put writers covering = BEARISH")
        elif total_pe_oi_added > total_pe_oi_removed * 1.3:
            bullish_score += 3
            interpretations.append(f"PE OI building +{total_pe_oi_added:,.0f} — put writers adding = BULLISH support")

        # Volume spike detection
        avg_ce_vol = sum(r.get("ce_volume", 0) for r in chain) / max(len(chain), 1) or 1
        avg_pe_vol = sum(r.get("pe_volume", 0) for r in chain) / max(len(chain), 1) or 1

        volume_spikes = []
        for r in chain:
            strike = r.get("strike", 0)
            ce_vol = r.get("ce_volume", 0) or 0
            pe_vol = r.get("pe_volume", 0) or 0
            if ce_vol > avg_ce_vol * 3 and ce_vol > 3000:
                volume_spikes.append({"strike": strike, "type": "CE", "volume": ce_vol, "ratio": round(ce_vol / avg_ce_vol, 1)})
            if pe_vol > avg_pe_vol * 3 and pe_vol > 3000:
                volume_spikes.append({"strike": strike, "type": "PE", "volume": pe_vol, "ratio": round(pe_vol / avg_pe_vol, 1)})

        # Direction
        if bullish_score > bearish_score:
            direction = "BULLISH"
        elif bearish_score > bullish_score:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # ── Generate trade recommendation ──
        trade = None
        if direction != "NEUTRAL" and oi_changes:
            # Pick the strike with highest OI change matching direction
            if direction == "BULLISH":
                # Look for CE near ATM with good LTP
                candidates = [r for r in oi_changes if r["ce_ltp"] > 5 and abs(r["strike"] - atm) <= 200]
                if candidates:
                    best = min(candidates, key=lambda r: abs(r["strike"] - atm))
                    ltp = best["ce_ltp"]
                    if ltp > 0:
                        trade = {
                            "action": "BUY CALL",
                            "instrument": f"NIFTY {best['strike']} CE",
                            "strike": best["strike"],
                            "opt_type": "CE",
                            "ltp": ltp,
                            "entry": ltp,
                            "sl": round(ltp * 0.80, 1),
                            "target1": round(ltp * 1.30, 1),
                            "target2": round(ltp * 1.60, 1),
                            "rr": f"1:{round(0.30 / 0.20, 1)}",
                            "reason": interpretations[0] if interpretations else "OI pattern bullish",
                            "confidence": "HIGH" if bullish_score >= 5 else "MODERATE",
                        }
            else:
                candidates = [r for r in oi_changes if r["pe_ltp"] > 5 and abs(r["strike"] - atm) <= 200]
                if candidates:
                    best = min(candidates, key=lambda r: abs(r["strike"] - atm))
                    ltp = best["pe_ltp"]
                    if ltp > 0:
                        trade = {
                            "action": "BUY PUT",
                            "instrument": f"NIFTY {best['strike']} PE",
                            "strike": best["strike"],
                            "opt_type": "PE",
                            "ltp": ltp,
                            "entry": ltp,
                            "sl": round(ltp * 0.80, 1),
                            "target1": round(ltp * 1.30, 1),
                            "target2": round(ltp * 1.60, 1),
                            "rr": f"1:{round(0.30 / 0.20, 1)}",
                            "reason": interpretations[0] if interpretations else "OI pattern bearish",
                            "confidence": "HIGH" if bearish_score >= 5 else "MODERATE",
                        }

        # Confidence
        total_signals = len(volume_spikes) + len([r for r in oi_changes if abs(r["ce_change"]) > 10000 or abs(r["pe_change"]) > 10000])
        confidence = min(20 + total_signals * 5 + max(bullish_score, bearish_score) * 8, 95)
        verdict = "PASS" if trade else ("PARTIAL" if len(oi_changes) > 3 else "NEUTRAL")

        # Sums for frontend display
        sums = {
            "ce_oi_added": int(total_ce_oi_added),
            "ce_oi_removed": int(total_ce_oi_removed),
            "ce_net": int(ce_net),
            "pe_oi_added": int(total_pe_oi_added),
            "pe_oi_removed": int(total_pe_oi_removed),
            "pe_net": int(pe_net),
            "direction": direction,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
        }

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "trade": trade,
                "oi_changes": oi_changes[:20],  # Top 20 most active strikes
                "recent_changes": recent_changes[:10],  # Last 5s changes
                "volume_spikes": volume_spikes[:10],
                "sums": sums,
                "interpretations": interpretations,
                "cycle": self._cycle_count,
                "status": f"{len(oi_changes)} strikes active | {direction}" if oi_changes else "Monitoring...",
            }
        )
