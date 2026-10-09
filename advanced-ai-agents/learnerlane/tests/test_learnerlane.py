"""
Tests for LearnerLane multi-agent learning curriculum builder.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from learnerlane.agents.skill_assessor import (
    assess_skill, parse_goal_freeform, SkillProfile
)
from learnerlane.agents.curriculum_builder import (
    build_curriculum, Curriculum, Module
)
from learnerlane.agents.resource_hunter import (
    ModuleResources, search_wikipedia, search_open_library,
    search_web_fallback, hunt_resources
)
from learnerlane.agents.practice_planner import (
    generate_plan, PracticePlan, PracticeTask
)
from learnerlane.orchestrator import (
    run_pipeline, format_plan, CompletePlan
)


class TestSkillAssessor:
    def test_default_assessment(self):
        profile = assess_skill(topic="photography")
        assert profile.topic == "photography"
        assert profile.level == "beginner"
        assert profile.time_per_week == "1-3 hours/week"
        assert profile.is_valid

    def test_full_assessment(self):
        profile = assess_skill(
            topic="guitar",
            level="intermediate",
            time_per_week="3-5 hours/week",
            goal="Master fingerstyle guitar"
        )
        assert profile.topic == "guitar"
        assert profile.level == "intermediate"
        assert profile.hours_per_week() == 4

    def test_freeform_parsing(self):
        profile = parse_goal_freeform("I want to learn photography to take better travel photos")
        assert profile.topic == "photography"
        assert profile.goal == "I want to learn photography to take better travel photos"
        assert profile.is_valid

    def test_freeform_with_level(self):
        profile = parse_goal_freeform("I'm a complete beginner wanting to learn python")
        assert "python" in profile.topic.lower()
        assert profile.level == "beginner"

    def test_freeform_intermediate(self):
        profile = parse_goal_freeform("I know my way around a guitar, want to learn fingerstyle")
        assert profile.level == "intermediate"

    def test_invalid_profile(self):
        profile = SkillProfile(topic="", level="")
        assert not profile.is_valid


class TestCurriculumBuilder:
    def test_photography_curriculum(self):
        profile = SkillProfile(topic="photography", level="beginner")
        curriculum = build_curriculum(profile)
        assert curriculum.topic == "photography"
        assert len(curriculum.modules) >= 4
        assert curriculum.is_valid

    def test_guitar_curriculum(self):
        profile = SkillProfile(topic="guitar", level="beginner")
        curriculum = build_curriculum(profile)
        assert curriculum.topic == "guitar"
        assert len(curriculum.modules) >= 4

    def test_python_curriculum(self):
        profile = SkillProfile(topic="python", level="dabbler")
        curriculum = build_curriculum(profile)
        assert curriculum.topic == "python"
        assert len(curriculum.modules) >= 4

    def test_generic_topic(self):
        profile = SkillProfile(topic="chess", level="beginner")
        curriculum = build_curriculum(profile)
        assert curriculum.topic == "chess"
        assert curriculum.is_valid
        # Generic topic should use the GENERIC_MODULES template
        assert len(curriculum.modules) >= 3

    def test_module_structure(self):
        profile = SkillProfile(topic="photography", level="beginner")
        curriculum = build_curriculum(profile)
        for i, mod in enumerate(curriculum.modules):
            assert mod.week == i + 1
            assert mod.title
            assert mod.goal
            assert len(mod.topics) > 0

    def test_beginner_less_time_fewer_modules(self):
        profile = SkillProfile(topic="photography", level="beginner", time_per_week="<1 hour/week")
        curriculum = build_curriculum(profile)
        # Should have fewer modules
        profile2 = SkillProfile(topic="photography", level="intermediate", time_per_week="5+ hours/week")
        curriculum2 = build_curriculum(profile2)
        assert len(curriculum.modules) <= len(curriculum2.modules)

    def test_empty_modules_shows_as_invalid(self):
        curriculum = Curriculum(topic="empty", modules=[])
        assert not curriculum.is_valid


class TestResourceHunter:
    def test_module_resources_data_class(self):
        mr = ModuleResources(module_title="Test Module", resources=[])
        assert mr.module_title == "Test Module"
        assert len(mr.resources) == 0

    def test_search_wikipedia_no_network(self):
        """Wikipedia search should not crash without network."""
        import httpx
        from learnerlane.agents.resource_hunter import set_client
        # Inject a client that returns empty
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"query": {"search": []}}))
        set_client(httpx.Client(transport=transport))
        results = search_wikipedia("test query", limit=2)
        assert isinstance(results, list)
        # Reset
        set_client(None)

    def test_web_fallback_generates_urls(self):
        results = search_web_fallback("python tutorials")
        assert len(results) >= 2
        # Should have YouTube and Google URLs
        assert any("youtube.com" in r.url for r in results)
        assert any("google.com" in r.url for r in results)
        # URLs should be properly encoded
        assert "%20" in results[0].url or "+" in results[0].url


class TestPracticePlanner:
    def test_generate_plan_for_photography(self):
        profile = SkillProfile(topic="photography", level="beginner")
        curriculum = build_curriculum(profile)
        plan = generate_plan(curriculum, profile)
        assert len(plan.tasks) == len(curriculum.modules)
        for task in plan.tasks:
            assert task.title
            assert task.description
            assert task.estimated_minutes > 0
            assert task.task_type in ("exercise", "project")

    def test_generic_plan(self):
        profile = SkillProfile(topic="chess", level="beginner")
        curriculum = build_curriculum(profile)
        plan = generate_plan(curriculum, profile)
        assert len(plan.tasks) > 0
        assert all(t.description for t in plan.tasks)

    def test_plan_includes_projects(self):
        profile = SkillProfile(topic="photography", level="beginner")
        curriculum = build_curriculum(profile)
        plan = generate_plan(curriculum, profile)
        # At least the capstone should be a project
        assert any(t.task_type == "project" for t in plan.tasks)


class TestOrchestrator:
    def test_full_pipeline_topic_only(self):
        import httpx
        from learnerlane.agents.resource_hunter import set_client as rh_set_client
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"query": {"search": []}}))
        rh_set_client(httpx.Client(transport=transport))
        plan = run_pipeline(topic="photography", mode="simulated")
        assert isinstance(plan, CompletePlan)
        assert plan.profile.topic == "photography"
        assert plan.curriculum.is_valid
        assert len(plan.curriculum.modules) >= 4
        assert len(plan.resources) == len(plan.curriculum.modules)
        assert len(plan.practice.tasks) == len(plan.curriculum.modules)

    def test_full_pipeline_with_goal(self):
        import httpx
        from learnerlane.agents.resource_hunter import set_client as rh_set_client
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"query": {"search": []}}))
        rh_set_client(httpx.Client(transport=transport))
        plan = run_pipeline(
            goal="I want to learn guitar to play around the campfire",
            mode="simulated"
        )
        assert "guitar" in plan.profile.topic.lower()
        assert plan.curriculum.is_valid

    def test_pipeline_multiple_topics(self):
        import httpx
        from learnerlane.agents.resource_hunter import set_client as rh_set_client
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"query": {"search": []}}))
        rh_set_client(httpx.Client(transport=transport))
        for topic in ["photography", "guitar", "python", "baking", "gardening"]:
            plan = run_pipeline(topic=topic, mode="simulated")
            assert plan.curriculum.is_valid
            assert plan.profile.topic.lower() == topic
            assert len(plan.curriculum.modules) >= 4
        rh_set_client(None)

    def test_format_plan_output(self):
        import httpx
        from learnerlane.agents.resource_hunter import set_client as rh_set_client
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"query": {"search": []}}))
        rh_set_client(httpx.Client(transport=transport))
        plan = run_pipeline(topic="photography", mode="simulated")
        output = format_plan(plan)
        assert "LEARNERLANE" in output
        assert "photography" in output.lower()
        assert "CURRICULUM" in output
        assert "FREE RESOURCES" in output
        assert "PRACTICE PLAN" in output


class TestEdgeCases:
    def test_empty_topic_raises(self):
        with pytest.raises(ValueError):
            run_pipeline(topic="", mode="simulated")

    def test_demo_topics_are_supported(self):
        import httpx
        from learnerlane.agents.resource_hunter import set_client as rh_set_client
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"query": {"search": []}}))
        rh_set_client(httpx.Client(transport=transport))
        topics = ["photography", "guitar", "baking", "gardening", "python"]
        for t in topics:
            plan = run_pipeline(topic=t, mode="simulated")
            assert plan.curriculum.is_valid
            assert len(plan.curriculum.modules) >= 3

    def test_mode_flag_preserved(self):
        plan = run_pipeline(topic="test", mode="simulated")
        assert plan.mode == "simulated"