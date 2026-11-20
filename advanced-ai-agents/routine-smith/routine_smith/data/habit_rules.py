"""Habit formation rules based on behavioral psychology.

Implements principles from:
- Atomic Habits (James Clear) — habit stacking, 2-minute rule
- Tiny Habits (BJ Fogg) — minimum viable habit, celebration
- The Power of Habit (Charles Duhigg) — cue → routine → reward loop
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HabitStack:
    """A habit stacked onto an existing cue."""
    cue: str                    # Existing habit/event to piggyback on
    new_habit: str              # New habit to attach
    min_viable_version: str     # The 2-minute version
    duration_minutes: int
    celebration: str            # What to do after (tiny celebration)
    category: str = "general"


# Common existing cues that people have
COMMON_CUES = [
    "after morning coffee",
    "after brushing teeth in morning",
    "after getting out of bed",
    "after using the bathroom",
    "after closing laptop for the day",
    "after finishing dinner",
    "after brushing teeth at night",
    "after putting on pajamas",
    "after walking through the front door",
    "after sitting down at desk",
    "after checking phone first time",
    "after eating lunch",
    "after turning off alarm",
    "after putting kids to bed",
]

# Predefined habit stacks for common goals
PREDEFINED_STACKS: list[HabitStack] = [
    HabitStack(
        cue="after morning coffee",
        new_habit="plan the day's top 3 priorities",
        min_viable_version="write ONE thing you want to accomplish today",
        duration_minutes=2,
        celebration="sip your coffee — you've earned it",
        category="productivity",
    ),
    HabitStack(
        cue="after brushing teeth in morning",
        new_habit="do 2 minutes of stretching",
        min_viable_version="touch your toes once",
        duration_minutes=2,
        celebration="say 'good start' out loud",
        category="fitness",
    ),
    HabitStack(
        cue="after getting out of bed",
        new_habit="drink a glass of water",
        min_viable_version="take one sip from your nightstand glass",
        duration_minutes=1,
        celebration="acknowledge you hydrated",
        category="nutrition",
    ),
    HabitStack(
        cue="after closing laptop for the day",
        new_habit="5-minute tidy-up of workspace",
        min_viable_version="put one thing away",
        duration_minutes=5,
        celebration="close the door and take a breath",
        category="productivity",
    ),
    HabitStack(
        cue="after finishing dinner",
        new_habit="load dishes immediately",
        min_viable_version="carry one plate to the sink",
        duration_minutes=3,
        celebration="5 minutes of guilt-free phone time",
        category="productivity",
    ),
    HabitStack(
        cue="after brushing teeth at night",
        new_habit="write tomorrow's date and one priority",
        min_viable_version="write ONE word about tomorrow",
        duration_minutes=1,
        celebration="turn off the light and feel prepared",
        category="productivity",
    ),
    HabitStack(
        cue="after sitting down at desk",
        new_habit="set a timer for the first deep-work block",
        min_viable_version="click the pomodoro timer start",
        duration_minutes=1,
        celebration="take three deep breaths before beginning",
        category="productivity",
    ),
    HabitStack(
        cue="after walking through the front door",
        new_habit="put keys/phone in their designated spot",
        min_viable_version="place ONE item in its spot",
        duration_minutes=1,
        celebration="say 'I'm home and organized'",
        category="productivity",
    ),
    HabitStack(
        cue="after putting on pajamas",
        new_habit="read 5 pages of a book",
        min_viable_version="read ONE paragraph",
        duration_minutes=5,
        celebration="mark your page and feel accomplished",
        category="learning",
    ),
    HabitStack(
        cue="after turning off alarm",
        new_habit="sit up and take three deep breaths",
        min_viable_version="take ONE deep breath before checking phone",
        duration_minutes=1,
        celebration="smile — you chose to start the day intentionally",
        category="mindfulness",
    ),
]


def find_stacks_for_goal(goal_category: str) -> list[HabitStack]:
    """Find relevant habit stacks for a given goal category."""
    stacks = []
    for stack in PREDEFINED_STACKS:
        if stack.category == goal_category:
            stacks.append(stack)
        # Also include general stacks and productivity (most universal)
        if stack.category in ("general", "productivity"):
            stacks.append(stack)
    return stacks


def suggest_cue(user_routines: list[str]) -> Optional[str]:
    """Suggest a good cue based on the user's existing routines."""
    # Simple heuristic: recommend un-used common cues
    existing_set = set(r.lower() for r in user_routines)
    for cue in COMMON_CUES:
        if cue not in existing_set:
            return cue
    return COMMON_CUES[0] if COMMON_CUES else None