"""
E11 — FII/DII Engine (Tier 2: Direction)
Tracks FII/DII net futures positions from DB (fetched daily by separate job).
3-day trend of FII net futures determines direction.
"""

from .base import BaseEngine, EngineResult


class FIIDIIEngine(BaseEngine):
    name = "FII/DII Flow"
    tier = 2
    refresh_seconds = 60  # daily data, no need for fast refresh

    def compute(self, ctx: dict) -> EngineResult:
        fii_dii = ctx.get("fii_dii", {})

        if not fii_dii:
            # Fallback: use spot price direction as proxy for institutional flow
            prices = ctx.get("prices", {})
            change_pct = prices.get("change_pct", 0)
            spot = prices.get("spot", 0)
            vix = ctx.get("vix", 0)

            if isinstance(change_pct, (int, float)) and abs(change_pct) > 0.1:
                direction = "BULLISH" if change_pct > 0 else "BEARISH"
                # Stronger move = higher confidence proxy
                conf = min(55, 30 + int(abs(change_pct) * 10))
                verdict = "PARTIAL"
            else:
                direction = "NEUTRAL"
                conf = 15
                verdict = "NEUTRAL"

            return EngineResult(
                verdict=verdict, direction=direction, confidence=conf,
                data={
                    "fii_net_fut": 0, "dii_net_fut": 0,
                    "fii_3day_trend": "PROXY",
                    "fii_opt_net": 0, "fii_history": [],
                    "direction": direction,
                    "proxy": True,
                    "proxy_source": f"Spot {change_pct:+.2f}%",
                }
            )

        # Current day data
        fii_net_fut = fii_dii.get("fii_net_fut", 0)  # FII net futures (long - short)
        dii_net_fut = fii_dii.get("dii_net_fut", 0)
        fii_opt_net = fii_dii.get("fii_opt_net", 0)  # FII net options

        # 3-day history: list of daily FII net futures values [day-3, day-2, day-1]
        fii_history = fii_dii.get("fii_net_fut_history", [])

        # Compute 3-day trend
        fii_3day_trend = "FLAT"
        direction = "NEUTRAL"
        confidence = 30
        verdict = "PARTIAL"

        if len(fii_history) >= 3:
            recent = fii_history[-3:]
            # Check monotonic trend
            increasing = all(recent[i] < recent[i + 1] for i in range(len(recent) - 1))
            decreasing = all(recent[i] > recent[i + 1] for i in range(len(recent) - 1))

            if increasing:
                fii_3day_trend = "INCREASING"
            elif decreasing:
                fii_3day_trend = "DECREASING"
            else:
                # Check net direction
                net_change = recent[-1] - recent[0]
                if net_change > 0:
                    fii_3day_trend = "NET_POSITIVE"
                elif net_change < 0:
                    fii_3day_trend = "NET_NEGATIVE"
                else:
                    fii_3day_trend = "FLAT"

        elif len(fii_history) >= 2:
            if fii_history[-1] > fii_history[-2]:
                fii_3day_trend = "INCREASING"
            elif fii_history[-1] < fii_history[-2]:
                fii_3day_trend = "DECREASING"

        # Direction logic
        # FII net long increasing = institutional buying = BULLISH
        if fii_3day_trend in ("INCREASING", "NET_POSITIVE"):
            direction = "BULLISH"
            confidence = 60
            verdict = "PASS"
        elif fii_3day_trend in ("DECREASING", "NET_NEGATIVE"):
            direction = "BEARISH"
            confidence = 60
            verdict = "PASS"

        # Boost if current day data confirms trend
        if fii_net_fut > 0 and direction == "BULLISH":
            confidence = min(confidence + 10, 80)
        elif fii_net_fut < 0 and direction == "BEARISH":
            confidence = min(confidence + 10, 80)
        elif fii_net_fut > 0 and direction == "BEARISH":
            confidence = max(confidence - 10, 25)  # conflicting signal
        elif fii_net_fut < 0 and direction == "BULLISH":
            confidence = max(confidence - 10, 25)

        # If no trend but current day has strong position
        if direction == "NEUTRAL" and abs(fii_net_fut) > 0:
            if fii_net_fut > 5000:  # large net long (in crores)
                direction = "BULLISH"
                confidence = 50
                verdict = "PASS"
            elif fii_net_fut < -5000:
                direction = "BEARISH"
                confidence = 50
                verdict = "PASS"

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "fii_net_fut": fii_net_fut,
                "dii_net_fut": dii_net_fut,
                "fii_3day_trend": fii_3day_trend,
                "fii_opt_net": fii_opt_net,
                "fii_history": fii_history[-5:] if fii_history else [],
                "direction": direction,
            }
        )
