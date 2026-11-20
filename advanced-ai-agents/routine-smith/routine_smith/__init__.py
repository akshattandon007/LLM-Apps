"""RoutineSmith — Daily Routine Optimizer & Habit Architect.

5 specialized agents collaborate to design your ideal daily routine:
- Time Auditor: finds available time pockets
- Goal Aligner: translates goals to concrete tasks
- Habit Architect: designs habit stacks on existing cues
- Energy Matcher: places tasks in energy-optimal windows
- Wind-Down Planner: evening wind-down routine
"""

__version__ = "1.0.0"
__author__ = "RoutineSmith Team"

from .orchestrator import RoutineSmithOrchestrator
from .models import UserProfile, Goal, DailyRoutine, RoutineTask, GoalCategory

__all__ = [
    "RoutineSmithOrchestrator",
    "UserProfile", "Goal", "DailyRoutine", "RoutineTask", "GoalCategory",
]