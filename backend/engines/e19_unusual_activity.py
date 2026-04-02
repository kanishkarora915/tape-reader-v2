"""
E19 — Unusual Options Activity Engine (Tier 4: Big Move)
HIGH PRIORITY ENGINE — generates direct BUY CALL/PUT signals with LTP, Entry, SL, Exit.

Detects institutional hidden activity:
1. Single-strike volume > 3x average = someone knows something
2. Volume >> OI = new large positions (block trades)
3. Far OTM strike with abnormal OI = institutional directional bet
4. OI building 3+ cycles at same strike = accumulation

When detected: outputs a TRADE RECOMMENDATION with specific strike, LTP, entry, SL, exit.
"""

from .base import BaseEngine, EngineResult


class UnusualActivityEngine(BaseEngine):
    name = "Unusual Activity"
    tier = 4
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._oi_history = {}
        self._max_history = 20

    def compute(self, ctx: dict) -> EngineResult:
        chain_raw = ctx.get("chains", {})
        spot = ctx.get("nifty_spot", 0) or ctx.get("prices", {}).get("spot", 0)

        if not chain_raw or spot <= 0:
            return EngineResult(verdict="NEUTRAL", confidence=0,
                                data={"status": "No chain/spot data", "trade": None})

        # Normalize chain to list format
        chain = []
        if isinstance(chain_raw, dict):
            for strike, entry in chain_raw.items():
                if isinstance(entry, dict) and isinstance(strike, (int, float)):
                    row = dict(entry)
                    row["strike"] = int(strike)
                    chain.append(row)
        elif isinstance(chain_raw, list):
            chain = chain_raw

        if not chain:
            return EngineResult(verdict="NEUTRAL", confidence=0,
                                data={"status": "Empty chain", "trade": None})

        chain.sort(key=lambda r: r.get("strike", 0))

        # ATM strike
        atm = round(spot / 50) * 50

        # ── 1. Volume spike detection (3x avg) ──
        ce_vols = [r.get("ce_volume", 0) or 0 for r in chain]
        pe_vols = [r.get("pe_volume", 0) or 0 for r in chain]
        avg_ce = sum(ce_vols) / max(len(ce_vols), 1) or 1
        avg_pe = sum(pe_vols) / max(len(pe_vols), 1) or 1

        uoa_signals = []
        for r in chain:
            strike = r.get("strike", 0)
            ce_vol = r.get("ce_volume", 0) or 0
            pe_vol = r.get("pe_volume", 0) or 0
            ce_oi = r.get("ce_oi", 0) or 0
            pe_oi = r.get("pe_oi", 0) or 0
            ce_ltp = r.get("ce_ltp", 0) or 0
            pe_ltp = r.get("pe_ltp", 0) or 0

            # CE unusual volume
            if ce_vol > avg_ce * 2.5 and ce_vol > 5000:
                otm = strike > atm
                uoa_signals.append({
                    "strike": strike, "type": "CE", "side": "BULLISH",
                    "volume": ce_vol, "oi": ce_oi, "ltp": ce_ltp,
                    "ratio": round(ce_vol / avg_ce, 1),
                    "otm": otm, "distance": strike - atm,
                    "strength": "STRONG" if ce_vol > avg_ce * 5 else "MODERATE",
                })

            # PE unusual volume
            if pe_vol > avg_pe * 2.5 and pe_vol > 5000:
                otm = strike < atm
                uoa_signals.append({
                    "strike": strike, "type": "PE", "side": "BEARISH",
                    "volume": pe_vol, "oi": pe_oi, "ltp": pe_ltp,
                    "ratio": round(pe_vol / avg_pe, 1),
                    "otm": otm, "distance": atm - strike,
                    "strength": "STRONG" if pe_vol > avg_pe * 5 else "MODERATE",
                })

        # ── 2. Block trades (volume >> OI) ──
        block_trades = []
        for r in chain:
            strike = r.get("strike", 0)
            for opt in [("ce", "BULLISH"), ("pe", "BEARISH")]:
                vol = r.get(f"{opt[0]}_volume", 0) or 0
                oi = r.get(f"{opt[0]}_oi", 0) or 0
                ltp = r.get(f"{opt[0]}_ltp", 0) or 0
                if oi > 0 and vol > oi * 1.5 and vol > 3000:
                    block_trades.append({
                        "strike": strike, "type": opt[0].upper(), "side": opt[1],
                        "volume": vol, "oi": oi, "ltp": ltp,
                        "vol_oi_ratio": round(vol / max(oi, 1), 1),
                    })

        # ── 3. OTM anomaly (far OTM with high OI) ──
        all_oi = [r.get("ce_oi", 0) or 0 for r in chain] + [r.get("pe_oi", 0) or 0 for r in chain]
        avg_oi = sum(all_oi) / max(len(all_oi), 1) or 1

        otm_anomalies = []
        for r in chain:
            strike = r.get("strike", 0)
            dist_pct = abs(strike - spot) / spot * 100 if spot else 0
            if dist_pct < 1.5:
                continue
            ce_oi = r.get("ce_oi", 0) or 0
            pe_oi = r.get("pe_oi", 0) or 0
            ce_ltp = r.get("ce_ltp", 0) or 0
            pe_ltp = r.get("pe_ltp", 0) or 0

            if ce_oi > avg_oi * 3 and strike > atm:
                otm_anomalies.append({
                    "strike": strike, "type": "CE", "side": "BULLISH",
                    "oi": ce_oi, "ltp": ce_ltp, "ratio": round(ce_oi / avg_oi, 1),
                    "distance_pct": round(dist_pct, 1),
                })
            if pe_oi > avg_oi * 3 and strike < atm:
                otm_anomalies.append({
                    "strike": strike, "type": "PE", "side": "BEARISH",
                    "oi": pe_oi, "ltp": pe_ltp, "ratio": round(pe_oi / avg_oi, 1),
                    "distance_pct": round(dist_pct, 1),
                })

        # ── 4. OI accumulation (building over cycles) ──
        builds = []
        for r in chain:
            strike = r.get("strike", 0)
            for opt in ["ce", "pe"]:
                oi = r.get(f"{opt}_oi", 0) or 0
                key = f"{strike}_{opt}"
                if key not in self._oi_history:
                    self._oi_history[key] = []
                self._oi_history[key].append(oi)
                if len(self._oi_history[key]) > self._max_history:
                    self._oi_history[key].pop(0)

                hist = self._oi_history[key]
                if len(hist) >= 3 and hist[-1] > hist[-2] > hist[-3] and hist[-3] > 0:
                    growth = ((hist[-1] - hist[-3]) / hist[-3]) * 100
                    if growth > 5:
                        ltp = r.get(f"{opt}_ltp", 0) or 0
                        builds.append({
                            "strike": strike, "type": opt.upper(),
                            "side": "BULLISH" if opt == "ce" else "BEARISH",
                            "oi": oi, "ltp": ltp, "growth_pct": round(growth, 1),
                        })

        # ── Combine all signals and generate trade recommendation ──
        all_signals = uoa_signals + block_trades + otm_anomalies + builds
        total = len(all_signals)

        bullish_signals = [s for s in all_signals if s.get("side") == "BULLISH"]
        bearish_signals = [s for s in all_signals if s.get("side") == "BEARISH"]

        bull_count = len(bullish_signals)
        bear_count = len(bearish_signals)

        if bull_count > bear_count:
            direction = "BULLISH"
            dominant_signals = sorted(bullish_signals, key=lambda s: s.get("volume", 0) or s.get("oi", 0), reverse=True)
        elif bear_count > bull_count:
            direction = "BEARISH"
            dominant_signals = sorted(bearish_signals, key=lambda s: s.get("volume", 0) or s.get("oi", 0), reverse=True)
        else:
            direction = "NEUTRAL"
            dominant_signals = []

        # ── Generate TRADE with LTP, Entry, SL, Exit ──
        trade = None
        if dominant_signals and direction != "NEUTRAL":
            best = dominant_signals[0]
            strike = best.get("strike", atm)
            opt_type = best.get("type", "CE" if direction == "BULLISH" else "PE")
            ltp = best.get("ltp", 0)

            if ltp > 0:
                entry = ltp
                sl = round(entry * 0.80, 1)  # 20% SL
                target1 = round(entry * 1.30, 1)  # 30% target
                target2 = round(entry * 1.60, 1)  # 60% target
                risk = entry - sl
                reward = target1 - entry
                rr = round(reward / risk, 1) if risk > 0 else 0

                trade = {
                    "action": f"BUY {'CALL' if opt_type == 'CE' else 'PUT'}",
                    "instrument": f"NIFTY {strike} {opt_type}",
                    "strike": strike,
                    "opt_type": opt_type,
                    "ltp": ltp,
                    "entry": ltp,
                    "sl": sl,
                    "target1": target1,
                    "target2": target2,
                    "rr": f"1:{rr}",
                    "reason": best.get("strength", "MODERATE") + f" — {opt_type} vol {best.get('volume', 0):,} ({best.get('ratio', 0)}x avg)" if best.get("volume") else f"OI anomaly {best.get('oi', 0):,}",
                    "confidence": "HIGH" if best.get("ratio", 0) > 5 or best.get("strength") == "STRONG" else "MODERATE",
                }

        categories = sum(1 for lst in [uoa_signals, block_trades, otm_anomalies, builds] if lst)
        confidence = min(20 + total * 6 + categories * 12, 95)
        verdict = "PASS" if trade else ("PARTIAL" if total > 0 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "trade": trade,
                "uoa_count": len(uoa_signals),
                "block_count": len(block_trades),
                "otm_count": len(otm_anomalies),
                "build_count": len(builds),
                "total_signals": total,
                "bull_signals": bull_count,
                "bear_signals": bear_count,
                "top_signal": str(dominant_signals[0].get("strike", "—")) + " " + dominant_signals[0].get("type", "") if dominant_signals else "None",
                "status": f"{total} signals detected" if total else "Monitoring...",
            }
        )
