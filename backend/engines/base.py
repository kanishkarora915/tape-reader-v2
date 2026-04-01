from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EngineResult:
    verdict: str = "NEUTRAL"      # PASS, FAIL, NEUTRAL, PARTIAL
    direction: str = "NEUTRAL"    # BULLISH, BEARISH, NEUTRAL
    confidence: int = 0           # 0-100
    data: dict = field(default_factory=dict)  # Panel-specific data for frontend

class BaseEngine(ABC):
    name: str = ""
    tier: int = 0
    refresh_seconds: int = 5

    def __init__(self):
        self._last_result = EngineResult()

    @abstractmethod
    def compute(self, ctx: dict) -> EngineResult:
        """ctx has: prices, chains, candles, vix, previous_results"""
        pass

    @property
    def last_result(self) -> EngineResult:
        return self._last_result

    def run(self, ctx: dict) -> EngineResult:
        try:
            self._last_result = self.compute(ctx)
        except Exception as e:
            self._last_result = EngineResult(verdict="NEUTRAL", data={"error": str(e)})
        return self._last_result

    def get_state(self) -> dict:
        r = self._last_result
        return {"name": self.name, "tier": self.tier, "verdict": r.verdict,
                "direction": r.direction, "confidence": r.confidence, "data": r.data}
