"""
E19 — Unusual Options Activity Engine (Tier 4: Big Move)
Detects UOA signals:
  1. Single-strike volume > 3x average = unusual activity
  2. Volume >> OI on a strike = new positions (block trades)
  3. Far OTM strike with 5x normal OI = anomaly
  4. Same strike OI building 3 periods in a row = multi-day build
"""

from .base import BaseEngine, EngineResult


class UnusualActivityEngine(BaseEngine):
    name = "Unusual Activity"
    tier = 4
    refresh_seconds = 10

    def __init__(self):
        super().__init__()
        self._oi_history = {}  # strike -> [oi values over time]
        self._max_history = 20

    def _detect_uoa(self, chain: list, spot: float) -> list:
        """Single-strike volume > 3x avg across chain."""
        if not chain:
            return []

        # Compute average volume across all strikes
        all_ce_vols = [s.get("ce_volume", 0) or 0 for s in chain]
        all_pe_vols = [s.get("pe_volume", 0) or 0 for s in chain]
        avg_ce_vol = sum(all_ce_vols) / max(len(all_ce_vols), 1)
        avg_pe_vol = sum(all_pe_vols) / max(len(all_pe_vols), 1)

        signals = []
        for s in chain:
            strike = s.get("strike", 0)
            ce_vol = s.get("ce_volume", 0) or 0
            pe_vol = s.get("pe_volume", 0) or 0

            if avg_ce_vol > 0 and ce_vol > avg_ce_vol * 3:
                signals.append({
                    "strike": strike, "type": "CE", "volume": ce_vol,
                    "ratio": round(ce_vol / avg_ce_vol, 2),
                    "side": "BULLISH" if strike > spot else "BEARISH",
                })
            if avg_pe_vol > 0 and pe_vol > avg_pe_vol * 3:
                signals.append({
                    "strike": strike, "type": "PE", "volume": pe_vol,
                    "ratio": round(pe_vol / avg_pe_vol, 2),
                    "side": "BEARISH" if strike < spot else "BULLISH",
                })
        return signals

    def _detect_block_trades(self, chain: list) -> list:
        """Volume >> OI on a strike = new positions / block trades."""
        blocks = []
        for s in chain:
            strike = s.get("strike", 0)
            for opt_type in ["ce", "pe"]:
                vol = s.get(f"{opt_type}_volume", 0) or 0
                oi = s.get(f"{opt_type}_oi", 0) or 0
                if oi > 0 and vol > oi * 2:
                    blocks.append({
                        "strike": strike, "type": opt_type.upper(),
                        "volume": vol, "oi": oi,
                        "vol_oi_ratio": round(vol / oi, 2),
                    })
                elif oi == 0 and vol > 1000:
                    # Brand new position with high volume
                    blocks.append({
                        "strike": strike, "type": opt_type.upper(),
                        "volume": vol, "oi": 0,
                        "vol_oi_ratio": float("inf"),
                    })
        return blocks

    def _detect_otm_anomaly(self, chain: list, spot: float) -> list:
        """Far OTM strike with 5x normal OI."""
        if not chain:
            return []

        # Compute average OI
        all_oi = []
        for s in chain:
            all_oi.append(s.get("ce_oi", 0) or 0)
            all_oi.append(s.get("pe_oi", 0) or 0)
        avg_oi = sum(all_oi) / max(len(all_oi), 1) if all_oi else 0

        anomalies = []
        for s in chain:
            strike = s.get("strike", 0)
            distance_pct = abs(strike - spot) / spot * 100 if spot > 0 else 0
            if distance_pct < 2.0:  # Not far enough OTM
                continue

            ce_oi = s.get("ce_oi", 0) or 0
            pe_oi = s.get("pe_oi", 0) or 0

            if avg_oi > 0:
                if ce_oi > avg_oi * 5:
                    anomalies.append({
                        "strike": strike, "type": "CE", "oi": ce_oi,
                        "ratio": round(ce_oi / avg_oi, 2),
                        "distance_pct": round(distance_pct, 2),
                    })
                if pe_oi > avg_oi * 5:
                    anomalies.append({
                        "strike": strike, "type": "PE", "oi": pe_oi,
                        "ratio": round(pe_oi / avg_oi, 2),
                        "distance_pct": round(distance_pct, 2),
                    })
        return anomalies

    def _detect_multi_day_build(self, chain: list) -> list:
        """Same strike OI building 3 periods in a row."""
        builds = []
        for s in chain:
            strike = s.get("strike", 0)
            for opt_type in ["ce", "pe"]:
                oi = s.get(f"{opt_type}_oi", 0) or 0
                key = f"{strike}_{opt_type}"

                if key not in self._oi_history:
                    self._oi_history[key] = []
                self._oi_history[key].append(oi)
                if len(self._oi_history[key]) > self._max_history:
                    self._oi_history[key].pop(0)

                hist = self._oi_history[key]
                if len(hist) >= 3:
                    last3 = hist[-3:]
                    if last3[2] > last3[1] > last3[0] and last3[0] > 0:
                        growth = ((last3[2] - last3[0]) / last3[0]) * 100
                        builds.append({
                            "strike": strike, "type": opt_type.upper(),
                            "periods": 3, "current_oi": oi,
                            "growth_pct": round(growth, 2),
                        })
        return builds

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", [])
        spot = ctx.get("prices", {}).get("spot", 0) or ctx.get("prices", {}).get("ltp", 0)

        if not chain or spot <= 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain or spot"})

        uoa_signals = self._detect_uoa(chain, spot)
        block_trades = self._detect_block_trades(chain)
        otm_anomaly = self._detect_otm_anomaly(chain, spot)
        multi_day_build = self._detect_multi_day_build(chain)

        total_signals = len(uoa_signals) + len(block_trades) + len(otm_anomaly) + len(multi_day_build)
        categories_active = sum(1 for lst in [uoa_signals, block_trades, otm_anomaly, multi_day_build]
                                if len(lst) > 0)

        # Determine direction from UOA signals
        bullish = sum(1 for s in uoa_signals if s.get("side") == "BULLISH")
        bearish = sum(1 for s in uoa_signals if s.get("side") == "BEARISH")
        direction = "BULLISH" if bullish > bearish else ("BEARISH" if bearish > bullish else "NEUTRAL")

        confidence = min(20 + total_signals * 8 + categories_active * 10, 90)
        verdict = "PASS" if categories_active >= 2 else ("PARTIAL" if categories_active >= 1 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "uoa_signals": uoa_signals[:10],  # Cap for frontend
                "block_trades": block_trades[:5],
                "otm_anomaly": otm_anomaly[:5],
                "multi_day_build": multi_day_build[:5],
                "total_signals": total_signals,
                "categories_active": categories_active,
            }
        )
