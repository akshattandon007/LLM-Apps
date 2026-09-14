"""College Scorecard API client — fetches data from api.data.gov.

Supports two modes:
  LIVE  – COLLEGE_SCORECARD_API_KEY is set, queries the real API
  SIMULATED – no key found, returns built-in sample data for development/testing
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from src.models import College

API_BASE = "https://api.data.gov/ed/collegescorecard/v1"
DEFAULT_FIELDS = (
    "id,school.name,school.city,school.state,"
    "latest.cost.net_price.overall,"
    "latest.cost.attendance.academic_year,"
    "latest.cost.attendance.program_year,"
    "latest.completion.completion_rate_4yr_150,"
    "latest.earnings.10_yrs_after_entry.median_earnings,"
    "latest.student.size,"
    "latest.admissions.sat_scores.average.overall,"
    "latest.admissions.act_scores.midpoint.midpoint"
)

# ---------------------------------------------------------------------------
# Simulated data — realistic sample colleges for offline dev/testing
# ---------------------------------------------------------------------------
_SAMPLE_COLLEGES: list[dict[str, Any]] = [
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
    {
        "id": 1002,
        "school.name": "Riverside Community College",
        "school.city": "Portland",
        "school.state": "OR",
        "latest.cost.net_price.overall": 3200,
        "latest.cost.attendance.academic_year": 4200,
        "latest.cost.attendance.program_year": 8400,
        "latest.completion.completion_rate_4yr_150": 0.38,
        "latest.earnings.10_yrs_after_entry.median_earnings": 38200,
        "latest.student.size": 14200,
        "latest.admissions.sat_scores.average.overall": None,
        "latest.admissions.act_scores.midpoint.midpoint": None,
    },
    {
        "id": 1003,
        "school.name": "Preston Liberal Arts College",
        "school.city": "Hanover",
        "school.state": "NH",
        "latest.cost.net_price.overall": 28500,
        "latest.cost.attendance.academic_year": 56200,
        "latest.cost.attendance.program_year": 56200,
        "latest.completion.completion_rate_4yr_150": 0.91,
        "latest.earnings.10_yrs_after_entry.median_earnings": 71200,
        "latest.student.size": 4200,
        "latest.admissions.sat_scores.average.overall": 1410,
        "latest.admissions.act_scores.midpoint.midpoint": 32.0,
    },
    {
        "id": 1004,
        "school.name": "Westfield State University",
        "school.city": "Westfield",
        "school.state": "MA",
        "latest.cost.net_price.overall": 16200,
        "latest.cost.attendance.academic_year": 11200,
        "latest.cost.attendance.program_year": 28200,
        "latest.completion.completion_rate_4yr_150": 0.65,
        "latest.earnings.10_yrs_after_entry.median_earnings": 49300,
        "latest.student.size": 8700,
        "latest.admissions.sat_scores.average.overall": 1090,
        "latest.admissions.act_scores.midpoint.midpoint": 22.0,
    },
    {
        "id": 1005,
        "school.name": "Metro Technical Institute",
        "school.city": "Atlanta",
        "school.state": "GA",
        "latest.cost.net_price.overall": 8800,
        "latest.cost.attendance.academic_year": 5100,
        "latest.cost.attendance.program_year": 15600,
        "latest.completion.completion_rate_4yr_150": 0.45,
        "latest.earnings.10_yrs_after_entry.median_earnings": 45600,
        "latest.student.size": 6300,
        "latest.admissions.sat_scores.average.overall": None,
        "latest.admissions.act_scores.midpoint.midpoint": None,
    },
    {
        "id": 1006,
        "school.name": "Pacific Shores University",
        "school.city": "San Diego",
        "school.state": "CA",
        "latest.cost.net_price.overall": 22100,
        "latest.cost.attendance.academic_year": 15800,
        "latest.cost.attendance.program_year": 42100,
        "latest.completion.completion_rate_4yr_150": 0.74,
        "latest.earnings.10_yrs_after_entry.median_earnings": 63900,
        "latest.student.size": 15400,
        "latest.admissions.sat_scores.average.overall": 1240,
        "latest.admissions.act_scores.midpoint.midpoint": 26.0,
    },
    {
        "id": 1007,
        "school.name": "Prairie View A&M",
        "school.city": "Prairie View",
        "school.state": "TX",
        "latest.cost.net_price.overall": 11050,
        "latest.cost.attendance.academic_year": 7800,
        "latest.cost.attendance.program_year": 22100,
        "latest.completion.completion_rate_4yr_150": 0.52,
        "latest.earnings.10_yrs_after_entry.median_earnings": 42500,
        "latest.student.size": 11600,
        "latest.admissions.sat_scores.average.overall": 1020,
        "latest.admissions.act_scores.midpoint.midpoint": 19.5,
    },
    {
        "id": 1008,
        "school.name": "Northwood University",
        "school.city": "Midland",
        "school.state": "MI",
        "latest.cost.net_price.overall": 19300,
        "latest.cost.attendance.academic_year": 28500,
        "latest.cost.attendance.program_year": 28500,
        "latest.completion.completion_rate_4yr_150": 0.68,
        "latest.earnings.10_yrs_after_entry.median_earnings": 52100,
        "latest.student.size": 3400,
        "latest.admissions.sat_scores.average.overall": 1130,
        "latest.admissions.act_scores.midpoint.midpoint": 23.5,
    },
]

# Program mapping for simulated data
_SAMPLE_PROGRAMS: dict[int, list[str]] = {
    1001: [
        "Computer Science",
        "Electrical Engineering",
        "Mechanical Engineering",
        "Business Administration",
    ],
    1002: ["Liberal Arts", "Nursing", "Business", "Criminal Justice"],
    1003: ["Economics", "English", "History", "Political Science", "Biology"],
    1004: ["Education", "Psychology", "Sociology", "Communications"],
    1005: ["Information Technology", "Welding", "Automotive Tech", "Culinary Arts"],
    1006: ["Computer Science", "Biology", "Business", "Marine Biology"],
    1007: ["Engineering", "Agriculture", "Nursing", "Education"],
    1008: ["Business Administration", "Marketing", "Accounting", "Supply Chain"],
}


def _is_simulated() -> bool:
    """Return True if no real API key is configured."""
    key = os.getenv("COLLEGE_SCORECARD_API_KEY", "")
    return not key or key == "your-key-here" or key.startswith("changeme")


def _api_key() -> str | None:
    key = os.getenv("COLLEGE_SCORECARD_API_KEY", "")
    return key if key and not _is_simulated() else None


def _row_to_college(row: dict[str, Any]) -> College:
    """Convert a Scorecard API result row into a College model."""
    cid = row.get("id", 0)
    return College(
        id=cid,
        name=row.get("school.name", ""),
        city=row.get("school.city", ""),
        state=row.get("school.state", ""),
        net_price=row.get("latest.cost.net_price.overall"),
        tuition_in_state=row.get("latest.cost.attendance.academic_year"),
        tuition_out_of_state=row.get("latest.cost.attendance.program_year"),
        graduation_rate=row.get("latest.completion.completion_rate_4yr_150"),
        median_earnings=row.get("latest.earnings.10_yrs_after_entry.median_earnings"),
        enrollment_size=row.get("latest.student.size"),
        sat_average=row.get("latest.admissions.sat_scores.average.overall"),
        act_midpoint=row.get("latest.admissions.act_scores.midpoint.midpoint"),
        programs=_SAMPLE_PROGRAMS.get(cid, []),
    )


def _simulate_search(
    budget_max: float | None = None,
    state: str = "",
    major: str = "",
    size_pref: str = "",
) -> list[College]:
    """Filter sample data. Works offline, no API key needed."""
    results: list[College] = []
    for row in _SAMPLE_COLLEGES:
        c = _row_to_college(row)

        # Budget filter (net price)
        if budget_max is not None and c.net_price is not None and c.net_price > budget_max:
            continue

        # State filter
        if state and c.state.lower() != state.lower():
            continue

        # Major filter (check program name)
        if major:
            major_lower = major.lower()
            if not any(major_lower in p.lower() for p in c.programs):
                continue

        # Size filter
        if size_pref and c.enrollment_size is not None:
            pref = size_pref.lower()
            if pref in ("small", "small (<5000)") and c.enrollment_size > 5000:
                continue
            if pref in ("medium", "medium (5000-15000)") and (
                c.enrollment_size < 5000 or c.enrollment_size > 15000
            ):
                continue
            if pref in ("large", "large (>15000)") and c.enrollment_size < 15000:
                continue

        results.append(c)

    return results


def _simulate_school_by_name(name: str) -> College | None:
    """Find a sample college by name (case-insensitive partial match)."""
    for row in _SAMPLE_COLLEGES:
        if name.lower() in row.get("school.name", "").lower():
            return _row_to_college(row)
    return None


def _simulate_earnings(school_name: str, field_of_study: str) -> dict[str, object]:
    """Return simulated earnings estimate for a field at a school."""
    return {
        "median_earnings": 50000,
        "note": "simulated estimate — based on national median for this field",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def search_colleges(
    budget_max: float | None = None,
    state: str = "",
    major: str = "",
    size_pref: str = "",
    per_page: int = 20,
) -> list[College]:
    """Search colleges by budget, state, major, and size."""
    assert per_page > 0, "per_page must be positive"
    assert budget_max is None or budget_max >= 0, "budget_max must be non-negative"

    if _is_simulated():
        return _simulate_search(budget_max, state, major, size_pref)

    # Live API call
    key = _api_key()
    assert key is not None, "API key should be available in live mode"

    params: dict[str, object] = {
        "api_key": key,
        "fields": DEFAULT_FIELDS,
        "per_page": min(per_page, 100),
    }
    if budget_max is not None:
        params["latest.cost.net_price.overall__range"] = f"0,{budget_max}"
    if state:
        params["school.state"] = state
    if size_pref:
        pref = size_pref.lower()
        if "small" in pref:
            params["latest.student.size__range"] = "0,5000"
        elif "large" in pref:
            params["latest.student.size__range"] = "15000,"
        else:
            params["latest.student.size__range"] = "5000,15000"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_BASE}/schools", params=params)  # type: ignore[arg-type]
        resp.raise_for_status()
        data = resp.json()

    results: list[College] = []
    for row in data.get("results", []):
        c = _row_to_college(row)

        # Major filter applied client-side (API doesn't filter on program name directly)
        if major:
            major_lower = major.lower()
            if not any(major_lower in p.lower() for p in c.programs):
                continue

        results.append(c)

    return results


async def get_college_profile(school_name: str) -> College | None:
    """Fetch detailed profile for a specific college by name."""
    if _is_simulated():
        return _simulate_school_by_name(school_name)

    key = _api_key()
    assert key is not None

    params: dict[str, object] = {
        "api_key": key,
        "fields": DEFAULT_FIELDS,
        "per_page": 10,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_BASE}/schools",
            params={**params, "school.name": school_name},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None
    return _row_to_college(results[0])


async def get_earnings(
    school_name: str, field_of_study: str
) -> dict[str, object]:
    """Get earnings data for a specific field of study at a school."""
    if _is_simulated():
        return _simulate_earnings(school_name, field_of_study)

    # In live mode, Scorecard API v1 doesn't have a direct program-level
    # earnings endpoint. We use institution-level median earnings as a proxy.
    key = _api_key()
    assert key is not None

    params: dict[str, object] = {
        "api_key": key,
        "fields": "id,school.name,latest.earnings.10_yrs_after_entry.median_earnings",
        "per_page": 10,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_BASE}/schools",
            params={**params, "school.name": school_name},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return {"median_earnings": None, "error": "School not found"}

    earnings = results[0].get(
        "latest.earnings.10_yrs_after_entry.median_earnings"
    )
    return {
        "median_earnings": earnings,
        "field_of_study": field_of_study,
        "note": "Overall median earnings 10 years after entry (program-level data not available via Scorecard API v1)",
    }