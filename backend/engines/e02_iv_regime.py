"""
E02 — IV Regime Engine (Tier 1: Core Gate)
Computes ATM IV via Black-Scholes Newton-Raphson, IVR, IV Skew.
Gates the system: IVR < 50 = OPEN, 50-70 = PARTIAL, > 70 = BLOCKED.
"""

import math
import numpy as np
from .base import BaseEngine, EngineResult


def _norm_cdf(x: float) -> float:
    """Standard normal CDF using error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _bs_price(S: float, K: float, T: float, r: float, sigma: float, is_call: bool) -> float:
    """Black-Scholes option price."""
    if T <= 0 or sigma <= 0:
        return max(0, (S - K) if is_call else (K - S))
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if is_call:
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def _bs_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes vega."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    return S * _norm_pdf(d1) * math.sqrt(T)


def implied_vol(market_price: float, S: float, K: float, T: float, r: float,
                is_call: bool, tol: float = 1e-5, max_iter: int = 50) -> float:
    """Newton-Raphson implied volatility solver."""
    if market_price <= 0 or T <= 0:
        return 0.0
    intrinsic = max(0, (S - K) if is_call else (K - S))
    if market_price < intrinsic:
        return 0.0

    sigma = 0.25  # initial guess
    for _ in range(max_iter):
        price = _bs_price(S, K, T, r, sigma, is_call)
        vega = _bs_vega(S, K, T, r, sigma)
        if vega < 1e-10:
            break
        diff = price - market_price
        sigma -= diff / vega
        sigma = max(0.01, min(sigma, 5.0))  # clamp
        if abs(diff) < tol:
            break
    return sigma


class IVRegimeEngine(BaseEngine):
    name = "IV Regime"
    tier = 1
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._iv_history = []    # rolling IV values for IVR computation
        self._max_history = 240  # ~20 min of data at 5s

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", {})
        spot = ctx.get("prices", {}).get("spot", 0)
        r = 0.07  # risk-free rate (India ~7%)

        if not chain or spot == 0:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain/spot data"})

        # Determine ATM
        strikes = sorted([int(s) for s in chain.keys() if str(s).isdigit()])
        if not strikes:
            return EngineResult(verdict="NEUTRAL", data={"error": "No strikes"})

        atm = min(strikes, key=lambda s: abs(s - spot))
        entry = chain.get(atm, chain.get(str(atm), {}))
        if not isinstance(entry, dict):
            return EngineResult(verdict="NEUTRAL", data={"error": "Bad chain entry"})

        # Get premiums and time to expiry
        ce_price = entry.get("ce_ltp", entry.get("call_ltp", 0)) or 0
        pe_price = entry.get("pe_ltp", entry.get("put_ltp", 0)) or 0
        dte = ctx.get("days_to_expiry", 7)
        T = max(dte / 365.0, 1 / 365.0)  # at least 1 day

        # Compute ATM implied vol
        ce_iv = implied_vol(ce_price, spot, atm, T, r, is_call=True)
        pe_iv = implied_vol(pe_price, spot, atm, T, r, is_call=False)
        atm_iv = (ce_iv + pe_iv) / 2.0 if (ce_iv > 0 and pe_iv > 0) else max(ce_iv, pe_iv)

        if atm_iv <= 0:
            return EngineResult(verdict="NEUTRAL", confidence=10,
                                data={"error": "Could not compute IV", "atm": atm})

        atm_iv_pct = atm_iv * 100  # as percentage

        # Track IV history for rolling IVR
        self._iv_history.append(atm_iv_pct)
        if len(self._iv_history) > self._max_history:
            self._iv_history.pop(0)

        # IVR: use 52-week data if available, else rolling window
        iv_52w_high = ctx.get("iv_52w_high", 0)
        iv_52w_low = ctx.get("iv_52w_low", 0)

        if iv_52w_high > iv_52w_low > 0:
            ivr = ((atm_iv_pct - iv_52w_low) / (iv_52w_high - iv_52w_low)) * 100
        elif len(self._iv_history) >= 20:
            rolling_high = max(self._iv_history[-240:])
            rolling_low = min(self._iv_history[-240:])
            iv_range = rolling_high - rolling_low
            ivr = ((atm_iv_pct - rolling_low) / iv_range * 100) if iv_range > 0 else 50
        else:
            ivr = 50  # default mid

        ivr = max(0, min(100, ivr))

        # Gate logic
        if ivr < 50:
            gate_status = "OPEN"
            verdict = "PASS"
            confidence = 70 + int((50 - ivr) * 0.6)
        elif ivr <= 70:
            gate_status = "PARTIAL"
            verdict = "PARTIAL"
            confidence = 50
        else:
            gate_status = "BLOCKED"
            verdict = "FAIL"
            confidence = 30 + int((ivr - 70) * 0.5)

        confidence = min(confidence, 95)

        # IV Skew
        skew = round((ce_iv - pe_iv) * 100, 2) if (ce_iv > 0 and pe_iv > 0) else 0
        # Positive skew = calls more expensive (fear of upside / hedging)
        # Negative skew = puts more expensive (downside fear)

        direction = "NEUTRAL"
        if skew > 2:
            direction = "BEARISH"  # call IV elevated, writers demanding more
        elif skew < -2:
            direction = "BULLISH"  # put IV elevated, contrarian

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "ivr": round(ivr, 1),
                "atm_iv": round(atm_iv_pct, 2),
                "ce_iv": round(ce_iv * 100, 2),
                "pe_iv": round(pe_iv * 100, 2),
                "gate_status": gate_status,
                "skew": skew,
                "atm_strike": atm,
            }
        )
