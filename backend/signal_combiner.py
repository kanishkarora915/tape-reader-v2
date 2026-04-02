"""
BuyBy Trading System — 4-Tier Signal Combiner
Combines 24 engine outputs into actionable trade signals.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("buyby.combiner")

# ── Engine Groups ───────────────────────────────────────────────────────

T1_GATES = ["e01", "e02", "e03", "e04"]
T2_DIRECTION = ["e05", "e06", "e07", "e08", "e09", "e10", "e11"]
T3_AMPLIFIERS = ["e12", "e13", "e14", "e15", "e16", "e17", "e18"]
T4_BIG_MOVE = ["e19", "e20", "e21", "e22", "e23"]
# e24 = Claude AI reasoning (separate)


class SignalCombiner:
    """4-tier signal combiner: Gate -> Direction -> Amplify -> Big Move."""

    def combine(self, engine_results: dict) -> dict:
        now = datetime.now(timezone.utc)
        ist_hour = (now.hour + 5) % 24
        ist_minute = (now.minute + 30) % 60
        if now.minute + 30 >= 60:
            ist_hour = (ist_hour + 1) % 24

        reasoning = []
        engine_verdicts = {}

        # Collect all verdicts — use correct keys from get_state()
        for eid, result in engine_results.items():
            engine_verdicts[eid] = {
                "verdict": result.get("verdict", "NEUTRAL"),
                "direction": result.get("direction", "NEUTRAL"),
                "confidence": result.get("confidence", 0),
                "name": result.get("name", eid),
            }

        # ── Time Gates ──
        if ist_hour == 9 and ist_minute < 25:
            reasoning.append("TIME GATE: Market opening volatility (9:15-9:25). No entry.")
            return self._build_signal("WAIT", reasoning=reasoning, engine_verdicts=engine_verdicts)

        if ist_hour >= 15:
            reasoning.append("TIME GATE: After 3:00 PM IST. No new entries.")
            return self._build_signal("WAIT", reasoning=reasoning, engine_verdicts=engine_verdicts)

        # ── T1: Gate Check (e01-e04 must all PASS) ──
        t1_pass = True
        for eid in T1_GATES:
            result = engine_results.get(eid, {})
            verdict = result.get("verdict", "NEUTRAL")
            if verdict not in ("PASS", "PARTIAL"):
                t1_pass = False
                name = result.get("name", eid)
                reasoning.append(f"T1 BLOCK: {name} ({eid}) → {verdict}")

        if not t1_pass:
            reasoning.append("HARD BLOCK: T1 gate engine(s) failed.")
            return self._build_signal("HARD_BLOCK", reasoning=reasoning, engine_verdicts=engine_verdicts)

        reasoning.append("T1 PASS: All 4 gate engines clear.")

        # ── T2: Direction (e05-e11 vote, need 3+ same direction) ──
        bullish = 0
        bearish = 0
        for eid in T2_DIRECTION:
            result = engine_results.get(eid, {})
            direction = result.get("direction", "NEUTRAL")
            if direction == "BULLISH":
                bullish += 1
            elif direction == "BEARISH":
                bearish += 1

        if bullish >= 3 and bullish > bearish:
            t2_direction = "BULLISH"
        elif bearish >= 3 and bearish > bullish:
            t2_direction = "BEARISH"
        else:
            reasoning.append(f"T2 SKIP: No clear direction (CALL votes: {bullish}, PUT votes: {bearish})")
            return self._build_signal("SKIP", reasoning=reasoning, engine_verdicts=engine_verdicts)

        reasoning.append(f"T2 DIRECTION: {t2_direction} (CALL: {bullish}, PUT: {bearish})")

        # ── T3: Amplifiers (e12-e18 matching direction) ──
        amp_count = 0
        for eid in T3_AMPLIFIERS:
            result = engine_results.get(eid, {})
            if result.get("verdict") == "PASS" and result.get("direction", "NEUTRAL") in (t2_direction, "NEUTRAL"):
                amp_count += 1

        reasoning.append(f"T3 AMPLIFIERS: {amp_count}/7 engines confirm")

        # ── T4: Big Move Detection (e19-e23, check for PASS) ──
        big_move = False
        big_move_engines = []
        for eid in T4_BIG_MOVE:
            result = engine_results.get(eid, {})
            if result.get("verdict") == "PASS":
                big_move = True
                big_move_engines.append(eid)

        if big_move:
            reasoning.append(f"T4 BIG MOVE ALERT: {', '.join(big_move_engines)} fired")

        # ── Mode Detection ──
        e12_pass = engine_results.get("e12", {}).get("verdict") == "PASS"
        e13_pass = engine_results.get("e13", {}).get("verdict") == "PASS"
        e15_pass = engine_results.get("e15", {}).get("verdict") == "PASS"
        e19_pass = engine_results.get("e19", {}).get("verdict") == "PASS"
        e20_pass = engine_results.get("e20", {}).get("verdict") == "PASS"
        e21_pass = engine_results.get("e21", {}).get("verdict") == "PASS"
        e22_pass = engine_results.get("e22", {}).get("verdict") == "PASS"

        mode = "NORMAL"
        if e12_pass and e15_pass:
            mode = "VOLATILE"
        if e13_pass and e20_pass:
            mode = "SUDDEN"
        if e19_pass and e21_pass and e22_pass:
            mode = "HIDDEN"

        # ── Score — dominant direction strength ──
        direction_score = max(bullish, bearish)
        score = direction_score + amp_count
        if big_move:
            score += len(big_move_engines)
        max_score = len(T2_DIRECTION) + len(T3_AMPLIFIERS) + len(T4_BIG_MOVE)

        # ── Signal Type ──
        if big_move and t1_pass:
            signal_type = "BIG_MOVE_ALERT"
        elif mode == "VOLATILE":
            signal_type = "VOLATILE_BUY"
        elif amp_count >= 4:
            signal_type = f"STRONG_BUY_{'CALL' if t2_direction == 'BULLISH' else 'PUT'}"
        else:
            signal_type = f"BUY_{'CALL' if t2_direction == 'BULLISH' else 'PUT'}"

        # ── Entry / SL / Targets from engine data ──
        entry_data = self._get_entry_data(engine_results, t2_direction)
        entry_low = entry_data.get("entry_low", 0)
        entry_high = entry_data.get("entry_high", 0)
        entry_mid = (entry_low + entry_high) / 2 if entry_low and entry_high else 0

        # SL: 15-20% of entry premium
        sl_pct = 0.15 if mode == "VOLATILE" else 0.20
        sl = round(entry_mid * (1 - sl_pct), 1) if entry_mid else 0

        # Targets
        t1_target = round(entry_mid * 1.30, 1) if entry_mid else 0
        t2_target = round(entry_mid * 1.50, 1) if entry_mid else 0
        t3_target = round(entry_mid * 2.00, 1) if entry_mid else 0

        # Risk-reward
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
        """Extract entry price data from ATM option in chain."""
        e05 = engine_results.get("e05", {})
        data = e05.get("data", {})

        # Get spot from multiple sources
        spot = data.get("spot", 0)
        if not spot:
            # Try VWAP engine
            e08 = engine_results.get("e08", {}).get("data", {})
            spot = e08.get("spot", 0) or e08.get("d_vwap", 0)
        if not spot:
            # Try E03 structure
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

            # Estimate entry from ATM option premium (rough: 1% of spot)
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
        """Build a standardized signal dict."""
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
