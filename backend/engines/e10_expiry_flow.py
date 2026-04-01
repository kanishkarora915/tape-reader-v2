"""
E10 — Expiry Flow Engine (Tier 2: Direction)
Computes Max Pain, days-to-expiry, OI drift direction.
Near-expiry (<2 days) activates ATM-only rule.
"""

from datetime import datetime, timedelta
from .base import BaseEngine, EngineResult


class ExpiryFlowEngine(BaseEngine):
    name = "Expiry Flow"
    tier = 2
    refresh_seconds = 10

    def _compute_max_pain(self, chain: dict, strikes: list) -> float:
        """Max Pain = strike where total pain to all writers is minimum."""
        if not strikes:
            return 0

        min_pain = float("inf")
        max_pain_strike = strikes[len(strikes) // 2]

        for test_strike in strikes:
            total_pain = 0
            for s in strikes:
                entry = chain.get(s, chain.get(str(s), {}))
                if not isinstance(entry, dict):
                    continue

                ce_oi = entry.get("ce_oi", entry.get("call_oi", 0)) or 0
                pe_oi = entry.get("pe_oi", entry.get("put_oi", 0)) or 0

                # Call writer pain: if expiry at test_strike, calls ITM for strikes < test_strike
                # Actually: CE buyer profit = max(0, test_strike - s) for each CE OI at strike s
                # Wait, CE buyer profits when test > strike... no.
                # CE at strike s is ITM if test_strike > s:
                #   CE holder profit = (test_strike - s) * ce_oi
                # PE at strike s is ITM if test_strike < s:
                #   PE holder profit = (s - test_strike) * pe_oi

                if test_strike > s:
                    total_pain += (test_strike - s) * ce_oi
                if test_strike < s:
                    total_pain += (s - test_strike) * pe_oi

            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = test_strike

        return max_pain_strike

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", {})
        spot = ctx.get("prices", {}).get("spot", 0)

        if not chain or spot == 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain/spot"})

        strikes = sorted([int(s) for s in chain.keys() if str(s).isdigit()])
        if not strikes:
            return EngineResult(verdict="NEUTRAL", data={"error": "No strikes"})

        # Days to expiry
        expiry_str = ctx.get("expiry_date", "")
        dte = ctx.get("days_to_expiry", 7)

        if expiry_str:
            try:
                expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d")
                dte = max(0, (expiry_dt - datetime.now()).days)
            except (ValueError, TypeError):
                pass

        # Expiry type
        if dte <= 7:
            expiry_type = "weekly"
        else:
            expiry_type = "monthly"

        # Max Pain
        max_pain = self._compute_max_pain(chain, strikes)

        # OI drift: compare OI build in calls vs puts at different regions
        step = strikes[1] - strikes[0] if len(strikes) > 1 else 50
        atm = min(strikes, key=lambda s: abs(s - spot))

        otm_ce_oi = 0  # strikes > ATM
        otm_pe_oi = 0  # strikes < ATM
        itm_ce_oi = 0
        itm_pe_oi = 0

        for s in strikes:
            entry = chain.get(s, chain.get(str(s), {}))
            if not isinstance(entry, dict):
                continue
            ce_oi = entry.get("ce_oi", entry.get("call_oi", 0)) or 0
            pe_oi = entry.get("pe_oi", entry.get("put_oi", 0)) or 0

            if s > atm:
                otm_ce_oi += ce_oi
                itm_pe_oi += pe_oi
            elif s < atm:
                otm_pe_oi += pe_oi
                itm_ce_oi += ce_oi

        # OI drift direction: heavy OTM put writing = support building = BULLISH
        total_otm = otm_ce_oi + otm_pe_oi
        if total_otm > 0:
            pe_dominance = otm_pe_oi / total_otm
        else:
            pe_dominance = 0.5

        if pe_dominance > 0.6:
            oi_drift = "BULLISH"  # more puts written OTM = support
        elif pe_dominance < 0.4:
            oi_drift = "BEARISH"  # more calls written OTM = resistance
        else:
            oi_drift = "NEUTRAL"

        # Direction
        direction = "NEUTRAL"
        confidence = 40
        verdict = "PARTIAL"

        # Max pain pull: price tends to move toward max pain near expiry
        mp_distance = (max_pain - spot) / spot * 100 if spot > 0 else 0

        if dte <= 2:
            # Near expiry: ATM-only rule, max pain gravitational pull
            if mp_distance > 0.3:
                direction = "BULLISH"
                confidence = 65
            elif mp_distance < -0.3:
                direction = "BEARISH"
                confidence = 65
            else:
                direction = "NEUTRAL"
                confidence = 50
            verdict = "PASS" if direction != "NEUTRAL" else "PARTIAL"
        else:
            # Regular: use OI drift
            direction = oi_drift
            confidence = 55 if direction != "NEUTRAL" else 35
            verdict = "PASS" if direction != "NEUTRAL" else "PARTIAL"

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 85),
            data={
                "max_pain": max_pain,
                "days_to_expiry": dte,
                "oi_drift_direction": oi_drift,
                "expiry_type": expiry_type,
                "mp_distance_pct": round(mp_distance, 2),
                "otm_ce_oi": otm_ce_oi,
                "otm_pe_oi": otm_pe_oi,
                "pe_dominance": round(pe_dominance, 3),
                "atm_strike": atm,
            }
        )
