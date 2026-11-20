"""Habit Architect Agent — Designs habit stacks and minimal-viable routines.

Responsibilities:
- Identify existing cues in the user's day
- Suggest habit stacks (piggyback new habits on existing ones)
- Apply behavioral design (2-minute rule, implementation intentions)
- Negotiate placements with Energy Matcher
"""

from typing import Optional

from ..models import UserProfile, Goal, RoutineTask, AgentMessage, TimePocket
from ..data.habit_rules import find_stacks_for_goal, suggest_cue, HabitStack, COMMON_CUES


class HabitArchitect:
    """Behavioral design agent that builds sustainable habits using psychology."""

    def __init__(self):
        self.name = "Habit Architect"

    def design_habit_stacks(self, goals: list[Goal], profile: UserProfile,
                            existing_routines: list[str] = None) -> tuple[list[RoutineTask], list[AgentMessage]]:
        """Design habit stacks — attaching new habits to existing cues."""
        habits: list[RoutineTask] = []
        messages: list[AgentMessage] = []

        if existing_routines is None:
            existing_routines = []

        for goal in goals:
            # Find relevant stacks for this goal category
            stacks = find_stacks_for_goal(goal.category.value)

            # Pick a stack that doesn't conflict with existing routines
            chosen: Optional[HabitStack] = None
            for stack in stacks:
                if stack.cue not in existing_routines:
                    chosen = stack
                    break

            if chosen:
                tasks_min = min(goal.duration_per_session_minutes, chosen.duration_minutes)
                habits.append(RoutineTask(
                    label=chosen.new_habit,
                    goal_ref=goal.description,
                    start_time=profile.wake_time,  # Will be placed properly later
                    duration_minutes=tasks_min,
                    energy_level=goal.energy_required,
                    category=goal.category,
                    is_habit_stack=True,
                    cue_trigger=chosen.cue,
                    notes=f"Stacked on '{chosen.cue}'. Min viable: '{chosen.min_viable_version}'. "
                          f"Celebration: {chosen.celebration}",
                ))
                existing_routines.append(chosen.cue)

                messages.append(AgentMessage(
                    sender="Habit Architect",
                    recipient="orchestrator",
                    message_type="proposal",
                    content=f"Stacked '{goal.description}' onto '{chosen.cue}'. "
                            f"Min viable version: {chosen.min_viable_version}. "
                            f"This makes the habit frictionless — just {tasks_min} minutes.",
                ))
            else:
                # Fallback: create a minimal-viable habit without a stack
                min_viable = f"Do {goal.description} for 2 minutes"
                habits.append(RoutineTask(
                    label=min_viable,
                    goal_ref=goal.description,
                    start_time=profile.wake_time,
                    duration_minutes=2,
                    energy_level=goal.energy_required,
                    category=goal.category,
                    is_habit_stack=True,
                    notes=f"Minimal viable version. Build up from here.",
                ))
                messages.append(AgentMessage(
                    sender="Habit Architect",
                    recipient="orchestrator",
                    message_type="proposal",
                    content=f"No existing cue found for '{goal.description}'. "
                            f"Starting with a 2-minute minimal viable version — "
                            f"easy to maintain, easy to scale up.",
                ))

        messages.append(AgentMessage(
            sender="Habit Architect",
            recipient="orchestrator",
            message_type="info",
            content=f"Designed {len(habits)} habit stacks. All start as 2-minute "
                    f"minimum viable habits to build consistency before intensity.",
        ))

        return habits, messages

    def suggest_implementation_intentions(self, habits: list[RoutineTask]) -> list[str]:
        """Generate implementation intention statements for each habit."""
        intentions = []
        for h in habits:
            if h.cue_trigger:
                intentions.append(
                    f"When {h.cue_trigger}, I will {h.label} for {h.duration_minutes} minutes."
                )
            else:
                intentions.append(
                    f"At {h.start_time.strftime('%H:%M')}, I will {h.label} for {h.duration_minutes} minutes."
                )
        return intentions

    def identify_cues(self, profile: UserProfile) -> list[str]:
        """Identify existing cues in the user's day based on their schedule."""
        cues = [
            "after waking up",
            "after brushing teeth",
        ]

        if profile.work_start:
            cues.append("after morning coffee")
            cues.append("after starting work")

        if profile.work_end:
            cues.append("after finishing work")
            cues.append("after walking through the front door")

        cues.extend([
            "after finishing dinner",
            "after brushing teeth at night",
            "after putting on pajamas",
        ])

        return cues