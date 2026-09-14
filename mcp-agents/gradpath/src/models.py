"""Pydantic models for college data."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class College(BaseModel):
    """Represents a college/university with key affordability and outcome fields."""

    id: int = 0
    name: str = ""
    city: str = ""
    state: str = ""
    net_price: int | None = None
    tuition_in_state: int | None = None
    tuition_out_of_state: int | None = None
    graduation_rate: float | None = None
    median_earnings: int | None = None
    enrollment_size: int | None = None
    sat_average: int | None = None
    act_midpoint: float | None = None
    demographics: dict[str, Any] = Field(default_factory=dict)
    programs: list[str] = Field(default_factory=list)


class CollegeSearchResult(BaseModel):
    """Results from a college search query."""

    total: int = 0
    colleges: list[College] = Field(default_factory=list)
    error: str | None = None


class ComparisonRow(BaseModel):
    """One row in a side-by-side comparison."""

    field: str
    school1_value: str
    school2_value: str


class ComparisonResult(BaseModel):
    """Head-to-head comparison of two colleges."""

    school1_name: str
    school2_name: str
    rows: list[ComparisonRow] = Field(default_factory=list)
    error: str | None = None


class EarningsResult(BaseModel):
    """Earnings data for a specific field of study at a college."""

    school_name: str
    field_of_study: str
    median_earnings: int | None = None
    error: str | None = None