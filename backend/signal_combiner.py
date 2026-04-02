"""
BuyBy Trading System — 4-Tier Signal Combiner
Combines 24 engine outputs into actionable trade signals.
NO gates, NO time restrictions — always produces signals based on engine votes.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("buyby.combiner")

T1_GATES = ["e01", "e02", "e03", "e04"]
T2_DIRECTION = ["e05", "e06", "e07", "e08", "e09", "e10", "e11"]
T3_AMPLIFIERS = ["e12", "e13", "e14", "e15", "e16", "e17", "e18"]
T4_BIG_MOVE = ["e19", "e20", "e21", "e22", "e23"]


class SignalCombiner:

    def combine(self, engine_results: dict) -> dict:
        reasoning = []
        engine_verdicts = {}

        for eid, result in engine_results.items():
            engine_verdicts[eid] = {
                "verdict": result.get("verdict", "NEUTRAL"),
                "direction": result.get("direction", "NEUTRAL"),
                "confidence": result.get("confidence", 0),
                "name": result.get("name", eid),
            }

        # ── T1: Info only (no blocking) ──
        t1_status = []
        for eid in T1_GATES:
            result = engine_results.get(eid, {})
            v = result.get("verdict", "NEUTRAL")
            name = result.get("name", eid)
            t1_status.append(f"{name}: {v}")
        reasoning.append(f"T1 STATUS: {', '.join(t1_status)}")

        # ── T2: Direction votes ──
        bullish = 0
        bearish = 0
        for eid in T2_DIRECTION:
            result = engine_results.get(eid, {})
            d = result.get("direction", "NEUTRAL")
            if d == "BULLISH":
                bullish += 1
            elif d == "BEARISH":
                bearish += 1

        # Also count direction from T1 engines
        for eid in T1_GATES:
            result = engine_results.get(eid, {})
            d = result.get("direction", "NEUTRAL")
            if d == "BULLISH":
                bullish += 1
            elif d == "BEARISH":
                bearish += 1

        reasoning.append(f"DIRECTION VOTES: CALL={bullish} PUT={bearish}")

        # Determine direction — majority wins, no minimum threshold
        if bullish > bearish:
            t2_direction = "BULLISH"
        elif bearish > bullish:
            t2_direction = "BEARISH"
        elif bullish == bearish and bullish > 0:
            # Tie — use VIX and price momentum to break
            # Check E12 (volatility) and E03 (structure) for tiebreaker
            e03_dir = engine_results.get("e03", {}).get("direction", "NEUTRAL")
            if e03_dir != "NEUTRAL":
                t2_direction = e03_dir
                reasoning.append(f"TIE BROKEN by Market Structure: {e03_dir}")
            else:
                t2_direction = "BEARISH"  # Default bearish on tie (safer)
                reasoning.append("TIE — defaulting BEARISH (conservative)")
        else:
            t2_direction = "NEUTRAL"

        reasoning.append(f"FINAL DIRECTION: {t2_direction}")

        # ── T3: Amplifiers ──
        amp_count = 0
        for eid in T3_AMPLIFIERS:
            result = engine_results.get(eid, {})
            if result.get("verdict") in ("PASS", "PARTIAL"):
                amp_count += 1
        reasoning.append(f"AMPLIFIERS: {amp_count}/7 active")

        # ── T4: Big Move ──
        big_move = False
        big_move_engines = []
        for eid in T4_BIG_MOVE:
            result = engine_results.get(eid, {})
            if result.get("verdict") in ("PASS", "PARTIAL"):
                big_move = True
                big_move_engines.append(eid)
        if big_move:
            reasoning.append(f"BIG MOVE: {', '.join(big_move_engines)}")

        # ── Mode ──
        e12_pass = engine_results.get("e12", {}).get("verdict") in ("PASS", "PARTIAL")
        e13_pass = engine_results.get("e13", {}).get("verdict") in ("PASS", "PARTIAL")
        e15_pass = engine_results.get("e15", {}).get("verdict") in ("PASS", "PARTIAL")
        e19_pass = engine_results.get("e19", {}).get("verdict") in ("PASS", "PARTIAL")
        e20_pass = engine_results.get("e20", {}).get("verdict") in ("PASS", "PARTIAL")
        e21_pass = engine_results.get("e21", {}).get("verdict") in ("PASS", "PARTIAL")
        e22_pass = engine_results.get("e22", {}).get("verdict") in ("PASS", "PARTIAL")

        mode = "NORMAL"
        if e12_pass and e15_pass:
            mode = "VOLATILE"
        if e13_pass and e20_pass:
            mode = "SUDDEN"
        if e19_pass and e21_pass and e22_pass:
            mode = "HIDDEN"

        # ── Score ──
        score = max(bullish, bearish) + amp_count
        if big_move:
            score += len(big_move_engines)
        max_score = len(T2_DIRECTION) + len(T1_GATES) + len(T3_AMPLIFIERS) + len(T4_BIG_MOVE)

        # ── Signal Type — always generate if direction exists ──
        if t2_direction == "NEUTRAL":
            signal_type = "SKIP"
        elif big_move:
            signal_type = "BIG_MOVE_ALERT"
        elif mode == "VOLATILE":
            signal_type = "VOLATILE_BUY"
        elif amp_count >= 3:
            signal_type = f"STRONG_BUY_{'CALL' if t2_direction == 'BULLISH' else 'PUT'}"
        else:
            signal_type = f"BUY_{'CALL' if t2_direction == 'BULLISH' else 'PUT'}"

        # ── Entry / SL / Targets ──
        entry_data = self._get_entry_data(engine_results, t2_direction)
        entry_low = entry_data.get("entry_low", 0)
        entry_high = entry_data.get("entry_high", 0)
        entry_mid = (entry_low + entry_high) / 2 if entry_low and entry_high else 0

        sl_pct = 0.15 if mode == "VOLATILE" else 0.20
        sl = round(entry_mid * (1 - sl_pct), 1) if entry_mid else 0

        t1_target = round(entry_mid * 1.30, 1) if entry_mid else 0
        t2_target = round(entry_mid * 1.50, 1) if entry_mid else 0
        t3_target = round(entry_mid * 2.00, 1) if entry_mid else 0

        risk = entry_mid - sl if entry_mid and sl else 1
        reward = t1_target - entry_mid if t1_target and entry_mid else 0
        rr = f"1:{round(reward / risk, 1)}" if risk > 0 else "—"

        return self._build_signal(
            signal_type,
            instrument=entry_data.get("instrument", "NIFTY"),
            strike=entry_data.get("strike", 0),
            entry=[entry_low, entry_high] if entry_low else [],
            sl=sl,
            t1=t1_target,
            t2=t2_target,
            t3=t3_target,
            score=score,
            max_score=max_score,
            rr=rr,
            mode=mode,
            reasoning=reasoning,
            engine_verdicts=engine_verdicts,
        )

    def _get_entry_data(self, engine_results: dict, direction: str) -> dict:
        e05 = engine_results.get("e05", {})
        data = e05.get("data", {})

        spot = data.get("spot", 0)
        if not spot:
            e08 = engine_results.get("e08", {}).get("data", {})
            spot = e08.get("spot", 0) or e08.get("d_vwap", 0)
        if not spot:
            e03 = engine_results.get("e03", {}).get("data", {})
            support = e03.get("support", 0)
            resistance = e03.get("resistance", 0)
            if support and resistance:
                spot = (support + resistance) / 2

        call_wall = data.get("call_wall", 0)
        put_wall = data.get("put_wall", 0)

        if spot:
            atm = round(spot / 50) * 50
            strike = atm
            opt_type = "CE" if direction == "BULLISH" else "PE"
            instrument = f"NIFTY {strike} {opt_type}"

            est_premium = round(spot * 0.005, 1)
            entry_low = round(est_premium * 0.95, 1)
            entry_high = round(est_premium * 1.05, 1)

            return {
                "instrument": instrument,
                "strike": strike,
                "entry_low": entry_low,
                "entry_high": entry_high,
            }

        return {"instrument": "NIFTY", "strike": 0, "entry_low": 0, "entry_high": 0}

    def _build_signal(self, signal_type: str, **kwargs) -> dict:
        return {
            "type": signal_type,
            "instrument": kwargs.get("instrument", ""),
            "strike": kwargs.get("strike", 0),
            "entry": kwargs.get("entry", []),
            "sl": kwargs.get("sl", 0),
            "t1": kwargs.get("t1", 0),
            "t2": kwargs.get("t2", 0),
            "t3": kwargs.get("t3", 0),
            "score": kwargs.get("score", 0),
            "maxScore": kwargs.get("max_score", 0),
            "rr": kwargs.get("rr", "—"),
            "mode": kwargs.get("mode", "NORMAL"),
            "reasoning": kwargs.get("reasoning", []),
            "engineVerdicts": kwargs.get("engine_verdicts", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
