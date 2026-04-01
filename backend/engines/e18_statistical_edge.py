"""
E18 — Statistical Edge Engine (Tier 3: Amplifier)
Pattern matching using current IVR, day of week, DTE, PCR zone.
  - Historical win rate from lookup table (simplified)
  - Monte Carlo simulation of N scenarios based on current conditions
  - Edge score combining win rate + monte carlo
"""

import random
import numpy as np
from .base import BaseEngine, EngineResult


class StatisticalEdgeEngine(BaseEngine):
    name = "Statistical Edge"
    tier = 3
    refresh_seconds = 30

    def __init__(self):
        super().__init__()
        self._monte_carlo_runs = 500
        # Simplified lookup: (ivr_zone, dow, dte_zone, pcr_zone) -> win_rate
        # ivr_zone: LOW(<25), MID(25-50), HIGH(>50)
        # pcr_zone: LOW(<0.7), MID(0.7-1.0), HIGH(>1.0)
        # dte_zone: NEAR(<3), MID(3-10), FAR(>10)
        self._lookup_table = {
            # High IVR + High PCR + Near expiry = high win for sellers
            ("HIGH", "NEAR", "HIGH"): {"win_rate": 72, "bias": "BEARISH"},
            ("HIGH", "NEAR", "MID"): {"win_rate": 65, "bias": "NEUTRAL"},
            ("HIGH", "NEAR", "LOW"): {"win_rate": 58, "bias": "BULLISH"},
            ("HIGH", "MID", "HIGH"): {"win_rate": 62, "bias": "BEARISH"},
            ("HIGH", "MID", "MID"): {"win_rate": 55, "bias": "NEUTRAL"},
            ("HIGH", "MID", "LOW"): {"win_rate": 60, "bias": "BULLISH"},
            ("HIGH", "FAR", "HIGH"): {"win_rate": 50, "bias": "BEARISH"},
            ("MID", "NEAR", "HIGH"): {"win_rate": 60, "bias": "BEARISH"},
            ("MID", "NEAR", "MID"): {"win_rate": 52, "bias": "NEUTRAL"},
            ("MID", "NEAR", "LOW"): {"win_rate": 55, "bias": "BULLISH"},
            ("MID", "MID", "MID"): {"win_rate": 50, "bias": "NEUTRAL"},
            ("LOW", "NEAR", "HIGH"): {"win_rate": 55, "bias": "BEARISH"},
            ("LOW", "NEAR", "LOW"): {"win_rate": 58, "bias": "BULLISH"},
            ("LOW", "MID", "MID"): {"win_rate": 48, "bias": "NEUTRAL"},
        }

    def _classify_ivr(self, ivr: float) -> str:
        if ivr > 50:
            return "HIGH"
        elif ivr > 25:
            return "MID"
        return "LOW"

    def _classify_dte(self, dte: int) -> str:
        if dte <= 3:
            return "NEAR"
        elif dte <= 10:
            return "MID"
        return "FAR"

    def _classify_pcr(self, pcr: float) -> str:
        if pcr > 1.0:
            return "HIGH"
        elif pcr > 0.7:
            return "MID"
        return "LOW"

    def _lookup_win_rate(self, ivr_zone: str, dte_zone: str, pcr_zone: str) -> dict:
        """Lookup historical win rate from simplified table."""
        key = (ivr_zone, dte_zone, pcr_zone)
        if key in self._lookup_table:
            return self._lookup_table[key]
        # Default fallback
        return {"win_rate": 50, "bias": "NEUTRAL"}

    def _monte_carlo(self, win_rate: float, avg_win: float, avg_loss: float) -> dict:
        """Run N Monte Carlo scenarios and compute expected score."""
        results = []
        for _ in range(self._monte_carlo_runs):
            pnl = 0
            for _ in range(10):  # 10 trades per simulation
                if random.random() < win_rate / 100:
                    pnl += avg_win
                else:
                    pnl -= avg_loss
            results.append(pnl)

        results = np.array(results)
        positive_pct = (results > 0).sum() / len(results) * 100
        avg_pnl = float(np.mean(results))

        return {
            "positive_scenarios_pct": round(positive_pct, 1),
            "avg_pnl": round(avg_pnl, 2),
            "worst_case": round(float(np.percentile(results, 5)), 2),
            "best_case": round(float(np.percentile(results, 95)), 2),
            "monte_carlo_score": round(positive_pct, 1),
        }

    def compute(self, ctx: dict) -> EngineResult:
        prev_results = ctx.get("previous_results", {})

        # Extract IVR from e02
        e02 = prev_results.get("e02", {})
        e02_data = e02.get("data", {}) if isinstance(e02, dict) else {}
        if hasattr(e02, "data"):
            e02_data = e02.data
        ivr = e02_data.get("ivr", 50)

        # Extract PCR from e06
        e06 = prev_results.get("e06", {})
        e06_data = e06.get("data", {}) if isinstance(e06, dict) else {}
        if hasattr(e06, "data"):
            e06_data = e06.data
        pcr = e06_data.get("pcr", 0.85)

        # DTE from context
        dte = ctx.get("dte", 5)

        # Day of week from context (0=Mon, 4=Fri)
        import datetime
        dow = ctx.get("day_of_week", datetime.datetime.now().weekday())

        ivr_zone = self._classify_ivr(ivr)
        dte_zone = self._classify_dte(dte)
        pcr_zone = self._classify_pcr(pcr)

        lookup = self._lookup_win_rate(ivr_zone, dte_zone, pcr_zone)
        win_rate = lookup["win_rate"]
        bias = lookup["bias"]

        # Monte Carlo with estimated win/loss sizes
        avg_win = 1.5  # Normalized
        avg_loss = 1.0
        mc = self._monte_carlo(win_rate, avg_win, avg_loss)

        # Edge score: combination of win rate and MC positive scenarios
        edge_score = round((win_rate * 0.6 + mc["monte_carlo_score"] * 0.4), 1)

        similar_setups = f"IVR={ivr_zone}, DTE={dte_zone}, PCR={pcr_zone}, DOW={dow}"

        verdict = "PASS" if edge_score > 60 else ("PARTIAL" if edge_score > 50 else "NEUTRAL")
        direction = bias
        confidence = min(int(edge_score), 90)

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "win_rate": win_rate,
                "monte_carlo_score": mc["monte_carlo_score"],
                "similar_setups": similar_setups,
                "edge_score": edge_score,
                "ivr_zone": ivr_zone,
                "dte_zone": dte_zone,
                "pcr_zone": pcr_zone,
                "day_of_week": dow,
                "monte_carlo": mc,
            }
        )
