"""PyTest fixtures for Career Compass tests."""

from __future__ import annotations

import pytest

from src.models import (
    CareerPathResult,
    CareerStep,
    CostOfLiving,
    DegreeLevel,
    GrowthOutlook,
    IndustryOutlook,
    IndustryResult,
    Occupation,
    OfferComparisonResult,
    SalaryResult,
    SkillGap,
    SkillsGapResult,
)


@pytest.fixture
def sample_occupation() -> Occupation:
    return Occupation(
        soc_code="15-1252",
        title="Software Developer",
        median_wage=130_160,
        p10_wage=74_000,
        p90_wage=208_000,
        typical_education=DegreeLevel.BACHELORS,
        experience_years=2,
        growth_rate=0.25,
        openings_year=162_900,
        description="Develop applications software.",
    )


@pytest.fixture
def sample_col() -> CostOfLiving:
    return CostOfLiving(
        zip_code="94105",
        city="San Francisco",
        state="CA",
        index=180.0,
        housing_index=250.0,
        groceries_index=120.0,
        transportation_index=135.0,
        utilities_index=118.0,
    )


@pytest.fixture
def sample_salary_result() -> SalaryResult:
    return SalaryResult(
        occupation="Software Developer",
        zip_code="94105",
        median_wage=130_160,
        p10_wage=74_000,
        p90_wage=208_000,
        cost_of_living_index=180.0,
        adjusted_median_wage=72_311.11,
        data_source="database",
    )


@pytest.fixture
def sample_industry_result() -> IndustryResult:
    return IndustryResult(
        region="National",
        industries=[
            IndustryOutlook(
                naics_code="541713",
                industry_name="Software Publishing",
                projected_growth_rate=0.28,
                projected_jobs_added=589_900,
                current_employment=2_580_000,
                key_regions=["San Francisco", "Seattle"],
                top_occupations=["Software Developer", "Data Scientist"],
            ),
        ],
        data_source="database",
    )


@pytest.fixture
def sample_skills_gap_result() -> SkillsGapResult:
    return SkillsGapResult(
        current_title="IT Support Specialist",
        target_title="Software Developer",
        gaps=[
            SkillGap(
                skill_name="Programming Language",
                category="tool",
                importance="required",
                typical_courses=["CS 101", "Codecademy Pro"],
                typical_cost_range="$0 - $500",
            ),
        ],
        data_source="database",
    )


@pytest.fixture
def sample_career_path_result() -> CareerPathResult:
    return CareerPathResult(
        entry_title="Junior Developer",
        years=10,
        steps=[
            CareerStep(step=1, title="Junior Developer", years_to_reach=0, salary_range="60,000 - 85,000", description="Entry-level", typical_promotion_path="2-3 years"),
            CareerStep(step=2, title="Developer", years_to_reach=3, salary_range="85,000 - 120,000", description="Mid-level", typical_promotion_path="2-3 years"),
        ],
        data_source="database",
    )


@pytest.fixture
def sample_offer_result() -> OfferComparisonResult:
    return OfferComparisonResult(
        base_salary=150_000,
        total_compensation=180_000,
        cost_of_living_index=158.8,
        effective_purchasing_power=113_350.13,
        breakdown={
            "base_salary": 150_000,
            "annualized_signing": 0.0,
            "target_annual_bonus": 15_000,
            "annual_equity": 10_000,
            "annualized_relocation": 0.0,
            "health_benefits_estimate": 5_000,
        },
        data_source="calculated",
    )