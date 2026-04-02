"""
E17 — Cross-Asset Correlation Engine (Tier 3: Amplifier)
Monitors USD/INR, Crude, Gold correlation with Nifty.
  - INR weakening (USD/INR rising) = bearish equities
  - Crude spiking = bearish
  - Gold rising = risk-off = bearish
Fires when 2+ cross-asset signals agree on direction.
"""

from .base import BaseEngine, EngineResult


class CrossAssetEngine(BaseEngine):
    name = "Cross-Asset"
    tier = 3
    refresh_seconds = 15

    def __init__(self):
        super().__init__()
        self._usdinr_threshold = 0.15   # % move threshold
        self._crude_threshold = 1.5     # % move threshold
        self._gold_threshold = 0.8      # % move threshold

    def _assess_usdinr(self, data: dict) -> dict:
        """INR weakening (USD/INR rising) = bearish equities."""
        current = data.get("current", 0)
        prev_close = data.get("prev_close", 0) or data.get("open", 0)
        if current <= 0 or prev_close <= 0:
            return {"active": False, "change_pct": 0, "direction": "NEUTRAL"}

        change_pct = ((current - prev_close) / prev_close) * 100
        # USD/INR rising = INR weakening = bearish for equities
        if change_pct > self._usdinr_threshold:
            direction = "BEARISH"
            active = True
        elif change_pct < -self._usdinr_threshold:
            direction = "BULLISH"
            active = True
        else:
            direction = "NEUTRAL"
            active = False

        return {
            "active": active,
            "change_pct": round(change_pct, 3),
            "current": current,
            "direction": direction,
        }

    def _assess_crude(self, data: dict) -> dict:
        """Crude spiking = bearish for equities."""
        current = data.get("current", 0)
        prev_close = data.get("prev_close", 0) or data.get("open", 0)
        if current <= 0 or prev_close <= 0:
            return {"active": False, "change_pct": 0, "direction": "NEUTRAL"}

        change_pct = ((current - prev_close) / prev_close) * 100
        if change_pct > self._crude_threshold:
            direction = "BEARISH"
            active = True
        elif change_pct < -self._crude_threshold:
            direction = "BULLISH"
            active = True
        else:
            direction = "NEUTRAL"
            active = False

        return {
            "active": active,
            "change_pct": round(change_pct, 3),
            "current": current,
            "direction": direction,
        }

    def _assess_gold(self, data: dict) -> dict:
        """Gold rising = risk-off = bearish equities."""
        current = data.get("current", 0)
        prev_close = data.get("prev_close", 0) or data.get("open", 0)
        if current <= 0 or prev_close <= 0:
            return {"active": False, "change_pct": 0, "direction": "NEUTRAL"}

        change_pct = ((current - prev_close) / prev_close) * 100
        if change_pct > self._gold_threshold:
            direction = "BEARISH"  # Gold up = risk-off = bearish equities
            active = True
        elif change_pct < -self._gold_threshold:
            direction = "BULLISH"
            active = True
        else:
            direction = "NEUTRAL"
            active = False

        return {
            "active": active,
            "change_pct": round(change_pct, 3),
            "current": current,
            "direction": direction,
        }

    def compute(self, ctx: dict) -> EngineResult:
        cross_assets = ctx.get("cross_assets", {})

        # Fallback: when no cross-asset data, derive from VIX and spot movement
        if not cross_assets or all(not cross_assets.get(k) for k in ("usdinr", "crude", "gold")):
            vix = ctx.get("vix", 0)
            prices = ctx.get("prices", {})
            change_pct = prices.get("change_pct", 0) if isinstance(prices, dict) else 0

            # VIX spike = risk-off = bearish, VIX low = risk-on = neutral/bullish
            direction = "NEUTRAL"
            confidence = 20
            verdict = "NEUTRAL"

            if isinstance(vix, (int, float)) and vix > 0:
                if vix > 20:
                    direction = "BEARISH"
                    confidence = 45
                    verdict = "PARTIAL"
                elif vix < 12 and isinstance(change_pct, (int, float)) and change_pct > 0.3:
                    direction = "BULLISH"
                    confidence = 40
                    verdict = "PARTIAL"

            return EngineResult(
                verdict=verdict, direction=direction, confidence=confidence,
                data={
                    "usdinr": {"active": False, "direction": "NEUTRAL", "change_pct": 0},
                    "crude": {"active": False, "direction": "NEUTRAL", "change_pct": 0},
                    "gold": {"active": False, "direction": "NEUTRAL", "change_pct": 0},
                    "correlation_signal": False,
                    "direction": direction,
                    "active_signals": 0,
                    "proxy": True,
                    "proxy_source": f"VIX={vix:.1f}" if isinstance(vix, (int, float)) else "VIX N/A",
                }
            )

        usdinr_data = cross_assets.get("usdinr", {})
        crude_data = cross_assets.get("crude", {})
        gold_data = cross_assets.get("gold", {})

        usdinr = self._assess_usdinr(usdinr_data)
        crude = self._assess_crude(crude_data)
        gold = self._assess_gold(gold_data)

        signals = [usdinr, crude, gold]
        active_signals = [s for s in signals if s["active"]]
        active_count = len(active_signals)

        # Determine net direction from active signals
        bearish_count = sum(1 for s in active_signals if s["direction"] == "BEARISH")
        bullish_count = sum(1 for s in active_signals if s["direction"] == "BULLISH")

        if bearish_count > bullish_count and bearish_count >= 2:
            direction = "BEARISH"
        elif bullish_count > bearish_count and bullish_count >= 2:
            direction = "BULLISH"
        elif active_count >= 1:
            # Single signal: use its direction but lower confidence
            direction = active_signals[0]["direction"]
        else:
            direction = "NEUTRAL"

        confidence = 20 + active_count * 20
        if active_count >= 2 and (bearish_count >= 2 or bullish_count >= 2):
            confidence += 15  # Bonus for agreement

        verdict = "PASS" if active_count >= 2 else ("PARTIAL" if active_count == 1 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "usdinr": usdinr,
                "crude": crude,
                "gold": gold,
                "correlation_signal": active_count >= 2,
                "direction": direction,
                "active_signals": active_count,
            }
        )
