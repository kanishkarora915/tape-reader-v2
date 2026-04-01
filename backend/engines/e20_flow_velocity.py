"""
E20 — Flow Velocity Engine (Tier 4: Big Move)
Tracks premium change SPEED across strikes.
  - ATM premium up > 15% in < 60 seconds = urgent buying
  - Multiple strikes expanding simultaneously = broad volatility bid
  - Velocity reversal detection
"""

import time
from .base import BaseEngine, EngineResult


class FlowVelocityEngine(BaseEngine):
    name = "Flow Velocity"
    tier = 4
    refresh_seconds = 5

    def __init__(self):
        super().__init__()
        self._premium_snapshots = []  # list of (timestamp, {strike: {ce_ltp, pe_ltp}})
        self._max_snapshots = 24      # ~2 minutes of 5s intervals
        self._velocity_threshold = 15  # 15% premium change = urgent

    def _capture_snapshot(self, chain: list) -> dict:
        """Capture current premium levels for all strikes."""
        snap = {}
        for s in chain:
            strike = s.get("strike", 0)
            snap[strike] = {
                "ce_ltp": s.get("ce_ltp", 0) or 0,
                "pe_ltp": s.get("pe_ltp", 0) or 0,
            }
        return snap

    def _compute_velocities(self, current_snap: dict, lookback_seconds: int = 60) -> dict:
        """Compute premium change velocity vs snapshot from ~lookback_seconds ago."""
        if len(self._premium_snapshots) < 2:
            return {"velocities": [], "max_velocity": 0, "expanding_strikes": 0}

        now = time.time()
        # Find snapshot closest to lookback_seconds ago
        target_time = now - lookback_seconds
        old_snap = None
        old_time = None
        for ts, snap in self._premium_snapshots:
            if ts <= target_time:
                old_snap = snap
                old_time = ts
            else:
                break

        if old_snap is None:
            # Use oldest available
            old_time, old_snap = self._premium_snapshots[0]

        elapsed = now - old_time
        if elapsed < 5:
            return {"velocities": [], "max_velocity": 0, "expanding_strikes": 0}

        velocities = []
        expanding = 0
        for strike, curr in current_snap.items():
            if strike not in old_snap:
                continue
            old = old_snap[strike]

            for opt_type in ["ce", "pe"]:
                key = f"{opt_type}_ltp"
                old_val = old.get(key, 0)
                new_val = curr.get(key, 0)
                if old_val > 0:
                    change_pct = ((new_val - old_val) / old_val) * 100
                    velocity_per_min = change_pct / (elapsed / 60) if elapsed > 0 else 0

                    if abs(change_pct) > 5:  # Meaningful change
                        velocities.append({
                            "strike": strike, "type": opt_type.upper(),
                            "change_pct": round(change_pct, 2),
                            "velocity_per_min": round(velocity_per_min, 2),
                            "old": old_val, "new": new_val,
                        })
                    if change_pct > 5:
                        expanding += 1

        velocities.sort(key=lambda x: abs(x.get("velocity_per_min", 0)), reverse=True)
        max_vel = abs(velocities[0]["velocity_per_min"]) if velocities else 0

        return {
            "velocities": velocities[:10],
            "max_velocity": round(max_vel, 2),
            "expanding_strikes": expanding,
        }

    def _detect_reversal(self) -> dict:
        """Detect velocity reversal: direction flipped in recent snapshots."""
        if len(self._premium_snapshots) < 6:
            return {"detected": False}

        # Compare first-half vs second-half of recent snapshots
        mid = len(self._premium_snapshots) // 2
        first_snap = self._premium_snapshots[mid]
        earliest_snap = self._premium_snapshots[0]
        latest_snap = self._premium_snapshots[-1]

        # Check if ATM-like strikes reversed direction
        first_changes = {}
        second_changes = {}
        for strike in latest_snap[1]:
            if strike in first_snap[1] and strike in earliest_snap[1]:
                for opt in ["ce_ltp", "pe_ltp"]:
                    v0 = earliest_snap[1][strike].get(opt, 0)
                    v1 = first_snap[1][strike].get(opt, 0)
                    v2 = latest_snap[1][strike].get(opt, 0)
                    if v0 > 0 and v1 > 0:
                        first_changes[f"{strike}_{opt}"] = v1 - v0
                        second_changes[f"{strike}_{opt}"] = v2 - v1

        reversals = 0
        for key in first_changes:
            if key in second_changes:
                if first_changes[key] > 0 and second_changes[key] < 0:
                    reversals += 1
                elif first_changes[key] < 0 and second_changes[key] > 0:
                    reversals += 1

        return {"detected": reversals >= 3, "reversal_count": reversals}

    def compute(self, ctx: dict) -> EngineResult:
        chain = ctx.get("chains", [])
        if not chain:
            return EngineResult(verdict="NEUTRAL", data={"error": "No chain data"})

        current_snap = self._capture_snapshot(chain)
        now = time.time()
        self._premium_snapshots.append((now, current_snap))
        if len(self._premium_snapshots) > self._max_snapshots:
            self._premium_snapshots.pop(0)

        vel_data = self._compute_velocities(current_snap)
        reversal = self._detect_reversal()

        max_vel = vel_data["max_velocity"]
        expanding = vel_data["expanding_strikes"]
        urgent = max_vel > self._velocity_threshold

        # Broad volatility bid = multiple strikes expanding simultaneously
        broad_bid = expanding >= 5

        # Direction from top velocity signal
        direction = "NEUTRAL"
        if vel_data["velocities"]:
            top = vel_data["velocities"][0]
            if top["type"] == "CE" and top["change_pct"] > 0:
                direction = "BULLISH"
            elif top["type"] == "PE" and top["change_pct"] > 0:
                direction = "BEARISH"
            elif top["type"] == "CE" and top["change_pct"] < 0:
                direction = "BEARISH"
            elif top["type"] == "PE" and top["change_pct"] < 0:
                direction = "BULLISH"

        urgency_level = "LOW"
        if urgent:
            urgency_level = "EXTREME"
        elif max_vel > 8:
            urgency_level = "HIGH"
        elif max_vel > 4:
            urgency_level = "MODERATE"

        confidence = 20
        if urgent:
            confidence += 30
        if broad_bid:
            confidence += 20
        if reversal["detected"]:
            confidence += 10

        verdict = "PASS" if urgent or broad_bid else (
            "PARTIAL" if max_vel > 5 else "NEUTRAL")

        return EngineResult(
            verdict=verdict,
            direction=direction,
            confidence=min(confidence, 90),
            data={
                "velocity_signals": vel_data["velocities"],
                "max_velocity": max_vel,
                "expanding_strikes": expanding,
                "broad_volatility_bid": broad_bid,
                "reversal": reversal,
                "direction": direction,
                "urgency_level": urgency_level,
            }
        )
