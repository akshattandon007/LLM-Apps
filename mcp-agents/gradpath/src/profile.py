"""Get detailed profile for a specific college."""

from __future__ import annotations

from src.models import College
from src.scorecard import get_college_profile


def _money(v: int | None) -> str:
    return f"${v:,}" if v is not None else "N/A"


def _pct(v: float | None) -> str:
    return f"{v * 100:.1f}%" if v is not None else "N/A"


def _format_profile(c: College) -> str:
    """Format a College model into a readable profile."""
    lines: list[str] = []
    lines.append(f"{c.name}")
    lines.append(f"{c.city}, {c.state}")
    lines.append("")

    lines.append("COSTS")
    lines.append(f"  Net price (avg after aid):  {_money(c.net_price)}")
    lines.append(f"  Tuition (in-state):         {_money(c.tuition_in_state)}")
    lines.append(f"  Tuition (out-of-state):     {_money(c.tuition_out_of_state)}")
    lines.append("")

    lines.append("OUTCOMES")
    lines.append(f"  Graduation rate (4yr):      {_pct(c.graduation_rate)}")
    lines.append(f"  Median earnings (10 yrs):   {_money(c.median_earnings)}")
    lines.append("")

    lines.append("ADMISSIONS")
    lines.append(f"  Average SAT:                 {c.sat_average if c.sat_average else 'N/A'}")
    lines.append(f"  ACT midpoint:                {c.act_midpoint if c.act_midpoint else 'N/A'}")
    lines.append("")

    lines.append("STUDENT BODY")
    lines.append(f"  Enrollment:                  {c.enrollment_size:,}" if c.enrollment_size else "  Enrollment: N/A")
    lines.append("")

    if c.programs:
        lines.append("PROGRAMS")
        for p in c.programs:
            lines.append(f"  - {p}")

    return "\n".join(lines)


async def college_profile(school_name: str) -> str:
    """Get a detailed profile for a specific college by name."""
    c = await get_college_profile(school_name)
    if c is None:
        return f"College '{school_name}' not found. Try a different name or use find_colleges to search."

    return _format_profile(c)