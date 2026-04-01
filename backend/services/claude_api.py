"""
BuyBy Trading System — Anthropic Claude Integration (Engine E24)
Calls Claude for AI-powered trade reasoning and risk assessment.
"""

import json
import logging

import anthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger("buyby.claude")

MODEL = "claude-sonnet-4-20250514"


async def get_reasoning(engine_states: dict, signal_data: dict) -> dict:
    """
    Call Claude API with engine states and signal data.
    Returns structured reasoning dict with: rationale, risk_factors, confidence.
    Returns empty dict on failure (never raises).
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("[CLAUDE] API key not configured — skipping AI reasoning")
        return {}

    # Build the prompt
    prompt = _build_prompt(engine_states, signal_data)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            system=(
                "You are an expert options trading analyst for the Indian markets (NSE/BSE). "
                "Analyze the engine verdicts and market data provided. "
                "Respond ONLY with valid JSON containing: "
                '{"rationale": "...", "risk_factors": ["..."], "confidence": "HIGH|MEDIUM|LOW", "key_drivers": ["..."]}'
            ),
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response_text[start:end])
            else:
                result = {"rationale": response_text, "risk_factors": [], "confidence": "LOW"}

        logger.info(f"[CLAUDE] Reasoning generated. Confidence: {result.get('confidence', 'N/A')}")
        return result

    except Exception as e:
        logger.error(f"[CLAUDE] API call failed: {e}")
        return {}


def _build_prompt(engine_states: dict, signal_data: dict) -> str:
    """Build a structured prompt with all engine verdicts and signal data."""
    engine_summary = []
    for eid, state in sorted(engine_states.items()):
        verdict = state.get("verdict", "N/A")
        direction = state.get("direction", "N/A")
        label = state.get("label", eid)
        score = state.get("score", 0)
        engine_summary.append(f"  {eid} ({label}): verdict={verdict}, direction={direction}, score={score}")

    engines_text = "\n".join(engine_summary)

    signal_type = signal_data.get("type", "UNKNOWN")
    instrument = signal_data.get("instrument", "N/A")
    strike = signal_data.get("strike", 0)
    mode = signal_data.get("mode", "NORMAL")
    score = signal_data.get("score", 0)
    max_score = signal_data.get("maxScore", 0)

    return f"""Analyze this trading signal from the BuyBy 24-engine system:

SIGNAL: {signal_type}
Instrument: {instrument} | Strike: {strike} | Mode: {mode}
Score: {score}/{max_score}

ENGINE VERDICTS:
{engines_text}

Based on the engine verdicts:
1. What is the primary trade rationale?
2. What are the top 3 risk factors?
3. What is your confidence level (HIGH/MEDIUM/LOW) and why?
4. What are the key drivers behind this signal?

Respond in JSON format only."""
