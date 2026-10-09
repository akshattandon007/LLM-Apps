"""
Orchestrator — Coordinates the four agents in the LearnerLane pipeline.

Pipeline: SkillAssessor → CurriculumBuilder → ResourceHunter → PracticePlanner
Output: Complete learning plan with curriculum, resources, and practice tasks.
"""

from dataclasses import dataclass, field
from typing import Optional

from .agents.skill_assessor import SkillProfile, assess_skill, parse_goal_freeform
from .agents.curriculum_builder import Curriculum, build_curriculum, Module
from .agents.resource_hunter import Resource, ModuleResources, hunt_resources
from .agents.practice_planner import PracticePlan, PracticeTask, generate_plan


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class CompletePlan:
    profile: SkillProfile
    curriculum: Curriculum
    resources: list[ModuleResources]
    practice: PracticePlan
    mode: str = "simulated"  # "simulated" or "live"


@dataclass
class PipelineStatus:
    current_stage: str = "pending"
    stages_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return self.current_stage == "complete"


STAGE_NAMES = [
    "skill_assessment",
    "curriculum_design",
    "resource_hunting",
    "practice_planning",
]


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run_pipeline(
    topic: str = "",
    level: str = "",
    time_per_week: str = "",
    goal: str = "",
    mode: str = "simulated",
) -> CompletePlan:
    """Run the full LearnerLane pipeline.
    
    1. Skill Assessment — Understand what to learn and constraints
    2. Curriculum Design — Build progressive learning modules
    3. Resource Hunting — Find free resources for each module
    4. Practice Planning — Generate weekly exercises
    """
    status = PipelineStatus(current_stage="skill_assessment")
    errors: list[str] = []
    
    # Stage 1: Skill Assessment
    if goal and not topic:
        profile = parse_goal_freeform(goal)
    else:
        profile = assess_skill(topic=topic, level=level, time_per_week=time_per_week, goal=goal)
    status.stages_completed.append("skill_assessment")
    
    # Stop if no valid topic
    if not profile.is_valid:
        raise ValueError("No valid topic provided. Please specify what you want to learn.")
    
    # Stage 2: Curriculum Design
    status.current_stage = "curriculum_design"
    curriculum = build_curriculum(profile)
    status.stages_completed.append("curriculum_design")
    
    # Stage 3: Resource Hunting
    status.current_stage = "resource_hunting"
    module_resources: list[ModuleResources] = []
    for module in curriculum.modules:
        try:
            mr = hunt_resources(module, profile.topic)
            module_resources.append(mr)
        except Exception as e:
            errors.append(f"Resource hunting failed for '{module.title}': {e}")
            module_resources.append(ModuleResources(module_title=module.title, resources=[]))
    
    status.stages_completed.append("resource_hunting")
    
    # Stage 4: Practice Planning
    status.current_stage = "practice_planning"
    try:
        plan = generate_plan(curriculum, profile)
    except Exception as e:
        errors.append(f"Practice planning failed: {e}")
        plan = PracticePlan(tasks=[])
    status.stages_completed.append("practice_planning")
    
    status.current_stage = "complete"
    
    return CompletePlan(
        profile=profile,
        curriculum=curriculum,
        resources=module_resources,
        practice=plan,
        mode=mode,
    )


def format_plan(plan: CompletePlan) -> str:
    """Format a CompletePlan as a readable string."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  📚 LEARNERLANE — Learning Plan")
    lines.append(f"{'='*60}")
    lines.append(f"  Topic:          {plan.profile.topic}")
    lines.append(f"  Level:          {plan.profile.level}")
    lines.append(f"  Time/week:      {plan.profile.time_per_week} ({plan.profile.hours_per_week():.0f}h)")
    lines.append(f"  Goal:           {plan.profile.goal}")
    lines.append(f"  Mode:           {plan.mode}")
    lines.append(f"  Plan duration:  {plan.curriculum.total_weeks} weeks")
    lines.append(f"{'='*60}")
    lines.append("")
    
    # Curriculum
    lines.append("📋  CURRICULUM")
    lines.append("-" * 60)
    for module in plan.curriculum.modules:
        lines.append(f"")
        lines.append(f"  Week {module.week}: {module.title}")
        lines.append(f"  └─ {module.goal}")
        lines.append(f"  └─ (~{module.estimated_hours:.0f}h)")
        for topic in module.topics:
            lines.append(f"     • {topic}")
    
    lines.append("")
    lines.append("📖  FREE RESOURCES")
    lines.append("-" * 60)
    for mr in plan.resources:
        lines.append(f"")
        lines.append(f"  For: {mr.module_title}")
        for res in mr.resources:
            source_icon = {"wikipedia": "📖", "openlibrary": "📚", "web": "🌐"}.get(res.source, "🔗")
            type_label = res.resource_type.capitalize()
            lines.append(f"  {source_icon} [{type_label}] {res.title}")
            lines.append(f"     {res.url}")
            if res.description:
                lines.append(f"     {res.description}")
    
    lines.append("")
    lines.append("🎯  PRACTICE PLAN")
    lines.append("-" * 60)
    for task in plan.practice.tasks:
        type_icon = "🔨" if task.task_type == "project" else "✏️"
        lines.append(f"")
        lines.append(f"  Week {task.week}: {type_icon} {task.title}")
        lines.append(f"  └─ {task.description}")
        lines.append(f"  └─ (~{task.estimated_minutes} min)")
    
    lines.append("")
    lines.append(f"{'='*60}")
    lines.append(f"  Generated by LearnerLane — Multi-Agent Learning Curriculum Builder")
    lines.append(f"{'='*60}")
    
    return "\n".join(lines)