"""
E05 — GEX Wall Engine (Tier 2: Direction)
Computes Gamma Exposure (GEX) per strike using BS gamma.
Identifies call/put walls and GEX flip for regime detection.
"""

import math
import numpy as np
from .base import BaseEngine, EngineResult


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _bs_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes gamma: N'(d1) / (S * sigma * sqrt(T))"""
    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    return _norm_pdf(d1) / (S * sigma * math.sqrt(T))


class GEXWallEngine(BaseEngine):
    name = "GEX Wall"
    tier = 2
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._prev_total_gex = None

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", {})
        spot = ctx.get("prices", {}).get("spot", 0)
        r = 0.07
        dte = ctx.get("days_to_expiry", 7)
        T = max(dte / 365.0, 1 / 365.0)
        contract_size = ctx.get("lot_size", 50)  # Nifty lot

        if not chain or spot == 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain/spot"})

        strikes = sorted([int(s) for s in chain.keys() if str(s).isdigit()])
        if not strikes:
            return EngineResult(verdict="NEUTRAL", data={"error": "No strikes"})

        # Default IV estimate if not available per-strike
        default_sigma = ctx.get("atm_iv", 15) / 100.0
        if default_sigma <= 0:
            default_sigma = 0.15

        gex_by_strike = []
        total_gex = 0.0
        max_call_gex = 0.0
        max_put_gex = 0.0
        call_wall_strike = 0
        put_wall_strike = 0

        for s in strikes:
            entry = chain.get(s, chain.get(str(s), {}))
            if not isinstance(entry, dict):
                continue

            ce_oi = entry.get("ce_oi", entry.get("call_oi", 0)) or 0
            pe_oi = entry.get("pe_oi", entry.get("put_oi", 0)) or 0

            # Use per-strike IV if available, else default
            sigma = default_sigma
            ce_iv = entry.get("ce_iv", 0)
            pe_iv = entry.get("pe_iv", 0)
            if ce_iv and pe_iv:
                sigma = ((ce_iv + pe_iv) / 2) / 100.0
            elif ce_iv:
                sigma = ce_iv / 100.0
            elif pe_iv:
                sigma = pe_iv / 100.0
            sigma = max(sigma, 0.01)

            gamma = _bs_gamma(spot, s, T, r, sigma)

            # GEX = OI * gamma * S^2 * contract_size / 1e7
            # Call GEX is positive (dealers long gamma), Put GEX is negative
            call_gex = ce_oi * gamma * spot ** 2 * contract_size / 1e7
            put_gex = -pe_oi * gamma * spot ** 2 * contract_size / 1e7

            strike_gex = call_gex + put_gex
            total_gex += strike_gex

            gex_by_strike.append({
                "strike": s,
                "call_gex": round(call_gex, 2),
                "put_gex": round(put_gex, 2),
                "net_gex": round(strike_gex, 2),
            })

            if call_gex > max_call_gex:
                max_call_gex = call_gex
                call_wall_strike = s
            if put_gex < max_put_gex:
                max_put_gex = put_gex
                put_wall_strike = s

        # GEX flip detection
        flip_detected = False
        if self._prev_total_gex is not None:
            if (self._prev_total_gex > 0 and total_gex < 0) or \
               (self._prev_total_gex < 0 and total_gex > 0):
                flip_detected = True
        self._prev_total_gex = total_gex

        # Direction: bullish if spot above biggest GEX wall (call wall = resistance)
        direction = "NEUTRAL"
        confidence = 40

        if call_wall_strike > 0 and put_wall_strike > 0:
            if spot > call_wall_strike:
                direction = "BULLISH"
                confidence = 65
            elif spot < put_wall_strike:
                direction = "BEARISH"
                confidence = 65
            else:
                # Between walls
                dist_to_call = call_wall_strike - spot
                dist_to_put = spot - put_wall_strike
                if dist_to_call < dist_to_put:
                    direction = "BULLISH"
                    confidence = 50
                else:
                    direction = "BEARISH"
                    confidence = 50

        if flip_detected:
            confidence = min(confidence + 15, 90)

        verdict = "PASS" if direction != "NEUTRAL" else "PARTIAL"

        # Top 10 strikes by absolute GEX for frontend
        sorted_gex = sorted(gex_by_strike, key=lambda x: abs(x["net_gex"]), reverse=True)[:10]

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "gex_by_strike": sorted_gex,
                "call_wall": call_wall_strike,
                "put_wall": put_wall_strike,
                "call_wall_gex": round(max_call_gex, 2),
                "put_wall_gex": round(max_put_gex, 2),
                "total_gex": round(total_gex, 2),
                "flip_detected": flip_detected,
                "spot": spot,
            }
        )
