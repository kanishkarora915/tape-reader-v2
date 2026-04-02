"""
E23 — Pre-Market Engine (Tier 4: Big Move)
Assesses morning bias from Gift Nifty / SGX, global cues, and gap prediction.
  - Gift Nifty level (placeholder: derived from previous close + global cues)
  - Global cues: Dow, Nasdaq, Asia indices (placeholder data for now)
  - Gap prediction based on overnight data
"""

from .base import BaseEngine, EngineResult


class PreMarketEngine(BaseEngine):
    name = "Pre-Market"
    tier = 4
    refresh_seconds = 60

    def __init__(self):
        super().__init__()

    def _assess_gift_nifty(self, ctx: dict) -> dict:
        """Derive Gift Nifty / SGX indication from context or placeholder."""
        premarket = ctx.get("premarket", {})
        gift_nifty = premarket.get("gift_nifty", 0)
        prev_close = ctx.get("prices", {}).get("prev_close", 0)

        if gift_nifty <= 0 and prev_close > 0:
            # Placeholder: use global cues to estimate
            global_cues = ctx.get("global_cues", {})
            dow_change = global_cues.get("dow_change_pct", 0)
            # Rough estimate: Nifty follows Dow at ~0.5x correlation
            estimated_change = dow_change * 0.5
            gift_nifty = prev_close * (1 + estimated_change / 100)

        if prev_close <= 0 or gift_nifty <= 0:
            return {"available": False, "gift_nifty": 0, "gap_pct": 0}

        gap_pct = ((gift_nifty - prev_close) / prev_close) * 100

        return {
            "available": True,
            "gift_nifty": round(gift_nifty, 2),
            "prev_close": prev_close,
            "gap_pct": round(gap_pct, 3),
            "direction": "BULLISH" if gap_pct > 0.1 else ("BEARISH" if gap_pct < -0.1 else "NEUTRAL"),
        }

    def _assess_global_cues(self, ctx: dict) -> dict:
        """Track Dow, Nasdaq, Asia overnight moves."""
        global_cues = ctx.get("global_cues", {})

        dow = global_cues.get("dow_change_pct", 0)
        nasdaq = global_cues.get("nasdaq_change_pct", 0)
        asia = global_cues.get("asia_change_pct", 0)  # Avg of SGX, Nikkei, Hang Seng

        signals = []
        for name, val in [("Dow", dow), ("Nasdaq", nasdaq), ("Asia", asia)]:
            if val > 0.5:
                signals.append({"index": name, "change": val, "bias": "BULLISH"})
            elif val < -0.5:
                signals.append({"index": name, "change": val, "bias": "BEARISH"})
            else:
                signals.append({"index": name, "change": val, "bias": "NEUTRAL"})

        bullish = sum(1 for s in signals if s["bias"] == "BULLISH")
        bearish = sum(1 for s in signals if s["bias"] == "BEARISH")

        overall = "BULLISH" if bullish > bearish else ("BEARISH" if bearish > bullish else "NEUTRAL")

        return {
            "signals": signals,
            "dow_pct": dow,
            "nasdaq_pct": nasdaq,
            "asia_pct": asia,
            "overall": overall,
        }

    def _predict_gap(self, gift_nifty_data: dict, global_data: dict) -> dict:
        """Predict gap open and fill probability."""
        gap_pct = gift_nifty_data.get("gap_pct", 0)
        abs_gap = abs(gap_pct)

        # Gap fill probability: smaller gaps fill more often
        if abs_gap < 0.2:
            fill_prob = 80
        elif abs_gap < 0.5:
            fill_prob = 65
        elif abs_gap < 1.0:
            fill_prob = 45
        else:
            fill_prob = 30

        # Adjust by global agreement
        global_dir = global_data.get("overall", "NEUTRAL")
        gap_dir = gift_nifty_data.get("direction", "NEUTRAL")
        if global_dir == gap_dir and global_dir != "NEUTRAL":
            fill_prob -= 10  # Gap supported by globals = less likely to fill

        prev_close = gift_nifty_data.get("prev_close", 0)
        gap_fill_target = prev_close if prev_close > 0 else 0

        return {
            "gap_expected": abs_gap > 0.15,
            "gap_pct": gap_pct,
            "gap_fill_probability": fill_prob,
            "gap_fill_target": gap_fill_target,
            "gap_direction": gift_nifty_data.get("direction", "NEUTRAL"),
        }

    def compute(self, ctx: dict) -> EngineResult:
        premarket = ctx.get("premarket", {})
        global_cues = ctx.get("global_cues", {})

        # If premarket and global_cues are empty, derive morning bias from VIX + spot
        has_premarket = bool(premarket) and (premarket.get("gift_nifty", 0) > 0)
        has_global = isinstance(global_cues, dict) and any(
            global_cues.get(k, 0) != 0 for k in ("dow_change_pct", "nasdaq_change_pct", "asia_change_pct")
        )

        if not has_premarket and not has_global:
            # Fallback: use VIX level + spot change as morning bias proxy
            vix = ctx.get("vix", 0)
            prices = ctx.get("prices", {})
            spot = prices.get("spot", 0) if isinstance(prices, dict) else 0
            change_pct = prices.get("change_pct", 0) if isinstance(prices, dict) else 0
            prev_close = prices.get("prev_close", 0) if isinstance(prices, dict) else 0

            direction = "NEUTRAL"
            confidence = 25

            if isinstance(change_pct, (int, float)) and abs(change_pct) > 0.15:
                direction = "BULLISH" if change_pct > 0 else "BEARISH"
                confidence = min(55, 30 + int(abs(change_pct) * 12))

            # VIX > 18 suggests caution
            if isinstance(vix, (int, float)) and vix > 18:
                confidence = max(confidence - 10, 15)

            verdict = "PARTIAL" if direction != "NEUTRAL" else "NEUTRAL"

            return EngineResult(
                verdict=verdict,
                direction=direction,
                confidence=confidence,
                data={
                    "morning_bias": direction,
                    "gift_nifty": 0,
                    "gap_expected": False,
                    "gap_pct": 0,
                    "gap_fill_target": prev_close if prev_close else 0,
                    "gap_fill_probability": 50,
                    "global_cues": {"signals": [], "overall": "NEUTRAL"},
                    "proxy": True,
                    "proxy_source": f"VIX={vix:.1f}, Spot chg={change_pct:+.2f}%" if isinstance(vix, (int, float)) else "N/A",
                }
            )

        gift_data = self._assess_gift_nifty(ctx)
        global_data = self._assess_global_cues(ctx)
        gap_data = self._predict_gap(gift_data, global_data)

        # Morning bias = consensus of gift nifty + global cues
        directions = [
            gift_data.get("direction", "NEUTRAL"),
            global_data.get("overall", "NEUTRAL"),
        ]
        bullish = sum(1 for d in directions if d == "BULLISH")
        bearish = sum(1 for d in directions if d == "BEARISH")

        if bullish > bearish:
            morning_bias = "BULLISH"
        elif bearish > bullish:
            morning_bias = "BEARISH"
        else:
            morning_bias = "NEUTRAL"

        has_data = gift_data.get("available", False) or any(
            s.get("bias") != "NEUTRAL" for s in global_data.get("signals", []))

        confidence = 30
        if has_data:
            confidence += 20
        abs_gap = abs(gift_data.get("gap_pct", 0))
        if abs_gap > 0.5:
            confidence += 20
        if morning_bias != "NEUTRAL":
            confidence += 10

        verdict = "PASS" if has_data and morning_bias != "NEUTRAL" else (
            "PARTIAL" if has_data else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=morning_bias,
            confidence=min(confidence, 90),
            data={
                "morning_bias": morning_bias,
                "gift_nifty": gift_data.get("gift_nifty", 0),
                "gap_expected": gap_data["gap_expected"],
                "gap_pct": gap_data["gap_pct"],
                "gap_fill_target": gap_data["gap_fill_target"],
                "gap_fill_probability": gap_data["gap_fill_probability"],
                "global_cues": global_data,
            }
        )
