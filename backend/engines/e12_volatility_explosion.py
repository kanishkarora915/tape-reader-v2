"""
E12 — Volatility Explosion Engine (Tier 3: Amplifier)
Detects impending volatility expansion via 4 sub-detectors:
  1. VIX spike: VIX change > 5% intraday
  2. Bollinger Band squeeze: bandwidth at 20-period low
  3. IV expansion: ATM IV rising > 2 std from mean
  4. ATR ratio: current ATR / 20-day avg ATR < 0.3 = compression
Fires if any 2 of the 4 are active.
"""

import numpy as np
from .base import BaseEngine, EngineResult


class VolatilityExplosionEngine(BaseEngine):
    name = "Volatility Explosion"
    tier = 3
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._iv_history = []     # rolling ATM IV for std dev computation
        self._max_iv_history = 240

    def _detect_vix_spike(self, ctx: dict) -> dict:
        """VIX intraday change > 5%."""
        vix = ctx.get("vix", {})
        current_vix = vix.get("current", 0)
        open_vix = vix.get("open", 0) or vix.get("prev_close", 0)

        if open_vix <= 0 or current_vix <= 0:
            return {"active": False, "change_pct": 0, "current": current_vix}

        change_pct = ((current_vix - open_vix) / open_vix) * 100
        return {
            "active": abs(change_pct) > 5,
            "change_pct": round(change_pct, 2),
            "current": current_vix,
        }

    def _detect_bb_squeeze(self, closes: np.ndarray, period: int = 20) -> dict:
        """Bollinger Band squeeze: bandwidth at 20-period low."""
        if len(closes) < period + 20:
            return {"active": False, "bandwidth": 0, "note": "Insufficient data"}

        # Compute BB bandwidth for last 20 periods
        bandwidths = []
        for i in range(20):
            idx = len(closes) - 20 + i
            if idx < period:
                continue
            window = closes[idx - period:idx]
            sma = np.mean(window)
            std = np.std(window)
            if sma > 0:
                bw = (2 * 2 * std) / sma * 100  # 2-std BB width as % of SMA
                bandwidths.append(bw)

        if len(bandwidths) < 5:
            return {"active": False, "bandwidth": 0}

        current_bw = bandwidths[-1]
        min_bw = min(bandwidths)

        return {
            "active": current_bw <= min_bw * 1.05,  # within 5% of period low
            "bandwidth": round(current_bw, 3),
            "min_bandwidth": round(min_bw, 3),
        }

    def _detect_iv_expansion(self, ctx: dict) -> dict:
        """ATM IV rising > 2 std from rolling mean."""
        prev_results = ctx.get("previous_results", {})
        e02 = prev_results.get("e02", {})
        atm_iv = e02.get("data", {}).get("atm_iv", 0) if isinstance(e02, dict) else 0

        # If e02 result is an EngineResult-like state dict
        if hasattr(e02, "data"):
            atm_iv = e02.data.get("atm_iv", 0)

        if atm_iv <= 0:
            return {"active": False, "atm_iv": 0}

        self._iv_history.append(atm_iv)
        if len(self._iv_history) > self._max_iv_history:
            self._iv_history.pop(0)

        if len(self._iv_history) < 20:
            return {"active": False, "atm_iv": atm_iv, "note": "Building IV history"}

        iv_arr = np.array(self._iv_history)
        iv_mean = np.mean(iv_arr)
        iv_std = np.std(iv_arr)

        if iv_std <= 0:
            return {"active": False, "atm_iv": atm_iv}

        z_score = (atm_iv - iv_mean) / iv_std

        return {
            "active": z_score > 2.0,
            "atm_iv": round(atm_iv, 2),
            "iv_mean": round(iv_mean, 2),
            "iv_std": round(iv_std, 2),
            "z_score": round(z_score, 2),
        }

    def _detect_atr_compression(self, highs: np.ndarray, lows: np.ndarray,
                                 closes: np.ndarray, period: int = 20) -> dict:
        """ATR ratio: current ATR / 20-day avg ATR. < 0.3 = compression."""
        n = len(closes)
        if n < period + 5:
            return {"active": False, "atr_ratio": 0}

        # True Range
        tr = np.zeros(n)
        tr[0] = highs[0] - lows[0]
        for i in range(1, n):
            tr[i] = max(highs[i] - lows[i],
                        abs(highs[i] - closes[i - 1]),
                        abs(lows[i] - closes[i - 1]))

        # Current ATR (last 5 bars) vs average ATR (last 20 bars)
        current_atr = np.mean(tr[-5:])
        avg_atr = np.mean(tr[-period:])

        atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0

        return {
            "active": atr_ratio < 0.3,
            "atr_ratio": round(atr_ratio, 3),
            "current_atr": round(current_atr, 2),
            "avg_atr": round(avg_atr, 2),
        }

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        closes_list = candles.get("close", [])
        highs_list = candles.get("high", [])
        lows_list = candles.get("low", [])

        # Sub-detector 1: VIX spike
        vix_result = self._detect_vix_spike(ctx)

        # Sub-detector 2: BB squeeze
        if len(closes_list) >= 40:
            closes = np.array(closes_list, dtype=float)
            bb_result = self._detect_bb_squeeze(closes)
        else:
            bb_result = {"active": False, "note": "Need 40+ candles"}

        # Sub-detector 3: IV expansion
        iv_result = self._detect_iv_expansion(ctx)

        # Sub-detector 4: ATR compression
        if len(closes_list) >= 25:
            highs = np.array(highs_list, dtype=float)
            lows = np.array(lows_list, dtype=float)
            closes = np.array(closes_list, dtype=float)
            atr_result = self._detect_atr_compression(highs, lows, closes)
        else:
            atr_result = {"active": False, "note": "Need 25+ candles"}

        # Count active sub-signals
        sub_signals = {
            "vix_spike": vix_result,
            "bb_squeeze": bb_result,
            "iv_expanding": iv_result,
            "atr_compression": atr_result,
        }
        active_count = sum(1 for s in sub_signals.values() if s.get("active", False))

        # Fires if 2+ sub-detectors active
        volatile_mode = active_count >= 2
        verdict = "PASS" if volatile_mode else ("PARTIAL" if active_count == 1 else "NEUTRAL")
        direction = "NEUTRAL"  # Amplifier, not directional
        confidence = 20 + active_count * 20

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "vix_spike": vix_result,
                "bb_squeeze": bb_result,
                "iv_expanding": iv_result,
                "atr_ratio": atr_result,
                "volatile_mode": volatile_mode,
                "active_sub_signals": active_count,
                "sub_signals": {k: v.get("active", False) for k, v in sub_signals.items()},
            }
        )
