"""Smoke tests for HomeCourt.

These tests verify the core pipeline works end-to-end with simulated data.
No API key or network call is required.
"""

from src.court import run_simulated_demo
from src.jurors import render_verdict
from src.personas import PERSONAS, PERSONA_MAP, get_persona
from src.reporter import format_verdict
from src.models import Verdict


class TestPersonas:
    """Verify all personas are well-formed."""

    def test_all_personas_have_required_fields(self):
        """Every persona must have a key, name, emoji, tone, greeting, and prompt."""
        for p in PERSONAS:
            assert p.key.value
            assert p.name
            assert p.emoji
            assert p.tone
            assert p.greeting
            assert p.personality_prompt

    def test_all_personas_are_in_map(self):
        """PERSONA_MAP must cover every entry in PERSONAS."""
        for p in PERSONAS:
            assert p.key in PERSONA_MAP

    def test_persona_lookup_by_string(self):
        """get_persona() works with both enum and string."""
        p1 = get_persona("grouchy_grandma")
        p2 = get_persona("reality_tv_judge")
        assert p1.key.value == "grouchy_grandma"
        assert p2.key.value == "reality_tv_judge"


class TestJurors:
    """Verify verdict generation works in simulate mode."""

    def test_simulated_verdict_returns_verdict(self, sushi_vs_pizza):
        """Smoke test: simulated verdict returns a Verdict with required fields."""
        verdict = render_verdict(sushi_vs_pizza, "grouchy_grandma", mode="simulate")
        assert verdict.case_name == "Sushi vs Pizza"
        assert verdict.presiding_judge == "Grouchy Grandma"
        assert verdict.reasoning
        assert verdict.ruling
        assert verdict.date_issued

    def test_simulated_verdict_for_each_persona(self, sushi_vs_pizza, all_persona_keys):
        """Every persona can generate a simulated verdict without errors."""
        for key in all_persona_keys:
            verdict = render_verdict(sushi_vs_pizza, key, mode="simulate")
            assert verdict.reasoning
            assert verdict.ruling
            assert len(verdict.reasoning) > 20

    def test_different_cases_have_different_case_names(
        self, sushi_vs_pizza, text_mom_now_vs_later
    ):
        """Different cases produce verdicts with different case names."""
        v1 = render_verdict(sushi_vs_pizza, "zen_master", mode="simulate")
        v2 = render_verdict(text_mom_now_vs_later, "zen_master", mode="simulate")
        assert v1.case_name != v2.case_name


class TestReporter:
    """Verify verdict formatting."""

    def test_formatted_verdict_includes_header(self, sushi_vs_pizza):
        """Formatted output must include the HomeCourt header."""
        verdict = render_verdict(sushi_vs_pizza, "best_friend", mode="simulate")
        output = format_verdict(verdict)
        assert "HOMECOURT" in output
        assert "OFFICIAL VERDICT" in output

    def test_formatted_verdict_includes_case_name(self, sushi_vs_pizza):
        """Formatted output must include the case name."""
        verdict = render_verdict(sushi_vs_pizza, "strict_logic_ai", mode="simulate")
        output = format_verdict(verdict)
        assert "Sushi vs Pizza" in output

    def test_formatted_verdict_includes_judge(self, sushi_vs_pizza):
        """Formatted output must include the presiding judge name."""
        verdict = render_verdict(sushi_vs_pizza, "reality_tv_judge", mode="simulate")
        output = format_verdict(verdict)
        assert "Reality-TV Judge" in output

    def test_formatted_verdict_includes_ruling_banner(self, sushi_vs_pizza):
        """Ruling must be delimited by a RULING banner."""
        verdict = render_verdict(sushi_vs_pizza, "shakespearean", mode="simulate")
        output = format_verdict(verdict)
        assert "RULING" in output


class TestEndToEnd:
    """End-to-end smoke tests."""

    def test_simulated_demo_runs(self):
        """run_simulated_demo() returns a Verdict at the end."""
        verdict = run_simulated_demo()
        assert isinstance(verdict, Verdict)
        assert verdict.case_name
        assert verdict.ruling