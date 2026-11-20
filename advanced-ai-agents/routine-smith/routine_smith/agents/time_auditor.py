"""Time Auditor Agent — Analyzes the user's schedule and finds available time pockets.

Responsibilities:
- Collect wake/sleep times, work hours, commute
- Identify all free time pockets in the day
- Calculate available minutes per pocket
- Negotiate with other agents when limitations are found
"""

from datetime import time, timedelta
from typing import Optional

from ..models import UserProfile, TimePocket, EnergyPattern, AgentMessage


class TimeAuditor:
    """Analyzes a user's schedule and identifies available time pockets."""

    def __init__(self):
        self.name = "Time Auditor"

    def collect_schedule(self) -> UserProfile:
        """Prompt the user for their schedule (or use defaults for demo)."""
        profile = UserProfile()
        print("\n=== Time Auditor: Let's Map Your Day ===")
        print("(Press Enter to accept defaults in brackets)")

        wake = input(f"  What time do you wake up? [{profile.wake_time.strftime('%H:%M')}]: ").strip()
        if wake:
            try:
                h, m = map(int, wake.split(":"))
                profile.wake_time = time(h, m)
            except (ValueError, IndexError):
                print("  Using default.")

        sleep = input(f"  What time do you go to sleep? [{profile.sleep_time.strftime('%H:%M')}]: ").strip()
        if sleep:
            try:
                h, m = map(int, sleep.split(":"))
                profile.sleep_time = time(h, m)
            except (ValueError, IndexError):
                print("  Using default.")

        work_start = input(f"  When do you start work/school? [{profile.work_start.strftime('%H:%M')}]: ").strip()
        if work_start:
            try:
                h, m = map(int, work_start.split(":"))
                profile.work_start = time(h, m)
            except (ValueError, IndexError):
                print("  Using default.")
        else:
            profile.work_start = None

        work_end = input(f"  When do you finish? [{profile.work_end.strftime('%H:%M') if profile.work_end else '17:00'}]: ").strip()
        if work_end:
            try:
                h, m = map(int, work_end.split(":"))
                profile.work_end = time(h, m)
            except (ValueError, IndexError):
                print("  Using default.")

        commute = input(f"  Commute (mins each way)? [{profile.commute_minutes}]: ").strip()
        if commute:
            try:
                profile.commute_minutes = int(commute)
            except ValueError:
                print("  Using default.")

        energy = input("  Are you a morning person, night person, or balanced? [balanced]: ").strip().lower()
        if energy in ("morning", "m", "morning person"):
            profile.energy_pattern = EnergyPattern.MORNING
        elif energy in ("night", "n", "night owl", "night person"):
            profile.energy_pattern = EnergyPattern.NIGHT
        else:
            profile.energy_pattern = EnergyPattern.BALANCED

        routine_m = input(f"  Morning routine (mins)? [{profile.morning_routine_minutes}]: ").strip()
        if routine_m:
            try:
                profile.morning_routine_minutes = int(routine_m)
            except ValueError:
                pass

        routine_e = input(f"  Evening wind-down (mins)? [{profile.evening_routine_minutes}]: ").strip()
        if routine_e:
            try:
                profile.evening_routine_minutes = int(routine_e)
            except ValueError:
                pass

        print()
        return profile

    def find_time_pockets(self, profile: UserProfile) -> list[TimePocket]:
        """Find all available time pockets in the user's day."""
        pockets = []
        wake_min = profile.wake_time.hour * 60 + profile.wake_time.minute
        sleep_min = profile.sleep_time.hour * 60 + profile.sleep_time.minute

        # Morning pocket: wake → commute/start
        if profile.work_start:
            work_start_min = profile.work_start.hour * 60 + profile.work_start.minute
            morning_gap = work_start_min - wake_min - profile.morning_routine_minutes
            if morning_gap > 5:
                start_h = wake_min + profile.morning_routine_minutes
                pockets.append(TimePocket(
                    label="Morning (before work)",
                    start=time(start_h // 60, start_h % 60),
                    end=profile.work_start,
                    duration_minutes=morning_gap,
                    typical_energy=EnergyPattern.MORNING,
                    is_commute_linked=True,
                ))

        # Lunch / midday pocket
        if profile.work_start and profile.work_end:
            ws = profile.work_start.hour * 60 + profile.work_start.minute
            we = profile.work_end.hour * 60 + profile.work_end.minute
            midday = ws + (we - ws) // 2
            pockets.append(TimePocket(
                label="Lunch / Midday Break",
                start=time(midday // 60 - 15, (midday - 15) % 60),
                end=time(midday // 60 + 15, (midday + 15) % 60),
                duration_minutes=30,
                typical_energy=EnergyPattern.BALANCED,
                is_mealtime_linked=True,
            ))

        # Evening pocket: after work → sleep
        if profile.work_end:
            we = profile.work_end.hour * 60 + profile.work_end.minute
            evening_start = we + profile.commute_minutes
            evening_gap = sleep_min - evening_start - profile.evening_routine_minutes
            if evening_gap > 15:
                pockets.append(TimePocket(
                    label="Evening (after work)",
                    start=time(evening_start // 60, evening_start % 60),
                    end=time(sleep_min // 60 - profile.evening_routine_minutes // 2,
                             (sleep_min - profile.evening_routine_minutes) % 60),
                    duration_minutes=evening_gap,
                    typical_energy=profile.energy_pattern,
                ))

        # Bedtime wind-down pocket
        sleep_pocket_start = sleep_min - profile.evening_routine_minutes
        pockets.append(TimePocket(
            label="Bedtime Wind-Down",
            start=time(sleep_pocket_start // 60, sleep_pocket_start % 60),
            end=profile.sleep_time,
            duration_minutes=profile.evening_routine_minutes,
            typical_energy=EnergyPattern.BALANCED,
        ))

        # Weekend/holiday — full day available
        if not profile.work_start or profile.has_flexible_schedule:
            pockets.append(TimePocket(
                label="Full Day Available",
                start=profile.wake_time,
                end=profile.sleep_time,
                duration_minutes=sleep_min - wake_min,
                typical_energy=profile.energy_pattern,
            ))

        profile.time_pockets = pockets
        return pockets

    def audit(self, profile: UserProfile) -> tuple[list[TimePocket], list[AgentMessage]]:
        """Run the audit: fill in defaults, find pockets, return messages."""
        messages = []
        pockets = self.find_time_pockets(profile)
        total_avail = sum(p.duration_minutes for p in pockets)
        total_day = (profile.sleep_time.hour * 60 + profile.sleep_time.minute) - \
                    (profile.wake_time.hour * 60 + profile.wake_time.minute)

        messages.append(AgentMessage(
            sender="Time Auditor",
            recipient="orchestrator",
            message_type="info",
            content=f"Found {len(pockets)} time pockets totaling {total_avail} free minutes out of "
                    f"{total_day} waking minutes ({total_avail / total_day * 100:.0f}% availability).",
        ))

        if total_avail < 60:
            messages.append(AgentMessage(
                sender="Time Auditor",
                recipient="Goal Aligner",
                message_type="adjustment",
                content=f"WARNING: Only {total_avail} free minutes available. Goals must be "
                        f"ultra-compact — prioritize minimal-viable versions under 5 minutes.",
            ))

        return pockets, messages