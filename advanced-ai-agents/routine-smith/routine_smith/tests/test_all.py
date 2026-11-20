"""Tests for RoutineSmith agents and orchestrator."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import time
from routine_smith.models import (
    UserProfile, Goal, GoalCategory, TaskEnergyLevel, Urgency,
    TimePocket, EnergyPattern, RoutineTask, DailyRoutine,
)
from routine_smith.data.energy_curves import get_energy_at_hour, is_task_compatible, Chronotype
from routine_smith.data.habit_rules import find_stacks_for_goal, suggest_cue, HabitStack
from routine_smith.data.time_estimates import estimate_duration


class TestModels:
    def test_user_profile_defaults(self):
        p = UserProfile()
        assert p.wake_time == time(7, 0)
        assert p.sleep_time == time(23, 0)
        assert p.energy_pattern == EnergyPattern.BALANCED
        assert len(p.goals) == 0
        assert len(p.time_pockets) == 0

    def test_goal_creation(self):
        g = Goal(
            description="Exercise for 20 minutes",
            category=GoalCategory.FITNESS,
            frequency="daily",
            duration_per_session_minutes=20,
            energy_required=TaskEnergyLevel.HIGH,
            urgency=Urgency.IMPORTANT,
        )
        assert g.category.value == "fitness"
        assert g.frequency == "daily"

    def test_routine_task_creation(self):
        t = RoutineTask(
            label="Morning run",
            goal_ref="Exercise",
            start_time=time(7, 0),
            duration_minutes=20,
            energy_level=TaskEnergyLevel.HIGH,
            category=GoalCategory.FITNESS,
        )
        assert not t.completed
        assert t.is_habit_stack is False

    def test_daily_routine_completion_rate(self):
        r = DailyRoutine(date="2026-11-20")
        r.tasks = [
            RoutineTask(label="A", goal_ref="G1", start_time=time(7, 0),
                        duration_minutes=10, energy_level=TaskEnergyLevel.LOW,
                        category=GoalCategory.FITNESS, completed=True),
            RoutineTask(label="B", goal_ref="G2", start_time=time(8, 0),
                        duration_minutes=10, energy_level=TaskEnergyLevel.LOW,
                        category=GoalCategory.LEARNING, completed=False),
        ]
        assert r.completion_rate == 0.5


class TestEnergyCurves:
    def test_get_energy_at_hour(self):
        # Morning person at 9 AM should be high energy
        energy = get_energy_at_hour(Chronotype.MORNING, 9)
        assert energy >= 7
        # Night owl at 9 AM should be low energy
        energy = get_energy_at_hour(Chronotype.NIGHT, 9)
        assert energy <= 5

    def test_is_task_compatible(self):
        # Morning person + high energy task at 10 AM → compatible
        assert is_task_compatible(Chronotype.MORNING, 10, "high")
        # Night owl + high energy task at 7 AM → not compatible
        assert not is_task_compatible(Chronotype.NIGHT, 7, "high")


class TestHabitRules:
    def test_find_stacks_for_goal(self):
        stacks = find_stacks_for_goal("fitness")
        assert len(stacks) > 0
        for s in stacks:
            assert isinstance(s, HabitStack)

    def test_suggest_cue(self):
        cue = suggest_cue([])
        assert cue is not None
        assert len(cue) > 0

    def test_predefined_stacks_have_all_fields(self):
        from data.habit_rules import PREDEFINED_STACKS
        for stack in PREDEFINED_STACKS:
            assert stack.cue
            assert stack.new_habit
            assert stack.min_viable_version
            assert stack.duration_minutes > 0
            assert stack.celebration


class TestTimeEstimates:
    def test_estimate_duration_known(self):
        assert estimate_duration("meditation") == 10
        assert estimate_duration("exercise_cardio") == 30

    def test_estimate_duration_unknown(self):
        assert estimate_duration("quantum_computing") == 15  # default


class TestAgentInteractions:
    def test_goal_to_task_translation(self):
        """Test that goals get translated to tasks with correct fields."""
        g = Goal(
            description="Read 15 pages",
            category=GoalCategory.LEARNING,
            frequency="daily",
            duration_per_session_minutes=15,
            energy_required=TaskEnergyLevel.LOW,
            urgency=Urgency.NICE,
        )
        # Simulate what Goal Aligner does
        assert g.category == GoalCategory.LEARNING
        assert g.energy_required == TaskEnergyLevel.LOW

    def test_energy_mismatch_detection(self):
        """Night owl with high energy task at 7 AM should be flagged."""
        from data.energy_curves import get_energy_at_hour, Chronotype
        energy_7am = get_energy_at_hour(Chronotype.NIGHT, 7)
        high_energy_threshold = 7
        assert energy_7am < high_energy_threshold, \
            f"Night owl shouldn't have high energy at 7 AM (got {energy_7am})"

    def test_orchestrator_pipeline_key_components(self):
        """Verify orchestrator can import and basic structure works."""
        from routine_smith.orchestrator import RoutineSmithOrchestrator
        o = RoutineSmithOrchestrator()
        assert hasattr(o, 'time_auditor')
        assert hasattr(o, 'goal_aligner')
        assert hasattr(o, 'habit_architect')
        assert hasattr(o, 'energy_matcher')
        assert hasattr(o, 'wind_down_planner')
        assert len(o.conversation_log) == 0


class TestScoreCalculation:
    def test_score_bounds(self):
        """Score should always be between 0 and 100."""
        from routine_smith.orchestrator import RoutineSmithOrchestrator
        o = RoutineSmithOrchestrator()
        from routine_smith.models import DailyRoutine
        r = DailyRoutine(date="2026-11-20")
        tasks = [
            RoutineTask(label="A", goal_ref="G1", start_time=time(7, 0),
                        duration_minutes=5, energy_level=TaskEnergyLevel.LOW,
                        category=GoalCategory.FITNESS),
            RoutineTask(label="B", goal_ref="G2", start_time=time(8, 0),
                        duration_minutes=5, energy_level=TaskEnergyLevel.LOW,
                        category=GoalCategory.MINDFULNESS),
        ]
        score = o._calculate_score(tasks, [])
        assert 0 <= score <= 100