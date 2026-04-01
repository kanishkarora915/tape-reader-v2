"""
E03 — Market Structure Engine (Tier 1: Core Gate)
SMC-based structure analysis from 5-minute candles:
  - Swing highs/lows via 3-bar pivot
  - BOS (Break of Structure), CHoCH (Change of Character)
  - Order Block detection
  - Regime: UPTREND, DOWNTREND, RANGE, BOS, CHoCH
"""

import numpy as np
from .base import BaseEngine, EngineResult


class MarketStructureEngine(BaseEngine):
    name = "Market Structure"
    tier = 1
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._swing_highs = []  # (index, price)
        self._swing_lows = []   # (index, price)
        self._events = []       # recent structure events
        self._order_blocks = [] # detected order blocks

    def _find_pivots(self, highs: np.ndarray, lows: np.ndarray, lookback: int = 3):
        """Find 3-bar pivot swing highs and lows."""
        swing_highs = []
        swing_lows = []
        n = len(highs)

        for i in range(lookback, n - lookback):
            # Swing high: high[i] is highest in window
            if highs[i] == max(highs[i - lookback: i + lookback + 1]):
                swing_highs.append((i, float(highs[i])))
            # Swing low: low[i] is lowest in window
            if lows[i] == min(lows[i - lookback: i + lookback + 1]):
                swing_lows.append((i, float(lows[i])))

        return swing_highs, swing_lows

    def _detect_structure(self, swing_highs, swing_lows, closes):
        """Detect BOS, CHoCH, and determine regime."""
        events = []
        regime = "RANGE"

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return regime, events

        # Check for Higher Highs / Lower Lows pattern
        last_2_highs = swing_highs[-2:]
        last_2_lows = swing_lows[-2:]

        hh = last_2_highs[-1][1] > last_2_highs[-2][1]  # higher high
        hl = last_2_lows[-1][1] > last_2_lows[-2][1]     # higher low
        lh = last_2_highs[-1][1] < last_2_highs[-2][1]   # lower high
        ll = last_2_lows[-1][1] < last_2_lows[-2][1]     # lower low

        current_price = float(closes[-1]) if len(closes) > 0 else 0

        # Regime detection
        if hh and hl:
            regime = "UPTREND"
        elif lh and ll:
            regime = "DOWNTREND"
        else:
            regime = "RANGE"

        # BOS: Break of Structure
        # Bullish BOS: current price breaks above last swing high
        prev_high = last_2_highs[-1][1]
        prev_low = last_2_lows[-1][1]

        if current_price > prev_high and regime != "DOWNTREND":
            events.append({
                "type": "BOS",
                "direction": "BULLISH",
                "level": prev_high,
                "candle_idx": len(closes) - 1,
            })
            regime = "BOS"

        # Bearish BOS: current price breaks below last swing low
        if current_price < prev_low and regime != "UPTREND":
            events.append({
                "type": "BOS",
                "direction": "BEARISH",
                "level": prev_low,
                "candle_idx": len(closes) - 1,
            })
            regime = "BOS"

        # CHoCH: first opposite break in established trend
        if len(swing_highs) >= 3 and len(swing_lows) >= 3:
            prev_3_highs = [h[1] for h in swing_highs[-3:]]
            prev_3_lows = [l[1] for l in swing_lows[-3:]]

            # Was in uptrend (HH, HL) but now made LL = CHoCH bearish
            if (prev_3_highs[-3] < prev_3_highs[-2] and  # was making HH
                    prev_3_lows[-3] < prev_3_lows[-2] and    # was making HL
                    prev_3_lows[-1] < prev_3_lows[-2]):       # now made LL
                events.append({
                    "type": "CHoCH",
                    "direction": "BEARISH",
                    "level": prev_3_lows[-2],
                    "candle_idx": swing_lows[-1][0],
                })
                regime = "CHoCH"

            # Was in downtrend (LH, LL) but now made HH = CHoCH bullish
            if (prev_3_highs[-3] > prev_3_highs[-2] and  # was making LH
                    prev_3_lows[-3] > prev_3_lows[-2] and    # was making LL
                    prev_3_highs[-1] > prev_3_highs[-2]):     # now made HH
                events.append({
                    "type": "CHoCH",
                    "direction": "BULLISH",
                    "level": prev_3_highs[-2],
                    "candle_idx": swing_highs[-1][0],
                })
                regime = "CHoCH"

        return regime, events

    def _detect_order_blocks(self, candles, swing_highs, swing_lows):
        """Detect order blocks: last opposing candle before impulse move."""
        order_blocks = []
        opens = candles.get("open", [])
        closes = candles.get("close", [])
        highs = candles.get("high", [])
        lows = candles.get("low", [])

        if len(opens) < 5:
            return order_blocks

        # Bullish OB: last bearish candle before a strong bullish impulse
        for i in range(2, min(len(opens) - 2, 50)):
            idx = len(opens) - 1 - i
            if idx < 1:
                break
            # Bearish candle followed by strong bullish move
            if (closes[idx] < opens[idx] and           # bearish candle
                    closes[idx + 1] > opens[idx + 1] and   # next is bullish
                    (closes[idx + 1] - opens[idx + 1]) > 1.5 * abs(closes[idx] - opens[idx])):  # impulse
                order_blocks.append({
                    "type": "BULLISH_OB",
                    "high": float(highs[idx]),
                    "low": float(lows[idx]),
                    "candle_idx": idx,
                })
                if len(order_blocks) >= 3:
                    break

        # Bearish OB: last bullish candle before strong bearish impulse
        for i in range(2, min(len(opens) - 2, 50)):
            idx = len(opens) - 1 - i
            if idx < 1:
                break
            if (closes[idx] > opens[idx] and           # bullish candle
                    closes[idx + 1] < opens[idx + 1] and   # next is bearish
                    (opens[idx + 1] - closes[idx + 1]) > 1.5 * abs(closes[idx] - opens[idx])):
                order_blocks.append({
                    "type": "BEARISH_OB",
                    "high": float(highs[idx]),
                    "low": float(lows[idx]),
                    "candle_idx": idx,
                })
                if len(order_blocks) >= 6:
                    break

        return order_blocks

    def compute(self, ctx: dict) -> EngineResult:
        candles = ctx.get("candles", {})
        highs_list = candles.get("high", [])
        lows_list = candles.get("low", [])
        closes_list = candles.get("close", [])

        if len(closes_list) < 10:
            return EngineResult(verdict="NEUTRAL", confidence=10,
                                data={"error": "Need at least 10 candles"})

        highs = np.array(highs_list, dtype=float)
        lows = np.array(lows_list, dtype=float)
        closes = np.array(closes_list, dtype=float)

        # Find pivots
        swing_highs, swing_lows = self._find_pivots(highs, lows, lookback=3)
        self._swing_highs = swing_highs
        self._swing_lows = swing_lows

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return EngineResult(verdict="PARTIAL", confidence=20,
                                data={"regime": "FORMING", "note": "Not enough swings"})

        # Detect structure
        regime, events = self._detect_structure(swing_highs, swing_lows, closes)
        self._events = events

        # Detect order blocks
        order_blocks = self._detect_order_blocks(candles, swing_highs, swing_lows)
        self._order_blocks = order_blocks

        # Support and resistance from swings
        support = swing_lows[-1][1] if swing_lows else 0
        resistance = swing_highs[-1][1] if swing_highs else 0

        # Direction and verdict
        direction = "NEUTRAL"
        verdict = "PARTIAL"
        confidence = 40

        if regime == "UPTREND":
            direction = "BULLISH"
            verdict = "PASS"
            confidence = 70
        elif regime == "DOWNTREND":
            direction = "BEARISH"
            verdict = "PASS"
            confidence = 70
        elif regime == "BOS":
            bos_dir = events[-1]["direction"] if events else "NEUTRAL"
            direction = bos_dir
            verdict = "PASS"
            confidence = 80
        elif regime == "CHoCH":
            choch_dir = events[-1]["direction"] if events else "NEUTRAL"
            direction = choch_dir
            verdict = "PASS"
            confidence = 85

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=confidence,
            data={
                "regime": regime,
                "support": round(support, 2),
                "resistance": round(resistance, 2),
                "order_blocks": order_blocks[:4],
                "recent_events": events[-5:],
                "swing_highs": [(i, round(p, 2)) for i, p in swing_highs[-5:]],
                "swing_lows": [(i, round(p, 2)) for i, p in swing_lows[-5:]],
            }
        )
