"""GradPath MCP Server — find affordable colleges with real outcome data.

Exposes 4 MCP tools that MCP hosts (Claude Desktop, etc.) can call:

  find_colleges       — search 6,300+ US schools by budget, state, major, size
  college_profile     — tuition, grad rate, median earnings, demographics
  compare_colleges    — head-to-head cost vs outcome
  earnings_by_program — what graduates earn by field of study
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from src.comparer import compare_colleges as _compare_colleges
from src.earnings import earnings_by_program as _earnings_by_program
from src.profile import college_profile as _college_profile
from src.searcher import find_colleges as _find_colleges

mcp = FastMCP(
    "GradPath",
    description="Find affordable US colleges with real cost, graduation rate, and post-grad earnings data from the College Scorecard API.",
)


@mcp.tool()
async def find_colleges(
    budget_max: float | None = None,
    state: str = "",
    major: str = "",
    size_pref: str = "",
) -> str:
    """Search US colleges by budget, state, major, and size.

    Args:
        budget_max: Maximum net price (average cost after financial aid) per year.
        state: Two-letter state abbreviation (e.g. 'CA', 'TX').
        major: Area of study (e.g. 'Computer Science', 'Nursing').
        size_pref: 'Small (<5000)', 'Medium (5000-15000)', or 'Large (>15000)'.
    """
    return await _find_colleges(
        budget_max=budget_max,
        state=state,
        major=major,
        size_pref=size_pref,
    )


@mcp.tool()
async def college_profile(school_name: str) -> str:
    """Get a detailed profile for a specific US college or university.

    Args:
        school_name: Full or partial name of the college (e.g. 'Stanford University').
    """
    return await _college_profile(school_name)


@mcp.tool()
async def compare_colleges(school1: str, school2: str) -> str:
    """Compare two colleges side-by-side on cost, graduation rate, and earnings.

    Args:
        school1: Name of the first college.
        school2: Name of the second college.
    """
    return await _compare_colleges(school1, school2)


@mcp.tool()
async def earnings_by_program(school: str, field_of_study: str) -> str:
    """Get earnings data for graduates of a specific program at a college.

    Args:
        school: Name of the college.
        field_of_study: Major or program name (e.g. 'Computer Science').
    """
    return await _earnings_by_program(school, field_of_study)


def run_stdio() -> None:
    """Run the MCP server over stdio transport (for MCP hosts)."""
    mcp.run(transport="stdio")


def run_sse(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run the MCP server over SSE transport (HTTP)."""
    mcp.run(transport="sse", host=host, port=port)