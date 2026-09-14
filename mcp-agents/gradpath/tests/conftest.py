"""Fixtures with mock college data for smoke tests."""

from __future__ import annotations

import os
from typing import Any

import pytest

from src.models import College


@pytest.fixture(autouse=True)
def _patch_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests always run in simulated mode."""
    monkeypatch.setenv("COLLEGE_SCORECARD_API_KEY", "")


@pytest.fixture
def sample_college() -> College:
    """A typical public university."""
    return College(
        id=1001,
        name="State University of Technology",
        city="Springfield",
        state="IL",
        net_price=12450,
        tuition_in_state=9800,
        tuition_out_of_state=24500,
        graduation_rate=0.72,
        median_earnings=58700,
        enrollment_size=18500,
        sat_average=1180,
        act_midpoint=24.5,
        programs=["Computer Science", "Electrical Engineering", "Mechanical Engineering"],
    )


@pytest.fixture
def sample_colleges() -> list[dict[str, Any]]:
    """Raw rows matching _SAMPLE_COLLEGES structure for scorecard tests."""
    return [
        {
            "id": 1001,
            "school.name": "State University of Technology",
            "school.city": "Springfield",
            "school.state": "IL",
            "latest.cost.net_price.overall": 12450,
            "latest.cost.attendance.academic_year": 9800,
            "latest.cost.attendance.program_year": 24500,
            "latest.completion.completion_rate_4yr_150": 0.72,
            "latest.earnings.10_yrs_after_entry.median_earnings": 58700,
            "latest.student.size": 18500,
            "latest.admissions.sat_scores.average.overall": 1180,
            "latest.admissions.act_scores.midpoint.midpoint": 24.5,
        },
    ]