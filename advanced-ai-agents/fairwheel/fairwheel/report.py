"""Markdown report renderer — one-page buying report."""

from __future__ import annotations

from .models import FairWheelReport

VERDICT_EMOJI = {"WORTH IT": "✅", "WAIT": "⏳", "AVOID": "🚫"}


def render_markdown(report: FairWheelReport) -> str:
    q = report.query
    v = report.verdict
    lines: list[str] = []

    lines.append(f"# 🚗 FairWheel — Buying Report: {q.year} {q.make.title()} {q.model.title()}")
    lines.append("")
    lines.append(f"**Verdict: {VERDICT_EMOJI.get(v.verdict, '')} {v.verdict}** — weighted score **{v.score:.0f}/100**")
    lines.append("")

    lines.append("## Safety (NHTSA)")
    s = report.safety
    if s.overall_rating is not None:
        lines.append(f"- Overall crash rating: **{s.overall_rating}/5 stars** (front {s.front_rating or 'n/a'}, side {s.side_rating or 'n/a'})")
    else:
        lines.append("- No safety rating found for this vehicle config.")
    if s.source == "simulated":
        lines.append(f"  - ⚠️ *Simulated data* (API unavailable: {s.error or 'demo mode'})")
    lines.append("")

    lines.append("## Complaints (NHTSA)")
    c = report.complaints
    if c.clusters:
        lines.append(f"- **{c.total_complaints} complaints** in NHTSA database; top themes:")
        for cluster in c.clusters[:5]:
            lines.append(f"  - {cluster.component.title()}: {cluster.count}")
    else:
        lines.append("- No complaints on file for this vehicle.")
    if c.source == "simulated":
        lines.append(f"  - ⚠️ *Simulated data* (API unavailable: {c.error or 'demo mode'})")
    lines.append("")

    lines.append("## Recalls (NHTSA)")
    r = report.recalls
    if r.recalls:
        lines.append(f"- **{r.count} open recall campaign(s)** — dealer must fix these free:")
        for recall in r.recalls[:4]:
            lines.append(f"  - `{recall.campaign_number}` — {recall.component}: {recall.summary[:140]}")
    else:
        lines.append("- No open recall campaigns on record. ✅")
    if r.source == "simulated":
        lines.append(f"  - ⚠️ *Simulated data* (API unavailable: {r.error or 'demo mode'})")
    lines.append("")

    lines.append("## Fuel cost (fueleconomy.gov)")
    co = report.cost
    if co.combined_mpg:
        lines.append(f"- Combined **{co.combined_mpg} mpg** (city {co.city_mpg}, hwy {co.highway_mpg})")
        lines.append(f"- 5-year fuel cost @ {q.annual_miles:,} mi/yr, ${q.fuel_price:.2f}/gal: **${co.five_year_fuel_cost:,.0f}**")
    else:
        lines.append("- Fuel data unavailable.")
    if co.source == "simulated":
        lines.append(f"  - ⚠️ *Simulated data* (API unavailable: {co.error or 'demo mode'})")
    lines.append("")

    lines.append("## Why")
    for reason in v.reasons:
        lines.append(f"- {reason}")
    lines.append("")

    lines.append("## Negotiation talking points")
    for i, point in enumerate(v.talking_points, 1):
        lines.append(f"{i}. {point}")
    lines.append("")

    sources = {report.safety.source, report.complaints.source, report.recalls.source, report.cost.source}
    if "simulated" in sources:
        lines.append("> ⚠️ Some data above is simulated because a live API was unreachable. Verify against the free NHTSA and fueleconomy.gov sites before relying on this report.")
    lines.append("")
    lines.append("---")
    lines.append("*FairWheel — free car research before you buy. Data: NHTSA + fueleconomy.gov.*")
    lines.append("")
    return "\n".join(lines)