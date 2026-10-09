"""
Skill Assessor Agent — Conversational intake for learning goals.

Learns what the user wants to study, their current level, and time commitment.
Produces a structured skill profile used by the other agents.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

# ── Data structures ──────────────────────────────────────────────────────────

LEVELS = ["beginner", "dabbler", "intermediate"]
TIME_BUCKETS = ["<1 hour/week", "1-3 hours/week", "3-5 hours/week", "5+ hours/week"]
TIME_HOURS = {"<1 hour/week": 0.5, "1-3 hours/week": 2, "3-5 hours/week": 4, "5+ hours/week": 6}


@dataclass
class SkillProfile:
    topic: str
    level: str = "beginner"
    time_per_week: str = "1-3 hours/week"
    goal: str = ""

    def hours_per_week(self) -> float:
        return TIME_HOURS.get(self.time_per_week, 2)

    @property
    def is_valid(self) -> bool:
        return bool(self.topic.strip()) and self.level in LEVELS


# ── Intake engine (simulated — no LLM needed) ───────────────────────────────

DEFAULT_QUESTIONS = [
    ("What skill or topic do you want to learn?", "topic"),
    ("What's your current level?", "level"),
    ("How much time can you commit per week?", "time_per_week"),
    ("What's your main goal with this skill?", "goal"),
]

INSTRUCTIONS = """
=== SKILL ASSESSOR — Instructions ===
Role: Intake agent. You ask the user what they want to learn.
IN: Nothing (or a user's free-text goal)
OUT: SkillProfile with topic, level, time commitment, goal.

If the user provides a free-text goal upfront:
- Parse the goal to extract topic, level hints ("always wanted to try", "I know the basics")
- Default level to "beginner" if not mentioned
- Default time per week to "1-3 hours/week" if not mentioned
- Set goal = user's full text

If the goal is empty:
- Prompt the user with the questions above
- Infer missing info from context
"""


def assess_skill(topic: str = "", level: str = "", time_per_week: str = "", goal: str = "") -> SkillProfile:
    """Assess a skill based on user-provided information.
    
    Simulates the intake process. In production this would be LLM-driven.
    """
    # If given a plain topic without other info, infer defaults
    if topic and not level and not time_per_week and not goal:
        goal = f"I want to learn {topic}"
    
    # Normalise level
    level_lower = level.lower().strip() if level else "beginner"
    for lvl in LEVELS:
        if lvl in level_lower:
            level = lvl
            break
    if level not in LEVELS:
        level = "beginner"
    
    # Normalise time
    if time_per_week not in TIME_BUCKETS:
        for bucket in TIME_BUCKETS:
            if any(word in time_per_week.lower() for word in bucket.lower().split("/")[0].split("-")):
                time_per_week = bucket
                break
        if time_per_week not in TIME_BUCKETS:
            time_per_week = "1-3 hours/week"
    
    return SkillProfile(
        topic=topic.strip(),
        level=level,
        time_per_week=time_per_week,
        goal=goal.strip() or f"Learn {topic}",
    )


def parse_goal_freeform(text: str) -> SkillProfile:
    """Parse a free-form goal string into a SkillProfile.
    
    Heuristic-based parsing. In production, this would use an LLM.
    """
    text = text.strip()
    profile = SkillProfile(topic="", goal=text)
    
    # Try to extract level hints
    level_patterns = [
        (r"(?:complete|absolute|total)\s+beginner", "beginner"),
        (r"(?:bit of|some|basic|dabbled|tried before)", "dabbler"),
        (r"(?:intermediate|comfortable|decent|know my way around)", "intermediate"),
    ]
    for pattern, level in level_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            profile.level = level
            break
    
    # Try to extract topic — everything after "I want to learn" or "learn"
    # Stop at: "to" (new clause), "so" (purpose), comma, period, or end of string
    topic_match = re.search(
        r"(?:I want to learn|learn|study|get into|start)\s+(.+?)(?:\s+to\s|\s+so\s|[,.]|$)",
        text, re.IGNORECASE
    )
    if topic_match:
        profile.topic = topic_match.group(1).strip()
    
    # If no topic found, use the whole text (truncated)
    if not profile.topic:
        profile.topic = text[:60]
    
    return profile