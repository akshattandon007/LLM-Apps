"""Earnings by field of study at a specific college."""

from __future__ import annotations

from src.models import College
from src.scorecard import get_college_profile, get_earnings


async def earnings_by_program(school: str, field_of_study: str) -> str:
    """Get earnings information for graduates of a specific program at a college.

    Note: The College Scorecard API v1 provides institution-level median earnings,
    not program-level. For program-specific data, we provide the institution-level
    figure as a proxy with caveats.
    """
    # First fetch the college profile to check program availability
    c: College | None = await get_college_profile(school)

    school_name = school

    if c is not None:
        school_name = c.name
        # Check if the requested field is offered
        if c.programs:
            field_lower = field_of_study.lower()
            matches = [p for p in c.programs if field_lower in p.lower()]
            if not matches:
                lines: list[str] = []
                lines.append(
                    f"'{field_of_study}' was not found among the listed programs at {c.name}."
                )
                lines.append(f"Programs offered: {', '.join(c.programs)}")
                lines.append("")
                lines.append(
                    "Showing overall earnings data for this institution instead:"
                )
                lines.append("")

    # Get earnings data
    earnings_data = await get_earnings(school_name, field_of_study)
    median = earnings_data.get("median_earnings")

    if median is not None:
        note = earnings_data.get("note", "")
        result = f"**{field_of_study} graduates from {school_name}**\n"
        result += f"Median earnings 10 years after entry: ${int(median):,}/yr\n"
        if note:
            result += f"\nNote: {note}"
        return result

    return (
        f"Earnings data not available for '{field_of_study}' at {school_name}."
    )