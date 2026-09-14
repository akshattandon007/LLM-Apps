"""Smoke tests for GradPath — verifies all MCP tools work with simulated data."""

from __future__ import annotations

import pytest

from src.searcher import find_colleges
from src.profile import college_profile
from src.comparer import compare_colleges
from src.earnings import earnings_by_program


@pytest.mark.asyncio
async def test_find_colleges_no_filters() -> None:
    """Search with no filters returns all sample colleges."""
    result = await find_colleges()
    assert "Found 8 college(s)" in result
    assert "State University of Technology" in result
    assert "Westfield State University" in result


@pytest.mark.asyncio
async def test_find_colleges_by_budget() -> None:
    """Budget filter narrows results to affordable schools."""
    result = await find_colleges(budget_max=10000)
    assert "Found" in result
    assert "Riverside Community College" in result
    assert "$3,200" in result or "$8,800" in result or "$9,800" in result
    # Preston is $28,500 net — should NOT appear
    assert "Preston Liberal Arts College" not in result


@pytest.mark.asyncio
async def test_find_colleges_by_state() -> None:
    """State filter returns only colleges in that state."""
    result = await find_colleges(state="IL")
    assert "Found" in result
    assert "State University of Technology" in result
    assert "Springfield, IL" in result
    assert "Riverside Community College" not in result


@pytest.mark.asyncio
async def test_find_colleges_by_major() -> None:
    """Major filter matches programs."""
    result = await find_colleges(major="Computer Science")
    assert "Found" in result
    assert "State University of Technology" in result
    assert "Pacific Shores University" in result


@pytest.mark.asyncio
async def test_find_colleges_by_size() -> None:
    """Size filter returns appropriate colleges."""
    result = await find_colleges(size_pref="small")
    assert "Found" in result
    assert "Preston Liberal Arts College" in result  # 4,200 students


@pytest.mark.asyncio
async def test_find_colleges_no_results() -> None:
    """Overly restrictive filters return a 'no results' message."""
    result = await find_colleges(budget_max=1000)
    assert "No colleges found" in result


@pytest.mark.asyncio
async def test_college_profile_existing() -> None:
    """Profile returns detailed info for a known college."""
    result = await college_profile("State University of Technology")
    assert "State University of Technology" in result
    assert "Springfield, IL" in result
    assert "$12,450" in result or "$12,450/yr" in result
    assert "72.0%" in result
    assert "Computer Science" in result


@pytest.mark.asyncio
async def test_college_profile_not_found() -> None:
    """Profile for unknown college returns not-found message."""
    result = await college_profile("Fake University Nowhere")
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_compare_colleges() -> None:
    """Comparison shows two colleges side by side."""
    result = await compare_colleges(
        "State University of Technology", "Preston Liberal Arts College"
    )
    assert "State University of Technology" in result
    assert "Preston Liberal Arts College" in result
    assert "$12,450" in result or "$12450" in result
    assert "$28,500" in result or "$28500" in result
    assert "Grad rate" in result


@pytest.mark.asyncio
async def test_compare_colleges_one_not_found() -> None:
    """Comparison handles one missing college gracefully."""
    result = await compare_colleges("State University of Technology", "NoSuchCollege")
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_earnings_by_program() -> None:
    """Earnings lookup returns an estimate for known data."""
    result = await earnings_by_program("Metro Technical Institute", "Information Technology")
    assert "Metro Technical Institute" in result
    assert "Information Technology" in result


@pytest.mark.asyncio
async def test_earnings_by_program_unlisted_field() -> None:
    """Earnings lookup for an unlisted field still returns overall data."""
    result = await earnings_by_program(
        "Riverside Community College", "Astrophysics"
    )
    assert "Riverside Community College" in result
    assert "Astrophysics" in result


@pytest.mark.asyncio
async def test_simulated_mode_is_active() -> None:
    """Confirm tests run in simulated mode."""
    from src.scorecard import _is_simulated

    assert _is_simulated()