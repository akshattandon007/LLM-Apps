"""Orchestrator — Coordinates the 5-agent pipeline to produce a daily routine.

Agent negotiation flow:
1. Time Auditor → schedule + pockets
2. Goal Aligner → goals → tasks (with Time Auditor negotiation on capacity)
3. Habit Architect → habit stacks (with Energy Matcher negotiation on placement)
4. Energy Matcher → energy-optimized placement (can veto Habit Architect placements)
5. Wind-Down Planner → evening routine

Each step produces AgentMessages to track inter-agent communication.
"""

from datetime import date, datetime
from typing import Optional

from .models import (
    UserProfile, Goal, GoalCategory, DailyRoutine, RoutineTask, AgentMessage,
)
from .agents.time_auditor import TimeAuditor
from .agents.goal_aligner import GoalAligner
from .agents.habit_architect import HabitArchitect
from .agents.energy_matcher import EnergyMatcher
from .agents.wind_down_planner import WindDownPlanner


class RoutineSmithOrchestrator:
    """Main orchestrator that runs the full multi-agent pipeline."""

    def __init__(self):
        self.time_auditor = TimeAuditor()
        self.goal_aligner = GoalAligner()
        self.habit_architect = HabitArchitect()
        self.energy_matcher = EnergyMatcher()
        self.wind_down_planner = WindDownPlanner()
        self.conversation_log: list[AgentMessage] = []
        self.vetoes: list[str] = []
        self.adjustments: list[str] = []
        self.profile: Optional[UserProfile] = None
        self.goals: list[Goal] = []

    def run_full_pipeline(self, quick_mode: bool = False) -> DailyRoutine:
        """Run the full 5-agent pipeline end-to-end."""
        # Step 1: Time Auditor
        print("\n" + "=" * 56)
        print("  RoutineSmith — Your Daily Routine Architect")
        print("  ⏰ Time Auditor | 🎯 Goal Aligner | 🧱 Habit Architect")
        print("  ⚡ Energy Matcher | 🕯️ Wind-Down Planner")
        print("=" * 56)

        if quick_mode:
            # Use defaults / demo mode
            self.profile = UserProfile()
            self.goals = self.goal_aligner._demo_goals()
        else:
            self.profile = self.time_auditor.collect_schedule()
            self.goals = self.goal_aligner.collect_goals()

        pockets, messages = self.time_auditor.audit(self.profile)
        self.conversation_log.extend(messages)

        print(f"  ⏰ Time Auditor: Found {len(pockets)} time pockets "
              f"({sum(p.duration_minutes for p in pockets)} free minutes)")

        # Step 2: Goal Aligner
        tasks, messages = self.goal_aligner.goals_to_tasks(self.goals, pockets, self.profile)
        self.conversation_log.extend(messages)

        for msg in messages:
            if msg.message_type == "adjustment":
                self.adjustments.append(msg.content)

        print(f"  🎯 Goal Aligner: {len(self.goals)} goals → {len(tasks)} tasks")

        # Step 3: Habit Architect
        cues = self.habit_architect.identify_cues(self.profile)
        habits, messages = self.habit_architect.design_habit_stacks(self.goals, self.profile, cues)
        self.conversation_log.extend(messages)

        # Merge habits into tasks (habits replace the base task for that goal)
        tasks = self._merge_habits(tasks, habits)

        print(f"  🧱 Habit Architect: {len(habits)} habit stacks designed")

        # Step 4: Energy Matcher
        matched_tasks, messages = self.energy_matcher.match_all_tasks(tasks, pockets, self.profile)
        self.conversation_log.extend(messages)

        for msg in messages:
            if msg.message_type == "veto":
                self.vetoes.append(msg.content)

        print(f"  ⚡ Energy Matcher: {len(matched_tasks)} tasks placed in optimal energy windows")

        # Step 5: Wind-Down Planner
        wind_down, messages = self.wind_down_planner.design_wind_down(self.profile, self.goals, matched_tasks)
        self.conversation_log.extend(messages)

        # Place wind-down tasks in the bedtime pocket
        bedtime_pocket = next((p for p in pockets if p.label == "Bedtime Wind-Down"), None)
        if bedtime_pocket:
            for wd in wind_down:
                if wd.start_time < bedtime_pocket.start:
                    wd.start_time = bedtime_pocket.start

        all_tasks = matched_tasks + wind_down

        print(f"  🕯️ Wind-Down Planner: {len(wind_down)} wind-down activities")
        print()

        # Compile the routine
        total_avail = sum(p.duration_minutes for p in pockets)
        total_used = sum(t.duration_minutes for t in all_tasks)
        score = self._calculate_score(all_tasks, self.goals)

        routine = DailyRoutine(
            date=date.today().isoformat(),
            tasks=sorted(all_tasks, key=lambda t: (t.start_time.hour, t.start_time.minute)),
            total_used_minutes=total_used,
            total_available_minutes=total_avail,
            score=score,
            vetoes=self.vetoes,
            adjustments=self.adjustments,
        )

        return routine

    def _merge_habits(self, tasks: list[RoutineTask], habits: list[RoutineTask]) -> list[RoutineTask]:
        """Merge habit stacks into the task list, replacing tasks when habit stacks exist for the same goal."""
        habit_goal_refs = {h.goal_ref for h in habits if h.goal_ref}
        result = []
        for task in tasks:
            if task.goal_ref in habit_goal_refs:
                # Replace with habit version
                matching_habits = [h for h in habits if h.goal_ref == task.goal_ref]
                result.extend(matching_habits)
            else:
                result.append(task)
        # Add any habits whose goal_ref wasn't in tasks
        result.extend(h for h in habits if h.goal_ref not in {t.goal_ref for t in tasks})
        return result

    def _calculate_score(self, tasks: list[RoutineTask], goals: list[Goal]) -> float:
        """Calculate a health/balance score for the routine (0-100)."""
        if not tasks:
            return 0.0

        score = 50.0  # Start at midpoint

        # + for goal coverage
        goal_categories_covered = set(t.category.value for t in tasks)
        score += len(goal_categories_covered) * 5

        # + for habit stacking
        habit_count = sum(1 for t in tasks if t.is_habit_stack)
        score += min(habit_count * 3, 15)

        # - for too many tasks (overwhelm)
        if len(tasks) > 15:
            score -= (len(tasks) - 15) * 2

        # - for gaps (no wind-down)
        has_wind_down = any("Wind-Down" in t.notes for t in tasks)
        if not has_wind_down:
            score -= 10

        # Check for balance
        categories = set(t.category for t in tasks)
        if GoalCategory.FITNESS in categories and GoalCategory.MINDFULNESS in categories:
            score += 5  # Balanced mind + body
        if GoalCategory.LEARNING in categories and GoalCategory.CREATIVE in categories:
            score += 3  # Input + output balance

        return max(0, min(100, score))

    def show_routine(self, routine: DailyRoutine):
        """Display the daily routine in a human-readable format."""
        print(f"\n  {'─' * 50}")
        print(f"  🌅 Your Daily Routine — {routine.date}")
        print(f"  {'─' * 50}")

        prev_hour = -1
        for task in routine.tasks:
            hour = task.start_time.hour
            if hour != prev_hour:
                # Print time header
                am_pm = "AM" if hour < 12 else "PM"
                display_hour = hour if hour <= 12 else hour - 12
                print(f"\n  ⏰ {display_hour}:00 {am_pm}")
                prev_hour = hour

            icon = self._category_icon(task.category)
            stack_marker = " 🔗" if task.is_habit_stack else ""
            cue_note = f" (after {task.cue_trigger})" if task.cue_trigger else ""
            print(f"  {icon} {task.start_time.strftime('%H:%M')} — {task.label} ({task.duration_minutes}min){stack_marker}{cue_note}")
            if task.notes:
                print(f"     💬 {task.notes[:120]}")

        print(f"\n  {'─' * 50}")
        print(f"  📊 Score: {routine.score:.0f}/100")
        print(f"  ⏱  {routine.total_used_minutes} min used of {routine.total_available_minutes} min available"
              f" ({routine.total_used_minutes / routine.total_available_minutes * 100:.0f}% utilization)")

        if self.vetoes:
            print(f"  🚫 {len(self.vetoes)} vetoes recorded")
        if self.adjustments:
            print(f"  🔧 {len(self.adjustments)} adjustments made")

        print(f"  {'─' * 50}")

        # Show implementation intentions
        print(f"\n  📋 Your Implementation Intentions (read aloud):")
        for task in routine.tasks[:5]:  # Top 5
            if task.cue_trigger:
                print(f"    • When {task.cue_trigger}, I will {task.label}.")
            else:
                print(f"    • At {task.start_time.strftime('%H:%M')}, I will {task.label}.")

        print()

    def _category_icon(self, category) -> str:
        import sys
        icons = {
            "fitness": "💪",
            "learning": "📚",
            "nutrition": "🥗",
            "mindfulness": "🧘",
            "productivity": "📋",
            "social": "👥",
            "creative": "🎨",
            "sleep": "😴",
            "finance": "💰",
            "other": "📌",
        }
        return icons.get(category.value if hasattr(category, 'value') else str(category), "📌")

    def show_negotiation_log(self):
        """Display the inter-agent negotiation log."""
        print(f"\n  📋 Agent Negotiation Log ({len(self.conversation_log)} messages):")
        for msg in self.conversation_log:
            direction = f"{msg.sender} → {msg.recipient}"
            msg_type_icon = {
                "proposal": "💡",
                "veto": "🚫",
                "adjustment": "🔧",
                "info": "ℹ️",
            }.get(msg.message_type, "📨")
            print(f"  {msg_type_icon} {direction}: {msg.content[:150]}")

    def log_completion(self, task_label: str, routine: DailyRoutine) -> Optional[str]:
        """Log that a task was completed, returning an adjustment message if appropriate."""
        for task in routine.tasks:
            if task.label == task_label and not task.completed:
                task.completed = True
                return f"✅ Marked '{task_label}' as done!"
        return None

    def generate_report(self, routine: DailyRoutine) -> str:
        """Generate a plain-text report for end-of-day."""
        lines = []
        lines.append(f"RoutineSmith — Daily Report for {routine.date}")
        lines.append(f"{'─' * 40}")
        lines.append(f"Score: {routine.score:.0f}/100")
        lines.append(f"Tasks planned: {len(routine.tasks)}")
        lines.append(f"Time used: {routine.total_used_minutes} min")
        lines.append(f"Categories covered: {len(set(t.category.value for t in routine.tasks))}")
        lines.append(f"Agents consulted: 5")
        lines.append(f"Vetoes: {len(self.vetoes)}")
        lines.append(f"Adjustments: {len(self.adjustments)}")
        return "\n".join(lines)