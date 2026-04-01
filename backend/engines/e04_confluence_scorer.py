"""
E04 — Confluence Scorer Engine (Tier 1: Core Gate)
Aggregates results from E01-E03 (T1 gates) and E05-E11 (T2 direction) engines.
Computes weighted directional score and determines if confluence gate passes.
"""

from .base import BaseEngine, EngineResult


class ConfluenceScorerEngine(BaseEngine):
    name = "Confluence Scorer"
    tier = 1
    refresh_seconds = 5

    # T1 engines: binary gate check
    T1_ENGINES = ["e01", "e02", "e03"]
    # T2 engines: directional vote
    T2_ENGINES = ["e05", "e06", "e07", "e08", "e09", "e10", "e11"]
    # Minimum T2 votes in same direction to pass
    MIN_T2_CONSENSUS = 3

    def compute(self, ctx: dict) -> EngineResult:
        prev = ctx.get("previous_results", {})
        if not prev:
            return EngineResult(verdict="NEUTRAL", confidence=10,
                                data={"error": "No previous engine results"})

        # --- T1 Gate Check ---
        t1_passed = 0
        t1_total = 0
        t1_details = {}

        for eid in self.T1_ENGINES:
            result = prev.get(eid)
            if result is None:
                continue
            t1_total += 1
            v = result.get("verdict", "NEUTRAL")
            t1_details[eid] = v
            if v in ("PASS", "PARTIAL"):
                t1_passed += 1

        # All T1 gates must pass (PASS or PARTIAL) for the system to proceed
        t1_gate_open = t1_passed >= t1_total and t1_total > 0

        # --- T2 Directional Votes ---
        t2_bull = 0
        t2_bear = 0
        t2_neutral = 0
        t2_details = {}

        for eid in self.T2_ENGINES:
            result = prev.get(eid)
            if result is None:
                continue
            d = result.get("direction", "NEUTRAL")
            t2_details[eid] = d
            if d == "BULLISH":
                t2_bull += 1
            elif d == "BEARISH":
                t2_bear += 1
            else:
                t2_neutral += 1

        # E01 and E03 also contribute direction votes
        for eid in ["e01", "e03"]:
            result = prev.get(eid)
            if result is None:
                continue
            d = result.get("direction", "NEUTRAL")
            if d == "BULLISH":
                t2_bull += 1
            elif d == "BEARISH":
                t2_bear += 1

        # Total directional votes
        max_score = len(self.T2_ENGINES) + 2  # +2 for e01, e03 direction
        total_votes = t2_bull + t2_bear + t2_neutral

        # Determine consensus direction
        if t2_bull >= self.MIN_T2_CONSENSUS and t2_bull > t2_bear:
            consensus_direction = "BULLISH"
            total_score = t2_bull
        elif t2_bear >= self.MIN_T2_CONSENSUS and t2_bear > t2_bull:
            consensus_direction = "BEARISH"
            total_score = t2_bear
        else:
            consensus_direction = "NEUTRAL"
            total_score = max(t2_bull, t2_bear)

        # Final gate
        gate_passed = t1_gate_open and consensus_direction != "NEUTRAL"

        # Confidence based on score ratio and gate status
        if gate_passed:
            score_ratio = total_score / max_score if max_score > 0 else 0
            confidence = int(50 + score_ratio * 45)  # 50-95
            verdict = "PASS"
        elif t1_gate_open and consensus_direction == "NEUTRAL":
            confidence = 30
            verdict = "PARTIAL"
        else:
            confidence = 15
            verdict = "FAIL"

        direction = consensus_direction if gate_passed else "NEUTRAL"

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 95),
            data={
                "total_score": total_score,
                "max_score": max_score,
                "t2_bull_votes": t2_bull,
                "t2_bear_votes": t2_bear,
                "t2_neutral_votes": t2_neutral,
                "direction": consensus_direction,
                "gate_passed": gate_passed,
                "t1_gate_open": t1_gate_open,
                "t1_details": t1_details,
                "t2_details": t2_details,
            }
        )
