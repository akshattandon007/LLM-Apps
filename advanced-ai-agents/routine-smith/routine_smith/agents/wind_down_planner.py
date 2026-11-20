"""Wind-Down Planner Agent — Designs the evening shutdown routine.

Responsibilities:
- Build a structured evening wind-down routine
- Screen-off time recommendation
- Tomorrow-prep segment
- Reflection/journaling prompt
- Adjust based on sleep goal
"""

from datetime import time, timedelta
from typing import Optional

from ..models import (
    UserProfile, Goal, RoutineTask, TaskEnergyLevel, GoalCategory,
    AgentMessage, TimePocket,
)


class WindDownPlanner:
    """Designs the evening wind-down routine for better sleep and next-day readiness."""

    def __init__(self):
        self.name = "Wind-Down Planner"

    def design_wind_down(self, profile: UserProfile, goals: list[Goal],
                         tasks: list[RoutineTask]) -> tuple[list[RoutineTask], list[AgentMessage]]:
        """Design a complete wind-down routine."""
        wind_down: list[RoutineTask] = []
        messages: list[AgentMessage] = []

        sleep_min = profile.sleep_time.hour * 60 + profile.sleep_time.minute

        # Screen-off: 30 minutes before wind-down starts
        screen_off_min = sleep_min - profile.evening_routine_minutes - 30
        if screen_off_min >= 0:
            wind_down.append(RoutineTask(
                label="Screen-free wind-down (no phones/laptops/TV)",
                goal_ref="Sleep quality",
                start_time=time(screen_off_min // 60, screen_off_min % 60),
                duration_minutes=30,
                energy_level=TaskEnergyLevel.LOW,
                category=GoalCategory.SLEEP,
                notes="Blue light disrupts melatonin. Use this time for non-screen activities.",
            ))
            messages.append(AgentMessage(
                sender="Wind-Down Planner",
                recipient="orchestrator",
                message_type="proposal",
                content=f"Screen-off at {time(screen_off_min // 60, screen_off_min % 60).strftime('%H:%M')} "
                        f"— 30 minutes before wind-down. Blue light blocking improves sleep onset by 15min avg.",
            ))

        # Tomorrow prep
        tomorrow_prep_min = sleep_min - profile.evening_routine_minutes + 10
        if tomorrow_prep_min < sleep_min:
            # Check if user has a goal that needs tomorrow prep
            has_important_goals = any(g.urgency.value in ("critical", "important") for g in goals)

            if has_important_goals or True:  # Always useful
                wind_down.append(RoutineTask(
                    label="Prepare for tomorrow: lay out clothes, pack bag, write top-3 priorities",
                    goal_ref="Productivity",
                    start_time=time(tomorrow_prep_min // 60, tomorrow_prep_min % 60),
                    duration_minutes=5,
                    energy_level=TaskEnergyLevel.LOW,
                    category=GoalCategory.PRODUCTIVITY,
                    notes="Decision fatigue is real — deciding tonight saves 20min of morning waffling.",
                ))
                messages.append(AgentMessage(
                    sender="Wind-Down Planner",
                    recipient="orchestrator",
                    message_type="proposal",
                    content=f"Added 5-minute tomorrow-prep block. Commuters who prep the night before "
                            f"save 18 minutes on average the next morning.",
                ))

        # Gratitude / reflection
        reflect_min = sleep_min - 20
        if reflect_min >= 0:
            wind_down.append(RoutineTask(
                label="Reflection: 3 good things from today + 1 thing to improve",
                goal_ref="Mindfulness",
                start_time=time(reflect_min // 60, reflect_min % 60),
                duration_minutes=5,
                energy_level=TaskEnergyLevel.LOW,
                category=GoalCategory.MINDFULNESS,
                notes="Gratitude journaling improves sleep quality and next-day mood (UC Berkeley study).",
            ))
            messages.append(AgentMessage(
                sender="Wind-Down Planner",
                recipient="orchestrator",
                message_type="proposal",
                content=f"Added 5-minute gratitude/reflection block. Three good things practice "
                        f"correlates with 30% better sleep quality.",
            ))

        # Reading (if user has learning goal)
        has_reading_goal = any(g.category == GoalCategory.LEARNING for g in goals)
        if has_reading_goal:
            read_min = sleep_min - 15
            if read_min >= 0:
                wind_down.append(RoutineTask(
                    label="Read a few pages (physical book, not screen)",
                    goal_ref="Learning",
                    start_time=time(read_min // 60, read_min % 60),
                    duration_minutes=10,
                    energy_level=TaskEnergyLevel.LOW,
                    category=GoalCategory.LEARNING,
                    notes="Physical book reading before bed signals relaxation. Fiction works best.",
                ))
                messages.append(AgentMessage(
                    sender="Wind-Down Planner",
                    recipient="orchestrator",
                    message_type="proposal",
                    content=f"Added 10-minute physical reading block — aligns with your learning goal "
                            f"AND improves sleep transition.",
                ))

        # Add wind-down label and update start_time on all
        for wd in wind_down:
            wd.notes = f"🕯️ Wind-Down: {wd.notes}"

        messages.append(AgentMessage(
            sender="Wind-Down Planner",
            recipient="orchestrator",
            message_type="info",
            content=f"Designed wind-down routine starting {wind_down[0].start_time.strftime('%H:%M') if wind_down else 'N/A'} "
                    f"with {len(wind_down)} activities totaling "
                    f"{sum(w.duration_minutes for w in wind_down)} minutes.",
        ))

        return wind_down, messages

    def optimize_for_sleep_goal(self, wind_down: list[RoutineTask],
                                sleep_goal_hours: int = 8) -> list[AgentMessage]:
        """Optimize wind-down based on sleep duration goal."""
        messages = []
        total_min = sum(w.duration_minutes for w in wind_down)

        if total_min < 20:
            messages.append(AgentMessage(
                sender="Wind-Down Planner",
                recipient="orchestrator",
                message_type="adjustment",
                content=f"Wind-down is only {total_min}min. For optimal sleep, aim for 30-60min "
                        f"of low-stimulation activity before bed.",
            ))
        elif total_min > 90:
            messages.append(AgentMessage(
                sender="Wind-Down Planner",
                recipient="orchestrator",
                message_type="adjustment",
                content=f"Wind-down is {total_min}min — might be too long. "
                        f"Long wind-downs can cause 'tired but wired' from over-relaxation.",
            ))

        return messages