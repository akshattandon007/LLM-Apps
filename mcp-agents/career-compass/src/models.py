"""Pydantic models for Career Compass."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────────────


class DegreeLevel(str, Enum):
    """Typical education requirement for an occupation."""

    HIGH_SCHOOL = "high_school"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    DOCTORAL = "doctoral"
    NONE = "none"


class GrowthOutlook(str, Enum):
    """Job growth classification."""

    DECLINE = "decline"
    LITTLE_CHANGE = "little_change"
    GROWING = "growing"
    FAST_GROWING = "fast_growing"
    VERY_FAST = "very_fast"


# ── Occupation ──────────────────────────────────────────────────────────────────


class Occupation(BaseModel):
    """A single occupation entry."""

    soc_code: str = Field(description="Standard Occupational Classification code, e.g. 15-1252")
    title: str = Field(description="Occupation title, e.g. Software Developer")
    median_wage: float = Field(description="Annual median wage in USD")
    p10_wage: float = Field(description="10th percentile annual wage")
    p90_wage: float = Field(description="90th percentile annual wage")
    typical_education: DegreeLevel = Field(description="Typical entry-level education")
    experience_years: int = Field(default=0, description="Typical years of experience")
    growth_rate: float = Field(default=0.0, description="Projected growth rate as decimal (0.07 = 7%)")
    openings_year: int = Field(default=0, description="Projected annual job openings")
    description: str = Field(default="", description="Brief description of the occupation")


# ── Cost of Living ──────────────────────────────────────────────────────────────


class CostOfLiving(BaseModel):
    """Regional cost-of-living index (US national average = 100)."""

    zip_code: str
    city: str
    state: str
    index: float = Field(description="Composite index; 100 = national average")
    housing_index: float = Field(default=100.0)
    groceries_index: float = Field(default=100.0)
    transportation_index: float = Field(default=100.0)
    utilities_index: float = Field(default=100.0)


# ── Skill / Certification ──────────────────────────────────────────────────────


class SkillGap(BaseModel):
    """A single skill or certification gap between two roles."""

    skill_name: str
    category: str = Field(description="e.g. 'certification', 'tool', 'soft_skill'")
    importance: str = Field(default="required", description="required / recommended / nice_to_have")
    typical_courses: list[str] = Field(default_factory=list)
    typical_cost_range: str = Field(default="")


# ── Career Step ────────────────────────────────────────────────────────────────


class CareerStep(BaseModel):
    """A single step in a career progression path."""

    step: int
    title: str
    years_to_reach: int = Field(description="Total years to reach this step from entry")
    salary_range: str = Field(description="e.g. 65000 - 85000")
    description: str = Field(default="")
    typical_promotion_path: str = Field(default="")


# ── Industry Outlook ────────────────────────────────────────────────────────────


class IndustryOutlook(BaseModel):
    """Growth data for a single industry."""

    naics_code: str = Field(default="", description="NAICS industry code")
    industry_name: str
    projected_growth_rate: float = Field(description="Decimal growth rate")
    projected_jobs_added: int = Field(default=0)
    current_employment: int = Field(default=0)
    key_regions: list[str] = Field(default_factory=list)
    top_occupations: list[str] = Field(default_factory=list)


# ── Job Offer ──────────────────────────────────────────────────────────────────


class JobOffer(BaseModel):
    """Details of a single job offer for comparison."""

    base_salary: float = Field(description="Annual base salary in USD")
    signing_bonus: float = Field(default=0.0)
    annual_bonus_target: float = Field(default=0.0, description="Target annual bonus as % of base")
    equity_value: float = Field(default=0.0, description="Annual RSU/option value estimate")
    relocation: float = Field(default=0.0)
    location: str = Field(default="", description="City, ST or zip code")
    employer_name: str = Field(default="")
    pto_days: int = Field(default=10)
    has_401k_match: bool = Field(default=False)
    health_benefits_value: float = Field(default=5000.0, description="Estimated annual health benefit value")


# ── Tool Results ───────────────────────────────────────────────────────────────


class SalaryResult(BaseModel):
    """Result of salary_by_role query."""

    occupation: str
    zip_code: str
    median_wage: float
    p10_wage: float
    p90_wage: float
    cost_of_living_index: float
    adjusted_median_wage: float
    data_source: str = "simulated"


class IndustryResult(BaseModel):
    """Result of growing_industries query."""

    region: str
    industries: list[IndustryOutlook]
    data_source: str = "simulated"


class SkillsGapResult(BaseModel):
    """Result of skills_gap query."""

    current_title: str
    target_title: str
    gaps: list[SkillGap]
    data_source: str = "simulated"


class CareerPathResult(BaseModel):
    """Result of career_path query."""

    entry_title: str
    years: int
    steps: list[CareerStep]
    data_source: str = "simulated"


class OfferComparisonResult(BaseModel):
    """Result of compare_offer query."""

    base_salary: float
    total_compensation: float
    cost_of_living_index: float
    effective_purchasing_power: float
    breakdown: dict[str, float]
    data_source: str = "simulated"


class JobOutlookResult(BaseModel):
    """Result of job_outlook query."""

    occupation: str
    region: str
    current_employment: int
    projected_growth_rate: float
    growth_outlook: GrowthOutlook
    annual_openings: int
    key_industries: list[str]
    data_source: str = "simulated"