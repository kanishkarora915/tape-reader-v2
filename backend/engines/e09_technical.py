"""
E09 — Technical Engine (Tier 2: Direction)
Computes EMA(20/50), RSI(14), MACD(12,26,9), Supertrend(10,3) from 5-min candles.
Direction requires 3 of 4 indicators to agree.
"""

import numpy as np
from .base import BaseEngine, EngineResult


def _ema(data: np.ndarray, period: int) -> np.ndarray:
    """Exponential Moving Average."""
    result = np.full_like(data, np.nan, dtype=float)
    if len(data) < period:
        return result
    alpha = 2.0 / (period + 1)
    result[period - 1] = np.mean(data[:period])
    for i in range(period, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    return result


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    """RSI using exponential smoothing."""
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                period: int = 10, multiplier: float = 3.0):
    """Supertrend indicator. Returns (supertrend_line, direction)."""
    n = len(closes)
    if n < period + 1:
        return None, None

    # ATR
    tr = np.zeros(n)
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i],
                     abs(highs[i] - closes[i - 1]),
                     abs(lows[i] - closes[i - 1]))
    tr[0] = highs[0] - lows[0]

    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    # Supertrend
    hl2 = (highs + lows) / 2.0
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr
    st = np.zeros(n)
    st_dir = np.zeros(n)  # 1 = bullish, -1 = bearish

    st[period - 1] = upper_band[period - 1]
    st_dir[period - 1] = -1

    for i in range(period, n):
        if closes[i] > upper_band[i - 1]:
            st_dir[i] = 1
        elif closes[i] < lower_band[i - 1]:
            st_dir[i] = -1
        else:
            st_dir[i] = st_dir[i - 1]

        if st_dir[i] == 1:
            st[i] = max(lower_band[i], st[i - 1]) if st_dir[i - 1] == 1 else lower_band[i]
        else:
            st[i] = min(upper_band[i], st[i - 1]) if st_dir[i - 1] == -1 else upper_band[i]

    return float(st[-1]), int(st_dir[-1])


class TechnicalEngine(BaseEngine):
    name = "Technical"
    tier = 2
    refresh_seconds = 5

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        closes_list = candles.get("close", [])
        highs_list = candles.get("high", [])
        lows_list = candles.get("low", [])

        if len(closes_list) < 50:
            return EngineResult(verdict="NEUTRAL", confidence=10,
                                data={"error": f"Need 50 candles, have {len(closes_list)}"})

        closes = np.array(closes_list, dtype=float)
        highs = np.array(highs_list, dtype=float)
        lows = np.array(lows_list, dtype=float)
        spot = float(closes[-1])

        # --- EMA(20) and EMA(50) ---
        ema20_arr = _ema(closes, 20)
        ema50_arr = _ema(closes, 50)
        ema_20 = float(ema20_arr[-1]) if not np.isnan(ema20_arr[-1]) else spot
        ema_50 = float(ema50_arr[-1]) if not np.isnan(ema50_arr[-1]) else spot

        ema_bullish = ema_20 > ema_50 and spot > ema_20

        # --- RSI(14) ---
        rsi_val = _rsi(closes, 14)
        rsi_bullish = rsi_val > 55
        rsi_bearish = rsi_val < 45

        # --- MACD(12,26,9) ---
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)

        macd_line = np.zeros(len(closes))
        for i in range(len(closes)):
            if not np.isnan(ema12[i]) and not np.isnan(ema26[i]):
                macd_line[i] = ema12[i] - ema26[i]

        signal_line = _ema(macd_line, 9)
        macd_val = float(macd_line[-1])
        signal_val = float(signal_line[-1]) if not np.isnan(signal_line[-1]) else 0
        histogram = macd_val - signal_val
        macd_bullish = macd_val > signal_val and histogram > 0

        # --- Supertrend(10, 3) ---
        st_line, st_dir = _supertrend(highs, lows, closes, period=10, multiplier=3.0)
        st_bullish = st_dir == 1 if st_dir is not None else False

        # --- Vote counting ---
        votes = {
            "ema": "BULLISH" if ema_bullish else ("BEARISH" if (ema_20 < ema_50 and spot < ema_20) else "NEUTRAL"),
            "rsi": "BULLISH" if rsi_bullish else ("BEARISH" if rsi_bearish else "NEUTRAL"),
            "macd": "BULLISH" if macd_bullish else ("BEARISH" if (macd_val < signal_val and histogram < 0) else "NEUTRAL"),
            "supertrend": "BULLISH" if st_bullish else ("BEARISH" if st_dir == -1 else "NEUTRAL"),
        }

        bull_votes = sum(1 for v in votes.values() if v == "BULLISH")
        bear_votes = sum(1 for v in votes.values() if v == "BEARISH")

        # 3 of 4 must agree
        if bull_votes >= 3:
            direction = "BULLISH"
            verdict = "PASS"
            confidence = 60 + bull_votes * 8
        elif bear_votes >= 3:
            direction = "BEARISH"
            verdict = "PASS"
            confidence = 60 + bear_votes * 8
        else:
            direction = "NEUTRAL"
            verdict = "PARTIAL"
            confidence = 30

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 92),
            data={
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "rsi": round(rsi_val, 2),
                "macd": round(macd_val, 2),
                "macd_signal": round(signal_val, 2),
                "macd_histogram": round(histogram, 2),
                "supertrend": round(st_line, 2) if st_line else 0,
                "supertrend_dir": st_dir,
                "votes": votes,
                "bull_votes": bull_votes,
                "bear_votes": bear_votes,
                "direction": direction,
            }
        )
