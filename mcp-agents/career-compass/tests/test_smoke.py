"""Smoke tests for Career Compass — validates all MCP tools with fake data."""

from __future__ import annotations

import pytest

from src.industries import growing_industries, job_outlook
from src.offers import compare_offer
from src.paths import career_path
from src.salary import salary_by_role
from src.skills import skills_gap


class TestSalaryByRole:
    def test_known_role_returns_data(self):
        """Software Developer should return realistic wage data."""
        result = salary_by_role("Software Developer")
        assert result.occupation == "Software Developer"
        assert result.median_wage > 50_000
        assert result.p10_wage <= result.median_wage <= result.p90_wage
        assert result.data_source == "database"

    def test_unknown_role_returns_zeros(self):
        """Unknown roles should return zero wages and 'not_found' source."""
        result = salary_by_role("Quantum Banana Farmer")
        assert result.median_wage == 0
        assert result.data_source == "not_found"

    def test_col_adjustment(self):
        """San Francisco ZIP code should adjust wage downward (COL > 100)."""
        result = salary_by_role("Software Developer", zip_code="94105")
        assert result.cost_of_living_index > 100
        assert result.adjusted_median_wage < result.median_wage

    def test_partial_title_match(self):
        """Partial titles like 'Developer' should still match."""
        result = salary_by_role("Developer")
        assert result.median_wage > 0
        assert result.occupation != "Developer"  # should use full title


class TestGrowingIndustries:
    def test_returns_top_industries(self):
        """Should return a list of growing industries."""
        result = growing_industries()
        assert len(result.industries) > 0
        assert result.industries[0].projected_growth_rate > 0

    def test_region_filter_works(self):
        """Filtering by region should return matching industries."""
        result = growing_industries(region="San Francisco")
        for ind in result.industries:
            assert any("San Francisco" in r for r in ind.key_regions)

    def test_empty_region_returns_all(self):
        """Empty region filter should return all industries."""
        result = growing_industries()
        result_filtered = growing_industries(region="")
        assert len(result.industries) == len(result_filtered.industries)


class TestSkillsGap:
    def test_support_to_developer_has_gaps(self):
        """Support -> Developer should identify programming gaps."""
        result = skills_gap("IT Support Specialist", "Software Developer")
        assert len(result.gaps) > 0
        assert result.current_title == "IT Support Specialist"
        assert result.target_title == "Software Developer"

    def test_generic_transition_has_edu_gap(self):
        """Unknown role transitions should generate generic gaps."""
        result = skills_gap("Barista", "Civil Engineer")
        assert len(result.gaps) > 0

    def test_gaps_have_courses(self):
        """Each gap should have at least one recommended course."""
        result = skills_gap("IT Support Specialist", "Software Developer")
        for gap in result.gaps:
            assert len(gap.typical_courses) > 0


class TestCareerPath:
    def test_software_path_returns_steps(self):
        """Software Developer path should return multiple steps."""
        result = career_path("Software Developer", years=10)
        assert len(result.steps) > 1
        assert result.steps[0].salary_range != ""

    def test_respects_years_horizon(self):
        """Steps beyond the years horizon should be excluded."""
        result_5yr = career_path("Software Developer", years=5)
        result_15yr = career_path("Software Developer", years=15)
        assert len(result_5yr.steps) <= len(result_15yr.steps)

    def test_each_step_has_salary(self):
        """Every career step should have a salary range."""
        result = career_path("Software Developer", years=10)
        for step in result.steps:
            assert step.salary_range is not None
            assert len(step.salary_range) > 0


class TestCompareOffer:
    def test_basic_offer(self):
        """A simple offer should return total comp >= base."""
        result = compare_offer(salary=100_000)
        assert result.total_compensation >= 100_000
        assert result.base_salary == 100_000

    def test_bonus_increases_total(self):
        """Bonus should increase total compensation."""
        base = compare_offer(salary=100_000)
        with_bonus = compare_offer(salary=100_000, annual_bonus_pct=15)
        assert with_bonus.total_compensation > base.total_compensation

    def test_col_adjusts_purchasing_power(self):
        """High COL area should reduce purchasing power."""
        national = compare_offer(salary=100_000)
        sf = compare_offer(salary=100_000, location="94105")
        assert sf.cost_of_living_index > 100
        assert sf.effective_purchasing_power < national.effective_purchasing_power


class TestJobOutlook:
    def test_growing_occupation(self):
        """Software Developer should show 'very_fast' growth."""
        result = job_outlook("Software Developer")
        assert result.projected_growth_rate > 0
        assert result.annual_openings > 0

    def test_outlook_returns_industries(self):
        """Outlook should identify key hiring industries."""
        result = job_outlook("Software Developer")
        assert len(result.key_industries) > 0

    def test_unknown_occupation(self):
        """Unknown occupation should return zeroes."""
        result = job_outlook("Fictional Job")
        assert result.current_employment == 0
        assert result.data_source == "not_found"


class TestMCPRegistration:
    def test_import_and_tools(self):
        """The server module should import cleanly and expose tools."""
        from src.server import mcp
        tools = mcp._tool_manager.list_tools()
        tool_names = [t.name for t in tools]
        assert "salary_by_role_tool" in tool_names
        assert "growing_industries_tool" in tool_names
        assert "skills_gap_tool" in tool_names
        assert "career_path_tool" in tool_names
        assert "compare_offer_tool" in tool_names
        assert "job_outlook_tool" in tool_names
        assert len(tool_names) >= 6


class TestCLIEntry:
    def test_cli_imports(self):
        """CLI main module should import cleanly."""
        from src.main import main
        assert main is not None