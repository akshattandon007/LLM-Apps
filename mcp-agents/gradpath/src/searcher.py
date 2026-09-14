"""Find colleges by budget, state, major, and size."""

from __future__ import annotations

from src.models import College
from src.scorecard import search_colleges


def _format_size(size: int | None) -> str:
    if size is None:
        return "N/A"
    if size < 2000:
        return "Very small"
    if size < 5000:
        return "Small"
    if size < 15000:
        return "Medium"
    if size < 30000:
        return "Large"
    return "Very large"


def _format_money(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:,}"


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


async def find_colleges(
    budget_max: float | None = None,
    state: str = "",
    major: str = "",
    size_pref: str = "",
) -> str:
    """Search for colleges matching the given criteria.

    Returns a human-readable formatted list of matching colleges.
    """
    results = await search_colleges(
        budget_max=budget_max,
        state=state,
        major=major,
        size_pref=size_pref,
        per_page=20,
    )

    if not results:
        criteria_parts = []
        if budget_max is not None:
            criteria_parts.append(f"budget ≤ ${budget_max:,.0f}")
        if state:
            criteria_parts.append(f"state: {state.upper()}")
        if major:
            criteria_parts.append(f"major: {major}")
        if size_pref:
            criteria_parts.append(f"size: {size_pref}")
        criteria = ", ".join(criteria_parts) if criteria_parts else "no filters"
        return f"No colleges found matching {criteria}. Try broadening your search."

    lines: list[str] = []
    lines.append(f"Found {len(results)} college(s):")
    lines.append("")

    for i, c in enumerate(results, 1):
        lines.append(f"{i}. {c.name} — {c.city}, {c.state}")
        lines.append(f"   Net price: {_format_money(c.net_price)}")
        lines.append(f"   Tuition: ${c.tuition_in_state:,}/yr in-state" if c.tuition_in_state else "   Tuition (in-state): N/A")
        lines.append(f"   Graduation rate: {_format_pct(c.graduation_rate)}")
        lines.append(f"   Median earnings (10 yrs): {_format_money(c.median_earnings)}")
        lines.append(f"   Enrollment: {_format_size(c.enrollment_size)} ({c.enrollment_size:,})" if c.enrollment_size else "   Enrollment: N/A")
        if c.programs:
            lines.append(f"   Programs: {', '.join(c.programs[:5])}{'…' if len(c.programs) > 5 else ''}")
        lines.append("")

    return "\n".join(lines)