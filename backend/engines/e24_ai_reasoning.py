"""
E24 — AI Reasoning Engine (Tier 4: Big Move)
Synthesizes all 23 engine outputs via Claude API.
  - Builds structured prompt with engine verdicts
  - Calls Claude API via services/claude_api.py
  - Parses response into: rationale, risk_factors, confidence_assessment
  - Rate limited: only calls Claude when signal fires or every 2 minutes max
"""

import time
import json
from .base import BaseEngine, EngineResult


class AIReasoningEngine(BaseEngine):
    name = "AI Reasoning"
    tier = 4
    refresh_seconds = 30

    def __init__(self):
        super().__init__()
        self._last_call_time = 0
        self._min_interval = 120  # 2 minutes between API calls
        self._last_ai_result = None
        self._cached_prompt_hash = None

    def _should_call_api(self, signal_fired: bool) -> bool:
        """Rate limit: call only when signal fires or every 2 minutes."""
        now = time.time()
        elapsed = now - self._last_call_time
        if signal_fired and elapsed > 10:
            return True
        if elapsed >= self._min_interval:
            return True
        return False

    def _build_prompt(self, engine_states: dict, ctx: dict) -> str:
        """Build structured prompt from all engine verdicts."""
        lines = [
            "You are an expert derivatives trader analyzing the Indian options market.",
            "Below are real-time signals from 23 trading engines. Synthesize them into a single",
            "actionable assessment.\n",
            "=== ENGINE VERDICTS ===",
        ]

        for key in sorted(engine_states.keys()):
            state = engine_states[key]
            if isinstance(state, dict):
                name = state.get("name", key)
                verdict = state.get("verdict", "NEUTRAL")
                direction = state.get("direction", "NEUTRAL")
                confidence = state.get("confidence", 0)
                tier = state.get("tier", 0)
                lines.append(
                    f"  {key} ({name}) [Tier {tier}]: "
                    f"verdict={verdict}, direction={direction}, confidence={confidence}%"
                )
                # Include key data points
                data = state.get("data", {})
                important_keys = [k for k in data.keys()
                                  if not isinstance(data[k], (list, dict)) or k in [
                                      "direction", "verdict"]][:5]
                for dk in important_keys:
                    lines.append(f"    {dk}: {data[dk]}")

        # Context data
        prices = ctx.get("prices", {})
        spot = prices.get("spot", 0) or prices.get("ltp", 0)
        vix = ctx.get("vix", {}).get("current", 0)
        dte = ctx.get("dte", "?")

        lines.extend([
            f"\n=== MARKET CONTEXT ===",
            f"  Spot: {spot}",
            f"  VIX: {vix}",
            f"  DTE: {dte}",
            f"\n=== INSTRUCTIONS ===",
            "Respond ONLY in this JSON format:",
            '{',
            '  "rationale": "2-3 sentence synthesis of the overall market picture",',
            '  "risk_factors": ["risk1", "risk2", "risk3"],',
            '  "confidence": <0-100>,',
            '  "direction": "BULLISH" | "BEARISH" | "NEUTRAL",',
            '  "trade_recommendation": "specific actionable recommendation or WAIT"',
            '}',
        ])

        return "\n".join(lines)

    def _call_claude(self, prompt: str) -> dict:
        """Call Claude API. Tries to import from services/claude_api.py."""
        try:
            from ..services.claude_api import call_claude
            response_text = call_claude(prompt)
        except (ImportError, Exception):
            # Fallback: return a placeholder when API is unavailable
            return {
                "rationale": "AI service unavailable. Manual analysis required based on engine signals.",
                "risk_factors": ["API unavailable", "Use engine verdicts directly"],
                "confidence": 0,
                "direction": "NEUTRAL",
                "trade_recommendation": "WAIT - AI analysis offline",
            }

        # Parse JSON from response
        try:
            # Try to extract JSON from response
            text = response_text.strip()
            # Handle markdown code blocks
            if "```" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    text = text[start:end]
            parsed = json.loads(text)
            return {
                "rationale": parsed.get("rationale", ""),
                "risk_factors": parsed.get("risk_factors", []),
                "confidence": int(parsed.get("confidence", 50)),
                "direction": parsed.get("direction", "NEUTRAL"),
                "trade_recommendation": parsed.get("trade_recommendation", "WAIT"),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "rationale": response_text[:500] if response_text else "Parse error",
                "risk_factors": ["Response parse error"],
                "confidence": 30,
                "direction": "NEUTRAL",
                "trade_recommendation": "WAIT - parse error",
            }

    def _fallback_synthesis(self, engine_states: dict) -> dict:
        """Quick rule-based synthesis when not calling API."""
        verdicts = {}
        directions = {}
        confidences = []

        for key, state in engine_states.items():
            if not isinstance(state, dict):
                continue
            v = state.get("verdict", "NEUTRAL")
            d = state.get("direction", "NEUTRAL")
            c = state.get("confidence", 0)
            tier = state.get("tier", 0)

            verdicts[v] = verdicts.get(v, 0) + 1
            if d != "NEUTRAL":
                weight = 1 + (tier * 0.5)
                directions[d] = directions.get(d, 0) + weight
            if c > 0:
                confidences.append(c)

        pass_count = verdicts.get("PASS", 0)
        fail_count = verdicts.get("FAIL", 0)

        bull_score = directions.get("BULLISH", 0)
        bear_score = directions.get("BEARISH", 0)

        if bull_score > bear_score * 1.3:
            direction = "BULLISH"
        elif bear_score > bull_score * 1.3:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        avg_conf = int(sum(confidences) / len(confidences)) if confidences else 30

        return {
            "rationale": (
                f"Rule-based: {pass_count} engines PASS, {fail_count} FAIL. "
                f"Directional scores: BULL={bull_score:.1f}, BEAR={bear_score:.1f}."
            ),
            "risk_factors": [
                f"{fail_count} engines failing" if fail_count > 3 else "Few failures",
                "Mixed signals" if direction == "NEUTRAL" else f"Leaning {direction}",
            ],
            "confidence": avg_conf,
            "direction": direction,
            "trade_recommendation": (
                f"Lean {direction}" if direction != "NEUTRAL" and avg_conf > 55
                else "WAIT for clarity"
            ),
        }

    def compute(self, ctx: dict) -> EngineResult:
        prev_results = ctx.get("previous_results", {})

        # Collect engine states
        engine_states = {}
        for key, val in prev_results.items():
            if hasattr(val, "get_state") if hasattr(val, "get_state") else False:
                engine_states[key] = val.get_state()
            elif isinstance(val, dict):
                engine_states[key] = val

        # Check if any signal fired (PASS verdicts in tier 4 engines)
        signal_fired = any(
            engine_states.get(f"e{i}", {}).get("verdict") == "PASS"
            for i in range(19, 24)
        )

        if self._should_call_api(signal_fired) and engine_states:
            prompt = self._build_prompt(engine_states, ctx)
            ai_result = self._call_claude(prompt)
            self._last_call_time = time.time()
            self._last_ai_result = ai_result
        elif self._last_ai_result:
            ai_result = self._last_ai_result
        else:
            ai_result = self._fallback_synthesis(engine_states)

        direction = ai_result.get("direction", "NEUTRAL")
        ai_confidence = ai_result.get("confidence", 30)

        verdict = "PASS" if ai_confidence > 60 and direction != "NEUTRAL" else (
            "PARTIAL" if ai_confidence > 40 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(ai_confidence, 95),
            data={
                "rationale": ai_result.get("rationale", ""),
                "risk_factors": ai_result.get("risk_factors", []),
                "confidence": ai_confidence,
                "trade_recommendation": ai_result.get("trade_recommendation", "WAIT"),
                "api_called": self._last_call_time == time.time(),
                "signal_triggered": signal_fired,
            }
        )
