"""Goal Aligner Agent — Translates user goals into concrete routine tasks.

Responsibilities:
- Collect goals from the user (or use demo goals)
- Categorize and prioritize goals
- Translate goals to concrete tasks with frequency/duration
- Negotiate with Time Auditor when goals exceed available time
"""

from typing import Optional

from ..models import (
    UserProfile, Goal, GoalCategory, TaskEnergyLevel, Urgency,
    RoutineTask, AgentMessage, TimePocket,
)


class GoalAligner:
    """Translates user aspirations into structured, schedule-ready tasks."""

    def __init__(self):
        self.name = "Goal Aligner"

    def collect_goals(self) -> list[Goal]:
        """Interactively collect goals from the user."""
        goals: list[Goal] = []
        print("\n=== Goal Aligner: What Do You Want to Improve? ===")
        print("Enter goals one at a time (empty line to finish).")
        print("Examples: 'exercise more', 'read 20 min daily', 'learn Spanish'")

        while True:
            desc = input("  Goal: ").strip()
            if not desc:
                if not goals:
                    print("  Let me add some demo goals to show you how it works.")
                    goals = self._demo_goals()
                break

            print("  Categories: fitness, learning, nutrition, mindfulness, productivity, social, creative, sleep, finance")
            cat_str = input(f"  Category [{self._guess_category(desc)}]: ").strip().lower() or self._guess_category(desc)
            try:
                cat = GoalCategory(cat_str)
            except ValueError:
                cat = GoalCategory.OTHER

            freq = input("  Frequency (daily / weekly_N / weekdays / weekends) [daily]: ").strip() or "daily"

            dur_str = input("  Minutes per session [15]: ").strip()
            dur = int(dur_str) if dur_str.isdigit() else 15

            energy_str = input("  Energy needed (high/medium/low) [medium]: ").strip().lower() or "medium"
            try:
                energy = TaskEnergyLevel(energy_str)
            except ValueError:
                energy = TaskEnergyLevel.MEDIUM

            urg_str = input("  Urgency (critical/important/nice/flexible) [nice]: ").strip().lower() or "nice"
            try:
                urg = Urgency(urg_str)
            except ValueError:
                urg = Urgency.NICE

            goals.append(Goal(
                description=desc,
                category=cat,
                frequency=freq,
                duration_per_session_minutes=dur,
                energy_required=energy,
                urgency=urg,
            ))
            print(f"  ✅ Added: {desc}\n")

        return goals

    def _guess_category(self, desc: str) -> str:
        """Guess a goal category from keywords."""
        d = desc.lower()
        if any(w in d for w in ("exercise", "gym", "run", "walk", "workout", "stretch", "yoga", "fitness", "sport")):
            return "fitness"
        if any(w in d for w in ("read", "learn", "study", "course", "practice", "skill", "language")):
            return "learning"
        if any(w in d for w in ("cook", "eat", "diet", "nutrition", "meal", "water", "healthy")):
            return "nutrition"
        if any(w in d for w in ("meditate", "meditation", "mindful", "breathe", "calm", "gratitude", "journal")):
            return "mindfulness"
        if any(w in d for w in ("work", "focus", "deep", "email", "plan", "organize", "priority")):
            return "productivity"
        if any(w in d for w in ("friend", "social", "call", "connect", "family", "date")):
            return "social"
        if any(w in d for w in ("draw", "write", "paint", "music", "creative", "hobby", "play", "instrument")):
            return "creative"
        if any(w in d for w in ("sleep", "bed", "wake", "rest", "nap")):
            return "sleep"
        return "other"

    def _demo_goals(self) -> list[Goal]:
        """Provide demo goals for a quick start."""
        return [
            Goal("Exercise for 20 minutes", GoalCategory.FITNESS, "daily", 20, TaskEnergyLevel.HIGH, Urgency.IMPORTANT),
            Goal("Read 15 pages of a book", GoalCategory.LEARNING, "daily", 15, TaskEnergyLevel.LOW, Urgency.NICE),
            Goal("Meditate for 10 minutes", GoalCategory.MINDFULNESS, "daily", 10, TaskEnergyLevel.LOW, Urgency.IMPORTANT),
            Goal("Work on side project", GoalCategory.CREATIVE, "weekly_3", 45, TaskEnergyLevel.HIGH, Urgency.NICE),
            Goal("Stretch for 5 minutes", GoalCategory.FITNESS, "daily", 5, TaskEnergyLevel.LOW, Urgency.IMPORTANT),
        ]

    def goals_to_tasks(self, goals: list[Goal], pockets: list[TimePocket],
                       profile: UserProfile) -> tuple[list[RoutineTask], list[AgentMessage]]:
        """Convert goals to concrete tasks that fit into available time pockets."""
        tasks: list[RoutineTask] = []
        messages: list[AgentMessage] = []
        total_avail = sum(p.duration_minutes for p in pockets)

        total_desired = sum(g.duration_per_session_minutes for g in goals)

        if total_desired > total_avail:
            messages.append(AgentMessage(
                sender="Goal Aligner",
                recipient="Time Auditor",
                message_type="adjustment",
                content=f"Goals require {total_desired}min but only {total_avail}min available. "
                        f"Will prioritize by urgency and reduce durations.",
            ))
            # Scale or drop flexible goals
            goals.sort(key=lambda g: (g.urgency.value, g.duration_per_session_minutes))
            adjusted_goals = []
            accumulated = 0
            for g in goals:
                if accumulated + g.duration_per_session_minutes <= total_avail:
                    adjusted_goals.append(g)
                    accumulated += g.duration_per_session_minutes
                elif g.urgency in (Urgency.CRITICAL, Urgency.IMPORTANT):
                    # Halve the duration
                    half = max(5, g.duration_per_session_minutes // 2)
                    if accumulated + half <= total_avail:
                        messages.append(AgentMessage(
                            sender="Goal Aligner",
                            recipient="orchestrator",
                            message_type="adjustment",
                            content=f"Reduced '{g.description}' from {g.duration_per_session_minutes}min to "
                                    f"{half}min to fit schedule.",
                        ))
                        g.duration_per_session_minutes = half
                        adjusted_goals.append(g)
                        accumulated += half
                else:
                    messages.append(AgentMessage(
                        sender="Goal Aligner",
                        recipient="orchestrator",
                        message_type="adjustment",
                        content=f"Dropped '{g.description}' — not enough time ({g.duration_per_session_minutes}min needed).",
                    ))
            goals = adjusted_goals

        for g in goals:
            # Determine which pocket this goal best fits in based on energy requirement
            best_pocket = self._find_best_pocket(g, pockets, profile)

            pocket_label = best_pocket.label if best_pocket else "Unallocated"

            tasks.append(RoutineTask(
                label=f"{g.description}",
                goal_ref=g.description,
                start_time=best_pocket.start if best_pocket else profile.wake_time,
                duration_minutes=g.duration_per_session_minutes,
                energy_level=g.energy_required,
                category=g.category,
                notes=f"Frequency: {g.frequency} | Urgency: {g.urgency.value} | Allocated to: {pocket_label}",
            ))

        messages.append(AgentMessage(
            sender="Goal Aligner",
            recipient="orchestrator",
            message_type="info",
            content=f"Converted {len(goals)} goals into {len(tasks)} concrete tasks. "
                    f"Total required: {sum(t.duration_minutes for t in tasks)} minutes.",
        ))

        return tasks, messages

    def _find_best_pocket(self, goal: Goal, pockets: list[TimePocket],
                          profile: UserProfile) -> Optional[TimePocket]:
        """Find the best time pocket for a goal based on energy requirements."""
        if not pockets:
            return None

        # High energy tasks → high energy pockets
        # Low energy tasks → low energy pockets
        if goal.energy_required == TaskEnergyLevel.HIGH:
            candidates = [p for p in pockets if p.typical_energy.value == profile.energy_pattern.value
                          or p.duration_minutes >= goal.duration_per_session_minutes]
        elif goal.energy_required == TaskEnergyLevel.LOW:
            candidates = sorted(pockets, key=lambda p: p.duration_minutes)
        else:
            candidates = sorted(pockets, key=lambda p: p.duration_minutes, reverse=True)

        # Find the first candidate big enough
        for c in candidates:
            if c.duration_minutes >= goal.duration_per_session_minutes * 0.8:
                return c

        # Fallback: largest pocket
        return max(pockets, key=lambda p: p.duration_minutes)