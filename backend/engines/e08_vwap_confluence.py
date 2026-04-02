"""
E08 — VWAP Confluence Engine (Tier 2: Direction)
Computes Daily VWAP and Weekly VWAP with standard deviation bands.
Direction: BULLISH if price > both VWAPs, BEARISH if below both.
"""

import numpy as np
from .base import BaseEngine, EngineResult


class VWAPConfluenceEngine(BaseEngine):
    name = "VWAP Confluence"
    tier = 2
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        # Intraday accumulators for D-VWAP
        self._d_cum_pv = 0.0    # cumulative price * volume
        self._d_cum_vol = 0.0   # cumulative volume
        self._d_cum_pv2 = 0.0   # for std dev: cumulative price^2 * volume
        self._tick_count = 0
        # Weekly VWAP from daily data
        self._w_vwap = 0.0
        self._w_computed = False

    def _compute_weekly_vwap(self, daily_candles: list) -> float:
        """Compute weekly VWAP from last 5 days of daily OHLCV data."""
        if not daily_candles or len(daily_candles) < 1:
            return 0.0

        cum_pv = 0.0
        cum_vol = 0.0
        for candle in daily_candles[-5:]:
            # Typical price = (H + L + C) / 3
            h = candle.get("high", 0)
            l = candle.get("low", 0)
            c = candle.get("close", 0)
            v = candle.get("volume", 0)
            if v > 0 and c > 0:
                tp = (h + l + c) / 3.0
                cum_pv += tp * v
                cum_vol += v

        return cum_pv / cum_vol if cum_vol > 0 else 0.0

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        prices = ctx.get("prices", {})
        spot = prices.get("spot", 0)
        daily_candles = ctx.get("daily_candles", [])

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])
        volumes = candles.get("volume", [])

        if spot == 0:
            spot = ctx.get("nifty_spot", 0) or ctx.get("prices", {}).get("spot", 0)
        if spot == 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No price data"})

        if not closes:
            # Fallback: estimate VWAP from spot tick data
            nifty_high = ctx.get("nifty_high", spot)
            nifty_low = ctx.get("nifty_low", spot)
            est_vwap = round((nifty_high + nifty_low + spot) / 3, 2)
            direction = "BULLISH" if spot > est_vwap else "BEARISH"
            return EngineResult(
                verdict="PARTIAL",
                direction=direction,
                confidence=35,
                data={
                    "d_vwap": est_vwap,
                    "w_vwap": est_vwap,
                    "sd1_upper": round(est_vwap + (nifty_high - nifty_low) * 0.5, 2),
                    "sd1_lower": round(est_vwap - (nifty_high - nifty_low) * 0.5, 2),
                    "sd2_upper": round(est_vwap + (nifty_high - nifty_low), 2),
                    "sd2_lower": round(est_vwap - (nifty_high - nifty_low), 2),
                    "std_dev": 0,
                    "position": "ESTIMATED",
                    "spot": spot,
                    "note": "Estimated from tick data, no candles yet",
                }
            )

        # --- D-VWAP from intraday candles ---
        if len(closes) > 0 and len(volumes) > 0:
            n = min(len(highs), len(lows), len(closes), len(volumes))
            cum_pv = 0.0
            cum_vol = 0.0
            cum_pv2 = 0.0

            for i in range(n):
                h = highs[i] if i < len(highs) else closes[i]
                l = lows[i] if i < len(lows) else closes[i]
                c = closes[i]
                v = volumes[i] if volumes[i] > 0 else 1

                tp = (h + l + c) / 3.0
                cum_pv += tp * v
                cum_vol += v
                cum_pv2 += tp * tp * v

            d_vwap = cum_pv / cum_vol if cum_vol > 0 else spot

            # Standard deviation for bands
            if cum_vol > 0:
                variance = (cum_pv2 / cum_vol) - (d_vwap ** 2)
                std_dev = max(0, variance) ** 0.5
            else:
                std_dev = 0

            sd1_upper = d_vwap + std_dev
            sd1_lower = d_vwap - std_dev
            sd2_upper = d_vwap + 2 * std_dev
            sd2_lower = d_vwap - 2 * std_dev
        else:
            d_vwap = spot
            std_dev = 0
            sd1_upper = sd1_lower = sd2_upper = sd2_lower = spot

        # --- W-VWAP from daily candles ---
        if daily_candles and not self._w_computed:
            self._w_vwap = self._compute_weekly_vwap(daily_candles)
            self._w_computed = True
        elif not daily_candles and not self._w_computed:
            # Approximate from intraday if no daily data
            self._w_vwap = d_vwap  # fallback

        w_vwap = self._w_vwap if self._w_vwap > 0 else d_vwap

        # --- Direction ---
        above_d_vwap = spot > d_vwap
        above_w_vwap = spot > w_vwap

        if above_d_vwap and above_w_vwap:
            direction = "BULLISH"
            position = "ABOVE_BOTH"
            confidence = 70
        elif not above_d_vwap and not above_w_vwap:
            direction = "BEARISH"
            position = "BELOW_BOTH"
            confidence = 70
        elif above_d_vwap and not above_w_vwap:
            direction = "BULLISH"
            position = "ABOVE_DVWAP_BELOW_WVWAP"
            confidence = 50
        else:
            direction = "BEARISH"
            position = "BELOW_DVWAP_ABOVE_WVWAP"
            confidence = 50

        # Boost if at SD2 extremes (mean reversion zone)
        if spot >= sd2_upper:
            direction = "BEARISH"  # overextended, expect reversion
            position = "SD2_UPPER"
            confidence = 60
        elif spot <= sd2_lower:
            direction = "BULLISH"  # oversold, expect bounce
            position = "SD2_LOWER"
            confidence = 60

        verdict = "PASS" if direction != "NEUTRAL" else "PARTIAL"

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "d_vwap": round(d_vwap, 2),
                "w_vwap": round(w_vwap, 2),
                "sd1_upper": round(sd1_upper, 2),
                "sd1_lower": round(sd1_lower, 2),
                "sd2_upper": round(sd2_upper, 2),
                "sd2_lower": round(sd2_lower, 2),
                "std_dev": round(std_dev, 2),
                "position": position,
                "spot": spot,
            }
        )
