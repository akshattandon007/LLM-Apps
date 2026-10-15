"""Deal Reviewer agent — the critic.

Weighs the four agency reports into a 0-100 score and a WORTH IT / WAIT /
AVOID verdict, with concrete negotiation talking points. Deterministic — no
LLM required, so the output is reproducible and honest.
"""

from __future__ import annotations

from ..models import (
    ComplaintReport,
    CostReport,
    DealVerdict,
    RecallReport,
    SafetyReport,
    VehicleQuery,
)

WEIGHTS = {"safety": 0.40, "complaints": 0.30, "recalls": 0.20, "cost": 0.10}

# Components that make a complaint cluster a hard-safety red flag.
CRITICAL_COMPONENTS = {"AIR BAGS", "BRAKES", "ENGINE", "FUEL SYSTEM", "STEERING", "SUSPENSION", "POWER TRAIN"}


def _safety_score(safety: SafetyReport) -> float:
    if safety.overall_rating is None:
        return 50.0
    return round(safety.overall_rating / 5.0 * 100, 1)


def _complaint_score(complaints: ComplaintReport) -> float:
    if not complaints.total_complaints:
        return 100.0
    # Every complaint costs points; critical-component clusters cost more.
    score = max(0.0, 100 - complaints.total_complaints * 0.15)
    critical_hits = sum(1 for c in complaints.clusters if c.component in CRITICAL_COMPONENTS)
    score = max(0.0, score - critical_hits * 5)
    return round(score, 1)


def _recall_score(recalls: RecallReport) -> float:
    if recalls.count == 0:
        return 100.0
    score = max(0.0, 100 - recalls.count * 12)
    return round(score, 1)


def _cost_score(cost: CostReport, query: VehicleQuery) -> float:
    if cost.five_year_fuel_cost is None:
        return 50.0
    # Baseline: 12k mi/yr * $3.50/gal @ 25 mpg => $8,400 / 5yr. Cheaper = better.
    baseline = 8400.0
    if cost.five_year_fuel_cost <= baseline:
        return 100.0
    return round(max(0.0, 100 - (cost.five_year_fuel_cost - baseline) / baseline * 100), 1)


def run(
    query: VehicleQuery,
    safety: SafetyReport,
    complaints: ComplaintReport,
    recalls: RecallReport,
    cost: CostReport,
) -> DealVerdict:
    scores = {
        "safety": _safety_score(safety),
        "complaints": _complaint_score(complaints),
        "recalls": _recall_score(recalls),
        "cost": _cost_score(cost, query),
    }
    total = round(sum(WEIGHTS[k] * v for k, v in scores.items()), 1)

    reasons: list[str] = []
    talking_points: list[str] = []

    if safety.overall_rating is not None:
        reasons.append(f"NHTSA overall crash rating: {safety.overall_rating}/5 stars.")
    if complaints.clusters:
        top = complaints.clusters[0]
        reasons.append(f"Top complaint theme: {top.component.title()} ({top.count} complaints in NHTSA database).")
    if recalls.count:
        reasons.append(f"{recalls.count} open NHTSA recall campaign(s) on record.")
    if cost.five_year_fuel_cost is not None:
        reasons.append(f"Estimated 5-year fuel cost: ${cost.five_year_fuel_cost:,.0f} ({cost.combined_mpg} mpg combined).")
    if query.budget and cost.five_year_fuel_cost is not None:
        total_5yr = query.budget + cost.five_year_fuel_cost
        reasons.append(f"5-year total (purchase + fuel): ${total_5yr:,.0f}.")

    # Hard gates
    if safety.overall_rating is not None and safety.overall_rating < 3:
        verdict = "AVOID"
        reasons.append("Hard gate: crash rating below 3 stars — do not buy.")
    elif total >= 80:
        verdict = "WORTH IT"
    elif total >= 55:
        verdict = "WAIT"
    else:
        verdict = "AVOID"

    # Negotiation talking points
    if recalls.count:
        talking_points.append(
            f"Open recall {recalls.recalls[0].campaign_number} must be fixed FREE by the dealer before you sign — use it as a closing lever."
        )
    if complaints.clusters:
        top = complaints.clusters[0]
        talking_points.append(
            f"Ask the dealer what they know about '{top.component.title()}' complaints — {top.count} owners filed complaints on NHTSA."
        )
    if cost.five_year_fuel_cost is not None and cost.five_year_fuel_cost > 8400:
        talking_points.append(
            f"Fuel costs ${cost.five_year_fuel_cost:,.0f} over 5 years — negotiate the price down or shop the higher-MPG trim."
        )
    if query.budget and cost.five_year_fuel_cost is not None and query.budget + cost.five_year_fuel_cost > query.budget * 1.3:
        talking_points.append("Purchase + fuel blows past budget by more than 30% over 5 years — hard price anchor for negotiation.")
    if not talking_points:
        talking_points.append("No major red flags found — verify the vehicle's VIN on the free NHTSA recall site before closing.")

    return DealVerdict(
        verdict=verdict,
        score=total,
        reasons=reasons,
        talking_points=talking_points,
        scores_by_factor=scores,
    )