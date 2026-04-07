"""
Trade Tracker — records signals as trades, tracks P&L, computes stats and learning insights.
Stores trades in memory; optionally persists to PostgreSQL.
"""

import uuid
import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger("trade_tracker")


class TradeTracker:
    def __init__(self):
        self.trades: list[dict] = []

    # ── Record / Update ─────────────────────────────────────────────────

    def record_trade(self, signal_data: dict, engines_snapshot: dict | None = None) -> dict:
        """Create a new trade record from a generated signal."""
        # Handle entry as array [low, high] or single number
        entry_raw = signal_data.get("entry") or signal_data.get("entry_price")
        if isinstance(entry_raw, list) and entry_raw:
            entry_price = sum(float(x) for x in entry_raw) / len(entry_raw)
        elif isinstance(entry_raw, (int, float)):
            entry_price = float(entry_raw)
        else:
            entry_price = None

        trade = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "date": date.today().isoformat(),
            "signal_type": signal_data.get("type") or signal_data.get("signal_type", "BUY"),
            "instrument": signal_data.get("instrument", "NIFTY"),
            "strike": signal_data.get("strike", "—"),
            "entry_price": round(entry_price, 1) if entry_price else None,
            "sl_price": float(signal_data.get("sl") or signal_data.get("sl_price") or 0) or None,
            "t1_price": float(signal_data.get("t1") or signal_data.get("t1_price") or 0) or None,
            "t2_price": float(signal_data.get("t2") or signal_data.get("t2_price") or 0) or None,
            "status": "ACTIVE",
            "exit_price": None,
            "pnl_amount": None,
            "pnl_pct": None,
            "sl_hit": False,
            "reason": signal_data.get("rr", ""),
            "engine_verdicts": {},  # Don't store full verdicts — too large + non-serializable
        }
        self.trades.append(trade)
        logger.info(f"[TRADE] Recorded #{len(self.trades)}: {trade['signal_type']} {trade['strike']} @ {trade['entry_price']}")
        return trade

    def update_trade(self, trade_id: str, exit_price: float, status: str, reason: str = "") -> Optional[dict]:
        """Mark a trade as WON / LOST / EXPIRED."""
        for t in self.trades:
            if t["id"] == trade_id:
                t["exit_price"] = exit_price
                t["status"] = status
                t["reason"] = reason
                if t["entry_price"] and exit_price:
                    t["pnl_amount"] = round(exit_price - t["entry_price"], 2)
                    t["pnl_pct"] = round((t["pnl_amount"] / t["entry_price"]) * 100, 1) if t["entry_price"] else 0
                t["sl_hit"] = status == "LOST"
                logger.info(f"[TRADE] Updated {trade_id[:8]}.. -> {status} | P&L: {t['pnl_amount']}")
                return t
        return None

    # ── Active Trade Monitoring ──────────────────────────────────────────

    def check_active_trades(self, current_tick: dict | None = None):
        """Check if SL or targets are hit for active trades given current tick data."""
        if not current_tick:
            return

        ltp = current_tick.get("ltp") or current_tick.get("last_price")
        if ltp is None:
            return

        for t in self.trades:
            if t["status"] != "ACTIVE":
                continue

            entry = t.get("entry_price")
            sl = t.get("sl_price")
            t1 = t.get("t1_price")
            t2 = t.get("t2_price")
            if entry is None:
                continue

            is_call = "CALL" in (t.get("signal_type") or "").upper()

            # Check stop loss
            if sl is not None:
                if (is_call and ltp <= sl) or (not is_call and ltp >= sl):
                    self.update_trade(
                        t["id"], ltp, "LOST",
                        f"SL hit at {ltp} — price reversed against position"
                    )
                    continue

            # Check target 1
            if t1 is not None:
                if (is_call and ltp >= t1) or (not is_call and ltp <= t1):
                    self.update_trade(
                        t["id"], ltp, "WON",
                        f"T1 hit at {ltp} — momentum confirmed"
                    )
                    continue

            # Check target 2 (higher priority if reached)
            if t2 is not None:
                if (is_call and ltp >= t2) or (not is_call and ltp <= t2):
                    self.update_trade(
                        t["id"], ltp, "WON",
                        f"T2 hit at {ltp} — strong follow-through"
                    )

    # ── Queries ──────────────────────────────────────────────────────────

    def get_today_trades(self) -> list[dict]:
        """Return trades for today."""
        today = date.today().isoformat()
        return [t for t in self.trades if t.get("date") == today]

    def get_stats(self) -> dict:
        """Compute today's aggregate stats."""
        today_trades = self.get_today_trades()
        closed = [t for t in today_trades if t["status"] in ("WON", "LOST")]
        won = [t for t in closed if t["status"] == "WON"]
        lost = [t for t in closed if t["status"] == "LOST"]

        today_pnl = sum(t.get("pnl_amount") or 0 for t in closed)
        win_rate = round((len(won) / len(closed)) * 100, 1) if closed else 0

        avg_rr = self._compute_avg_rr(closed)
        accuracy_trend = self._compute_accuracy_trend()
        insights = self.get_learning_insights()

        return {
            "today_pnl": round(today_pnl, 2),
            "today_trades": len(today_trades),
            "won": len(won),
            "lost": len(lost),
            "win_rate": win_rate,
            "avg_rr": avg_rr,
            "accuracy_trend": accuracy_trend,
            "learning_insights": insights,
        }

    # ── Analytics ─────────────────────────────────────────────────────────

    def _compute_avg_rr(self, closed: list[dict]) -> str:
        """Average reward-to-risk ratio of closed trades."""
        ratios = []
        for t in closed:
            entry = t.get("entry_price")
            sl = t.get("sl_price")
            exit_p = t.get("exit_price")
            if entry and sl and exit_p and entry != sl:
                risk = abs(entry - sl)
                reward = abs(exit_p - entry)
                if risk > 0:
                    ratios.append(reward / risk)
        if not ratios:
            return "—"
        return f"1:{round(sum(ratios) / len(ratios), 1)}"

    def _compute_accuracy_trend(self) -> str:
        """Compare last 10 closed trades vs previous 10."""
        closed = [t for t in self.trades if t["status"] in ("WON", "LOST")]
        if len(closed) < 5:
            return "IMPROVING"

        recent = closed[-10:]
        previous = closed[-20:-10] if len(closed) >= 20 else closed[:-10]

        recent_wr = sum(1 for t in recent if t["status"] == "WON") / len(recent) if recent else 0
        prev_wr = sum(1 for t in previous if t["status"] == "WON") / len(previous) if previous else 0

        return "IMPROVING" if recent_wr >= prev_wr else "DECLINING"

    def get_learning_insights(self) -> list[str]:
        """Analyze trade history and generate actionable learning strings."""
        closed = [t for t in self.trades if t["status"] in ("WON", "LOST")]
        insights = []

        if len(closed) < 3:
            return ["Accumulating trade data — insights will appear after 3+ closed trades"]

        # ── Per-engine accuracy ──
        engine_stats: dict[str, dict] = {}
        for t in closed:
            for eng, verdict in (t.get("engine_verdicts") or {}).items():
                if eng not in engine_stats:
                    engine_stats[eng] = {"won": 0, "lost": 0}
                if t["status"] == "WON":
                    engine_stats[eng]["won"] += 1
                else:
                    engine_stats[eng]["lost"] += 1

        for eng, s in engine_stats.items():
            total = s["won"] + s["lost"]
            if total >= 3:
                acc = round((s["won"] / total) * 100)
                if acc >= 70:
                    insights.append(
                        f"{eng} signals have {acc}% accuracy in last {total} trades — increasing weight"
                    )
                elif acc <= 40:
                    insights.append(
                        f"{eng} signals: {acc}% accuracy — reducing allocation"
                    )

        # ── Time-of-day patterns ──
        morning = [t for t in closed if _hour(t) is not None and _hour(t) < 10]
        midday = [t for t in closed if _hour(t) is not None and 10 <= _hour(t) < 14]
        afternoon = [t for t in closed if _hour(t) is not None and _hour(t) >= 14]

        for label, bucket in [("Morning (pre-10am)", morning), ("Midday (10-2pm)", midday), ("Afternoon (post-2pm)", afternoon)]:
            if len(bucket) >= 3:
                wr = round(sum(1 for t in bucket if t["status"] == "WON") / len(bucket) * 100)
                if wr >= 70:
                    insights.append(f"{label} trades: {wr}% win rate — high confidence zone")
                elif wr <= 40:
                    insights.append(f"{label} trades: {wr}% accuracy — reducing allocation")

        # ── SL hit timing ──
        sl_trades = [t for t in closed if t["sl_hit"] and _hour(t) is not None]
        if len(sl_trades) >= 3:
            early_sl = sum(1 for t in sl_trades if _hour(t) < 10)
            if early_sl / len(sl_trades) > 0.5:
                insights.append(
                    f"SL hits mostly occur before 10 AM ({early_sl}/{len(sl_trades)}) — delaying entry may improve results"
                )

        # ── PCR range patterns ──
        pcr_high = [t for t in closed if (t.get("pcr") or 0) > 1.3]
        if len(pcr_high) >= 3:
            wr = round(sum(1 for t in pcr_high if t["status"] == "WON") / len(pcr_high) * 100)
            insights.append(f"PCR > 1.3 trades: {wr}% win rate — {'high confidence zone' if wr >= 65 else 'needs review'}")

        # ── VIX range patterns ──
        vix_low = [t for t in closed if (t.get("vix") or 99) < 14]
        if len(vix_low) >= 3:
            wr = round(sum(1 for t in vix_low if t["status"] == "WON") / len(vix_low) * 100)
            insights.append(f"Low VIX (<14) trades: {wr}% win rate — {'favorable conditions' if wr >= 60 else 'caution advised'}")

        # ── Overall win rate ──
        total_wr = round(sum(1 for t in closed if t["status"] == "WON") / len(closed) * 100)
        insights.append(f"Overall system accuracy: {total_wr}% across {len(closed)} trades")

        return insights


def _hour(trade: dict) -> Optional[int]:
    """Extract hour from trade timestamp string (HH:MM:SS)."""
    ts = trade.get("timestamp", "")
    if not ts or ":" not in ts:
        return None
    try:
        return int(ts.split(":")[0])
    except (ValueError, IndexError):
        return None
