"""Job offer comparison and total compensation breakdown.

Evaluates and compares job offers with total compensation calculation,
cost-of-living adjustments, and benefits valuation.
"""

from __future__ import annotations

from .databases import find_cost_of_living
from .models import JobOffer, OfferComparisonResult


def _total_comp(offer: JobOffer) -> float:
    """Calculate total annual compensation for a job offer."""
    base = offer.base_salary
    signing_annualized = offer.signing_bonus / 4 if offer.signing_bonus else 0  # amortize over 4 years
    annual_bonus = offer.base_salary * (offer.annual_bonus_target / 100)
    equity = offer.equity_value
    relocation_annualized = offer.relocation / 3 if offer.relocation else 0
    benefits = offer.health_benefits_value
    return base + signing_annualized + annual_bonus + equity + relocation_annualized + benefits


def compare_offer(
    salary: float,
    benefits: str = "",
    location: str = "",
    signing_bonus: float = 0.0,
    annual_bonus_pct: float = 0.0,
    equity: float = 0.0,
    relocation: float = 0.0,
    employer: str = "",
) -> OfferComparisonResult:
    """Evaluate a single job offer with total comp breakdown.

    Args:
        salary: Annual base salary in USD.
        benefits: Brief description of benefits (free text).
        location: City, ST or zip code for cost-of-living adjustment.
        signing_bonus: One-time signing bonus.
        annual_bonus_pct: Target annual bonus as percentage of base.
        equity: Annual equity value (RSU/option).
        relocation: Relocation assistance amount.
        employer: Employer name for context.

    Returns:
        OfferComparisonResult with total compensation and purchasing power.
    """
    offer = JobOffer(
        base_salary=salary,
        signing_bonus=signing_bonus,
        annual_bonus_target=annual_bonus_pct,
        equity_value=equity,
        relocation=relocation,
        location=location,
        employer_name=employer,
    )

    total = _total_comp(offer)

    # Cost-of-living adjustment
    col = find_cost_of_living(location) if location else None
    col_index = col.index if col else 100.0
    purchasing_power = round(total * (100.0 / col_index), 2) if col_index != 100.0 else total

    breakdown = {
        "base_salary": salary,
        "annualized_signing": round(offer.signing_bonus / 4, 2) if offer.signing_bonus else 0.0,
        "target_annual_bonus": round(salary * (annual_bonus_pct / 100), 2),
        "annual_equity": equity,
        "annualized_relocation": round(offer.relocation / 3, 2) if offer.relocation else 0.0,
        "health_benefits_estimate": offer.health_benefits_value,
    }

    return OfferComparisonResult(
        base_salary=salary,
        total_compensation=round(total, 2),
        cost_of_living_index=col_index,
        effective_purchasing_power=round(purchasing_power, 2),
        breakdown=breakdown,
        data_source="calculated",
    )