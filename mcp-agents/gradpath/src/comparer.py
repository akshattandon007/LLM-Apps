"""Side-by-side comparison of two colleges."""

from __future__ import annotations

from src.models import College
from src.scorecard import get_college_profile


def _money(v: int | None) -> str:
    return f"${v:,}" if v is not None else "N/A"


def _pct(v: float | None) -> str:
    return f"{v * 100:.1f}%" if v is not None else "N/A"


def _roi(v: College) -> str:
    """Quick ROI estimate: net price vs earnings."""
    if v.net_price and v.median_earnings and v.net_price > 0:
        years = v.net_price / (v.median_earnings / 12)
        return f"~{years:.1f} months of post-grad earnings to cover net price"
    return "N/A"


async def compare_colleges(school1: str, school2: str) -> str:
    """Head-to-head comparison of cost vs outcome for two colleges."""
    c1 = await get_college_profile(school1)
    c2 = await get_college_profile(school2)

    if c1 is None and c2 is None:
        return f"Neither '{school1}' nor '{school2}' were found. Try different names."
    if c1 is None:
        return f"College '{school1}' not found. Try a different name."
    if c2 is None:
        return f"College '{school2}' not found. Try a different name."

    lines: list[str] = []
    lines.append(f"{'Field':<35} {c1.name:<35} {c2.name:<35}")
    lines.append(f"{'-'*35:<35} {'-'*35:<35} {'-'*35:<35}")
    lines.append(
        f"{'Net price':<35} {_money(c1.net_price):<35} {_money(c2.net_price):<35}"
    )
    lines.append(
        f"{'Tuition (in-state)':<35} {_money(c1.tuition_in_state):<35} {_money(c2.tuition_in_state):<35}"
    )
    lines.append(
        f"{'Tuition (out-of-state)':<35} {_money(c1.tuition_out_of_state):<35} {_money(c2.tuition_out_of_state):<35}"
    )
    lines.append(
        f"{'Grad rate':<35} {_pct(c1.graduation_rate):<35} {_pct(c2.graduation_rate):<35}"
    )
    lines.append(
        f"{'Median earnings (10yr)':<35} {_money(c1.median_earnings):<35} {_money(c2.median_earnings):<35}"
    )
    lines.append(
        f"{'Enrollment':<35} {str(c1.enrollment_size) if c1.enrollment_size else 'N/A':<35} {str(c2.enrollment_size) if c2.enrollment_size else 'N/A':<35}"
    )
    lines.append(
        f"{'SAT average':<35} {str(c1.sat_average) if c1.sat_average else 'N/A':<35} {str(c2.sat_average) if c2.sat_average else 'N/A':<35}"
    )
    lines.append("")
    lines.append("ROI ESTIMATE")
    lines.append(f"  {c1.name}: {_roi(c1)}")
    lines.append(f"  {c2.name}: {_roi(c2)}")

    return "\n".join(lines)