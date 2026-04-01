"""
BuyBy Trading System — Demo/Mock Data Generator
Provides realistic mock data when no live Kite connection is active.
"""

import asyncio
import random
import math
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def _ist_now():
    return datetime.now(IST)


def _rand(low, high, decimals=2):
    return round(random.uniform(low, high), decimals)


def generate_tick_data():
    """Generate tick data based on last trading session (Apr 1, 2026 close)."""
    # Last session closing levels (realistic)
    nifty_base = 23165
    bn_base = 48720
    sensex_base = 76230
    vix = 14.35

    # Small jitter to simulate tick movement
    nifty_chg = _rand(-3, 3, 1)
    bn_chg = _rand(-8, 8, 1)
    sensex_chg = _rand(-5, 5, 1)

    return {
        "nifty": {
            "ltp": round(nifty_base + nifty_chg, 1),
            "change": -142.3 + nifty_chg,
            "changePct": -0.61,
            "high": 23310.5,
            "low": 23110.8,
        },
        "banknifty": {
            "ltp": round(bn_base + bn_chg, 1),
            "change": -285.6 + bn_chg,
            "changePct": -0.58,
            "high": 49080.3,
            "low": 48520.1,
        },
        "sensex": {
            "ltp": round(sensex_base + sensex_chg, 1),
            "change": -398.2 + sensex_chg,
            "changePct": -0.52,
            "high": 76780.5,
            "low": 76050.2,
        },
        "vix": round(vix + _rand(-0.1, 0.1, 2), 2),
    }


def generate_engine_data():
    """Generate mock data for all 24 engines."""
    tick = generate_tick_data()
    nifty_ltp = tick["nifty"]["ltp"]
    atm = round(nifty_ltp / 50) * 50
    ivr = random.randint(18, 55)
    pcr = _rand(0.6, 1.5, 2)
    bias = "BULLISH" if random.random() > 0.45 else "BEARISH"
    opp = "BEARISH" if bias == "BULLISH" else "BULLISH"

    def _verdict(tier, bullish_prob=0.6):
        if tier == 1:
            return "PASS" if random.random() < 0.75 else "FAIL"
        return bias if random.random() < bullish_prob else opp

    def _conf():
        return random.randint(40, 95)

    # Generate OI chain
    chain_data = []
    for i in range(-8, 9):
        strike = atm + i * 50
        ce_oi = random.randint(50000, 800000)
        pe_oi = random.randint(50000, 800000)
        ce_chg = random.randint(-50000, 80000)
        pe_chg = random.randint(-50000, 80000)
        ce_ltp = max(1, round(max(0, nifty_ltp - strike) + _rand(-20, 40), 1))
        pe_ltp = max(1, round(max(0, strike - nifty_ltp) + _rand(-20, 40), 1))
        ce_iv = _rand(12, 25, 1)
        pe_iv = _rand(12, 28, 1)
        chain_data.append({
            "strike": strike, "ce_oi": ce_oi, "pe_oi": pe_oi,
            "ce_chg": ce_chg, "pe_chg": pe_chg,
            "ce_ltp": ce_ltp, "pe_ltp": pe_ltp,
            "ce_iv": ce_iv, "pe_iv": pe_iv,
            "atm": strike == atm,
        })

    max_pain = atm + random.choice([-50, 0, 50])

    # GEX data
    gex_data = []
    for row in chain_data:
        s = row["strike"]
        call_gex = _rand(0, 100) if s >= atm else _rand(0, 30)
        put_gex = _rand(0, 100) if s <= atm else _rand(0, 30)
        gex_data.append({"strike": s, "call_gex": call_gex, "put_gex": -put_gex})

    call_wall = atm + random.choice([100, 150, 200])
    put_wall = atm - random.choice([100, 150, 200])

    # Writer trap events
    traps = []
    if random.random() > 0.5:
        trap_strike = atm + random.choice([-100, -50, 50, 100])
        traps.append({
            "strike": trap_strike,
            "side": "Call" if trap_strike > atm else "Put",
            "oi_drop": f"-{random.randint(5, 15)}%",
            "premium_change": f"+{random.randint(3, 12)}%",
            "timestamp": _ist_now().strftime("%H:%M:%S"),
        })

    # Technical votes
    ema_bull = bias == "BULLISH"
    rsi_val = _rand(35, 70, 1)
    tech_votes = {
        "ema": {"value": f"{'20>50' if ema_bull else '20<50'}", "vote": "BULLISH" if ema_bull else "BEARISH"},
        "rsi": {"value": str(rsi_val), "vote": "BULLISH" if rsi_val > 55 else ("BEARISH" if rsi_val < 45 else "NEUTRAL")},
        "macd": {"value": f"{'Positive' if random.random() > 0.4 else 'Negative'}", "vote": bias if random.random() > 0.3 else opp},
        "supertrend": {"value": f"{'Above' if bias == 'BULLISH' else 'Below'}", "vote": bias},
    }
    bull_tech = sum(1 for v in tech_votes.values() if v["vote"] == "BULLISH")
    bear_tech = sum(1 for v in tech_votes.values() if v["vote"] == "BEARISH")
    tech_direction = "BULLISH" if bull_tech >= 3 else ("BEARISH" if bear_tech >= 3 else "NEUTRAL")

    # VWAP
    d_vwap = round(nifty_ltp + _rand(-30, 30), 1)
    w_vwap = round(nifty_ltp + _rand(-60, 60), 1)

    # FII/DII
    fii_net = _rand(-2000, 3000, 0)
    dii_net = _rand(-1500, 2500, 0)

    # Structure
    structures = ["UPTREND", "DOWNTREND", "RANGE", "BOS", "CHoCH"]
    weights = [0.3, 0.25, 0.25, 0.1, 0.1]
    regime = random.choices(structures, weights)[0]

    engines = {
        "e01": {
            "name": "OI Pulse", "tier": 1,
            "verdict": _verdict(1), "direction": bias, "confidence": _conf(),
            "data": {
                "oi_change_ce": random.randint(-100000, 100000),
                "oi_change_pe": random.randint(-100000, 100000),
                "writer_signal": f"{'CE' if bias == 'BULLISH' else 'PE'} writers covering",
                "total_oi_trend": random.choice(["Building", "Flat", "Declining"]),
            }
        },
        "e02": {
            "name": "IV Regime", "tier": 1,
            "verdict": "PASS" if ivr < 50 else ("PARTIAL" if ivr < 70 else "FAIL"),
            "direction": "NEUTRAL", "confidence": _conf(),
            "data": {
                "ivr": ivr, "atm_iv": _rand(12, 22, 1),
                "ce_iv": _rand(13, 20, 1), "pe_iv": _rand(14, 24, 1),
                "gate_status": "OPEN" if ivr < 50 else ("PARTIAL" if ivr < 70 else "BLOCKED"),
                "skew": _rand(-3, 5, 2),
            }
        },
        "e03": {
            "name": "Market Structure", "tier": 1,
            "verdict": "PASS" if regime in ["UPTREND", "DOWNTREND", "BOS"] else "NEUTRAL",
            "direction": "BULLISH" if regime in ["UPTREND", "BOS"] else ("BEARISH" if regime in ["DOWNTREND", "CHoCH"] else "NEUTRAL"),
            "confidence": _conf(),
            "data": {
                "regime": regime,
                "support": round(nifty_ltp - _rand(80, 200), 0),
                "resistance": round(nifty_ltp + _rand(80, 200), 0),
                "order_blocks": [
                    {"level": round(nifty_ltp - _rand(50, 150), 0), "type": "Demand"},
                    {"level": round(nifty_ltp + _rand(50, 150), 0), "type": "Supply"},
                ],
                "events": [
                    {"type": regime, "level": round(nifty_ltp + _rand(-50, 50), 0), "time": _ist_now().strftime("%H:%M")},
                ],
            }
        },
        "e04": {
            "name": "Confluence", "tier": 1,
            "verdict": "PASS", "direction": bias, "confidence": _conf(),
            "data": {
                "total_score": random.randint(4, 8), "max_score": 9,
                "t2_bull_votes": random.randint(2, 5), "t2_bear_votes": random.randint(1, 4),
                "direction": bias, "gate_passed": True,
            }
        },
        "e05": {
            "name": "GEX Wall", "tier": 2,
            "verdict": "PASS", "direction": bias, "confidence": _conf(),
            "data": {
                "gex_by_strike": gex_data, "call_wall": call_wall, "put_wall": put_wall,
                "total_gex": _rand(-50, 50), "spot": nifty_ltp, "flip_detected": random.random() > 0.85,
            }
        },
        "e06": {
            "name": "PCR Flow", "tier": 2,
            "verdict": "PASS", "direction": "BULLISH" if pcr > 1.2 else ("BEARISH" if pcr < 0.7 else "NEUTRAL"),
            "confidence": _conf(),
            "data": {"pcr": pcr, "pcr_change": _rand(-0.1, 0.1, 3), "bias": "Fear" if pcr > 1.3 else ("Greed" if pcr < 0.6 else "Neutral")}
        },
        "e07": {
            "name": "Writer Trap", "tier": 2,
            "verdict": "PASS" if traps else "NEUTRAL",
            "direction": bias if traps else "NEUTRAL", "confidence": _conf(),
            "data": {"traps": traps, "direction": bias if traps else "NEUTRAL"}
        },
        "e08": {
            "name": "VWAP", "tier": 2,
            "verdict": "PASS", "direction": "BULLISH" if nifty_ltp > d_vwap else "BEARISH",
            "confidence": _conf(),
            "data": {
                "d_vwap": d_vwap, "w_vwap": w_vwap,
                "sd1_upper": round(d_vwap + 40, 1), "sd1_lower": round(d_vwap - 40, 1),
                "sd2_upper": round(d_vwap + 80, 1), "sd2_lower": round(d_vwap - 80, 1),
                "position": "ABOVE" if nifty_ltp > d_vwap else "BELOW",
            }
        },
        "e09": {
            "name": "Technical", "tier": 2,
            "verdict": "PASS" if tech_direction != "NEUTRAL" else "NEUTRAL",
            "direction": tech_direction, "confidence": _conf(),
            "data": {
                "votes": tech_votes, "summary": f"{bull_tech}/4 BULL, {bear_tech}/4 BEAR",
                "direction": tech_direction,
                "ema_20": round(nifty_ltp + _rand(-15, 15), 1),
                "ema_50": round(nifty_ltp + _rand(-30, 30), 1),
                "rsi": rsi_val,
            }
        },
        "e10": {
            "name": "Expiry Flow", "tier": 2,
            "verdict": "PASS", "direction": bias, "confidence": _conf(),
            "data": {
                "max_pain": max_pain, "days_to_expiry": random.randint(0, 6),
                "oi_drift_direction": bias, "expiry_type": random.choice(["Weekly", "Monthly"]),
            }
        },
        "e11": {
            "name": "FII/DII", "tier": 2,
            "verdict": "PASS", "direction": "BULLISH" if fii_net > 0 else "BEARISH",
            "confidence": _conf(),
            "data": {
                "fii_net_fut": fii_net, "dii_net_fut": dii_net,
                "fii_3day_trend": "Buying" if fii_net > 500 else ("Selling" if fii_net < -500 else "Flat"),
                "fii_opt_net": _rand(-1000, 1000, 0),
            }
        },
        "e12": {
            "name": "Volatility", "tier": 3,
            "verdict": "PASS" if random.random() > 0.6 else "NEUTRAL",
            "direction": "NEUTRAL", "confidence": _conf(),
            "data": {
                "vix": tick["vix"], "vix_spike": random.random() > 0.7,
                "bb_squeeze": random.choice(["Compressed", "Normal", "Expanding"]),
                "iv_expanding": random.random() > 0.6,
                "atr_ratio": _rand(0.3, 1.2, 2),
                "volatile_mode": random.random() > 0.8,
            }
        },
        "e13": {
            "name": "Momentum", "tier": 3,
            "verdict": "PASS" if random.random() > 0.65 else "NEUTRAL",
            "direction": bias, "confidence": _conf(),
            "data": {"ignition_detected": random.random() > 0.7, "consecutive_bars": random.randint(0, 4)}
        },
        "e14": {
            "name": "Delta Spike", "tier": 3,
            "verdict": "NEUTRAL", "direction": bias, "confidence": _conf(),
            "data": {"delta_shift": _rand(-0.3, 0.3, 3), "otm_ce_activity": random.randint(0, 100), "otm_pe_activity": random.randint(0, 100)}
        },
        "e15": {
            "name": "VWAP Snapback", "tier": 3,
            "verdict": "NEUTRAL", "direction": opp, "confidence": _conf(),
            "data": {"stretched": random.random() > 0.75, "distance_from_vwap": _rand(0, 80, 1), "snap_probability": random.randint(20, 80)}
        },
        "e16": {
            "name": "Multi-TF", "tier": 3,
            "verdict": "PASS" if random.random() > 0.5 else "NEUTRAL",
            "direction": bias, "confidence": _conf(),
            "data": {"tf_5m": bias, "tf_15m": bias if random.random() > 0.3 else opp, "tf_1h": bias if random.random() > 0.4 else opp, "aligned": random.random() > 0.4}
        },
        "e17": {
            "name": "Cross-Asset", "tier": 3,
            "verdict": "NEUTRAL", "direction": "NEUTRAL", "confidence": _conf(),
            "data": {"usdinr": _rand(83, 85, 2), "crude": _rand(72, 82, 1), "gold": _rand(2300, 2500, 0)}
        },
        "e18": {
            "name": "Statistical Edge", "tier": 3,
            "verdict": "PASS" if random.random() > 0.5 else "NEUTRAL",
            "direction": bias, "confidence": _conf(),
            "data": {"win_rate": random.randint(45, 78), "monte_carlo_score": random.randint(55, 85), "similar_setups": random.randint(12, 45)}
        },
        "e19": {
            "name": "Unusual Activity", "tier": 4,
            "verdict": "NEUTRAL", "direction": "NEUTRAL", "confidence": _conf(),
            "data": {"uoa_signals": [], "block_trades": random.random() > 0.8, "active": random.random() > 0.75}
        },
        "e20": {
            "name": "Flow Velocity", "tier": 4,
            "verdict": "NEUTRAL", "direction": "NEUTRAL", "confidence": _conf(),
            "data": {"max_velocity": _rand(0, 15, 1), "urgency_level": random.choice(["Low", "Medium", "High"]), "active": random.random() > 0.7}
        },
        "e21": {
            "name": "Hidden Divergence", "tier": 4,
            "verdict": "NEUTRAL", "direction": "NEUTRAL", "confidence": _conf(),
            "data": {"divergences": [], "active": random.random() > 0.8}
        },
        "e22": {
            "name": "Microstructure", "tier": 4,
            "verdict": "NEUTRAL", "direction": "NEUTRAL", "confidence": _conf(),
            "data": {"imbalance_ratio": _rand(40, 70, 0), "absorption_side": random.choice(["None", "Buy", "Sell"]), "active": random.random() > 0.75}
        },
        "e23": {
            "name": "Pre-Market", "tier": 4,
            "verdict": "PASS", "direction": bias, "confidence": _conf(),
            "data": {
                "morning_bias": f"{'BULLISH' if bias == 'BULLISH' else 'BEARISH'} GAP",
                "gift_nifty": round(nifty_ltp + _rand(-50, 50), 0),
                "gap_fill_target": round(nifty_ltp + _rand(-30, 30), 0),
                "global_cues": [
                    {"name": "Dow Jones", "change": _rand(-1.5, 1.5, 2)},
                    {"name": "Nasdaq", "change": _rand(-2, 2, 2)},
                    {"name": "Nikkei", "change": _rand(-1, 1.5, 2)},
                    {"name": "Hang Seng", "change": _rand(-1.5, 1, 2)},
                ],
            }
        },
        "e24": {
            "name": "AI Reasoning", "tier": 4,
            "verdict": "PASS", "direction": bias, "confidence": random.randint(60, 90),
            "data": {
                "rationale": f"Market showing {bias.lower()} bias with {regime.lower()} structure. PCR at {pcr} suggests {'fear/contrarian bullish setup' if pcr > 1.2 else 'greed/contrarian bearish setup' if pcr < 0.7 else 'neutral positioning'}. IVR at {ivr} keeps premiums {'affordable' if ivr < 50 else 'elevated'}. FII {'net long' if fii_net > 0 else 'net short'} supports the {bias.lower()} thesis. Key levels: support {round(nifty_ltp - 150)} / resistance {round(nifty_ltp + 150)}.",
                "risk_factors": [
                    f"IVR at {ivr} — {'premiums cheap, good for buying' if ivr < 50 else 'elevated, watch for crush'}",
                    f"VIX at {tick['vix']} — {'low volatility, moves may be contained' if tick['vix'] < 15 else 'elevated, expect wider swings'}",
                    f"PCR at {pcr} — {'extreme levels, reversal possible' if pcr > 1.4 or pcr < 0.5 else 'within normal range'}",
                ],
                "confidence": random.randint(60, 90),
                "trade_recommendation": f"{'BUY NIFTY ' + str(atm) + (' CE' if bias == 'BULLISH' else ' PE')} | SL: 15% premium | T1: {call_wall if bias == 'BULLISH' else put_wall}",
            }
        },
    }

    return tick, engines, chain_data, max_pain


async def run_demo_broadcast(ws_manager, is_live_fn=None):
    """Background task: broadcast last-session data every 3 seconds when no live engine."""
    while True:
        try:
            # Skip if live market engine is running
            if is_live_fn and is_live_fn():
                await asyncio.sleep(5)
                continue

            if ws_manager.client_count > 0:
                tick, engines, chain, max_pain = generate_engine_data()

                await ws_manager.broadcast("tick", tick)
                await ws_manager.broadcast("engines", engines)
                await ws_manager.broadcast("chain", chain, index="NIFTY", max_pain=max_pain)

                # Occasionally send a signal
                if random.random() > 0.85:
                    bias = engines["e04"]["data"]["direction"]
                    atm = chain[len(chain)//2]["strike"]
                    signal = {
                        "type": f"BUY_{'CALL' if bias == 'BULLISH' else 'PUT'}",
                        "instrument": "NIFTY",
                        "strike": atm,
                        "entry": [_rand(150, 250, 0), _rand(260, 310, 0)],
                        "sl": _rand(120, 180, 0),
                        "t1": atm + (150 if bias == "BULLISH" else -150),
                        "t2": atm + (250 if bias == "BULLISH" else -250),
                        "score": random.randint(5, 8),
                        "maxScore": 9,
                        "rr": f"1:{_rand(1.5, 3.5, 1)}",
                        "mode": random.choice(["NORMAL", "HIGH_CONVICTION"]),
                        "reasoning": [engines["e24"]["data"]["rationale"]],
                        "timestamp": _ist_now().strftime("%H:%M:%S"),
                    }
                    await ws_manager.broadcast("signal", signal)

        except Exception as e:
            pass

        await asyncio.sleep(3)
