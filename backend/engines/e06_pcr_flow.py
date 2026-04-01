"""
E06 — PCR Flow Engine (Tier 2: Direction)
Computes Put-Call Ratio from total OI across the chain.
Contrarian interpretation: extreme PCR = reversal signal.
Tracks intraday PCR rate of change.
"""

from .base import BaseEngine, EngineResult


class PCRFlowEngine(BaseEngine):
    name = "PCR Flow"
    tier = 2
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._pcr_history = []   # rolling PCR values
        self._max_history = 120  # ~10 min at 5s

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", {})
        if not chain:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain data"})

        total_ce_oi = 0
        total_pe_oi = 0

        for key, entry in chain.items():
            if not isinstance(entry, dict):
                continue
            total_ce_oi += entry.get("ce_oi", entry.get("call_oi", 0)) or 0
            total_pe_oi += entry.get("pe_oi", entry.get("put_oi", 0)) or 0

        if total_ce_oi == 0:
            return EngineResult(verdict="NEUTRAL", confidence=10,
                                data={"error": "Zero CE OI"})

        pcr = total_pe_oi / total_ce_oi

        # Track history
        self._pcr_history.append(pcr)
        if len(self._pcr_history) > self._max_history:
            self._pcr_history.pop(0)

        # PCR rate of change
        pcr_change = 0.0
        if len(self._pcr_history) >= 2:
            old_pcr = self._pcr_history[0]
            if old_pcr > 0:
                pcr_change = ((pcr - old_pcr) / old_pcr) * 100

        # Contrarian interpretation
        direction = "NEUTRAL"
        bias = "NEUTRAL"
        confidence = 40
        verdict = "PARTIAL"

        if pcr > 1.4:
            direction = "BULLISH"
            bias = "EXTREME_FEAR"
            confidence = 70 + min(int((pcr - 1.4) * 30), 25)
            verdict = "PASS"
        elif pcr > 1.2:
            direction = "BULLISH"
            bias = "FEAR"
            confidence = 55
            verdict = "PASS"
        elif pcr < 0.5:
            direction = "BEARISH"
            bias = "EXTREME_GREED"
            confidence = 70 + min(int((0.5 - pcr) * 60), 25)
            verdict = "PASS"
        elif pcr < 0.7:
            direction = "BEARISH"
            bias = "GREED"
            confidence = 55
            verdict = "PASS"
        else:
            # Normal range 0.7 - 1.2
            bias = "NORMAL"
            confidence = 30

            # Mild directional from PCR change
            if pcr_change > 10:
                direction = "BULLISH"  # PCR rising = more puts = contrarian bullish
                confidence = 45
            elif pcr_change < -10:
                direction = "BEARISH"  # PCR falling = fewer puts = contrarian bearish
                confidence = 45

        interpretation = f"PCR={pcr:.2f} ({bias})"
        if pcr_change != 0:
            interpretation += f", change={pcr_change:+.1f}%"

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 95),
            data={
                "pcr": round(pcr, 3),
                "pcr_change": round(pcr_change, 2),
                "bias": bias,
                "interpretation": interpretation,
                "total_ce_oi": total_ce_oi,
                "total_pe_oi": total_pe_oi,
            }
        )
