"""Categorizer — Detect recurring charges and categorize subscriptions."""

from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from src.merchant_db import MERCHANT_DB, resolve_merchant
from src.models import (
    CategorizedSub,
    Category,
    Charge,
    Frequency,
    Subscription,
)


def _is_likely_recurring(charges: list[Charge], merchant_name: str) -> bool:
    """Heuristic: if same merchant appears 2+ times, it's recurring."""
    return len(charges) >= 2


def _detect_frequency(dates: list[date]) -> Frequency:
    """Detect billing frequency from a list of dates.

    Looks for consistent intervals: monthly (28-31 days), yearly (365),
    weekly (7), quarterly (90-95).
    """
    if len(dates) < 2:
        return Frequency.UNKNOWN

    sorted_dates = sorted(dates)
    intervals = []
    for i in range(1, len(sorted_dates)):
        delta = (sorted_dates[i] - sorted_dates[i - 1]).days
        intervals.append(delta)

    if not intervals:
        return Frequency.UNKNOWN

    avg_interval = sum(intervals) / len(intervals)

    if 25 <= avg_interval <= 35:
        return Frequency.MONTHLY
    elif 6 <= avg_interval <= 8:
        return Frequency.WEEKLY
    elif 85 <= avg_interval <= 100:
        return Frequency.QUARTERLY
    elif 355 <= avg_interval <= 375:
        return Frequency.YEARLY
    else:
        return Frequency.UNKNOWN


def _compute_annual_cost(amount: float, frequency: Frequency) -> float:
    """Estimate annual cost from price and frequency."""
    multipliers = {
        Frequency.MONTHLY: 12,
        Frequency.YEARLY: 1,
        Frequency.WEEKLY: 52,
        Frequency.QUARTERLY: 4,
        Frequency.UNKNOWN: 12,  # default assumption
    }
    return round(amount * multipliers.get(frequency, 12), 2)


def _assign_category(merchant_name: str) -> Category:
    """Look up category from merchant DB."""
    name_lower = merchant_name.lower().strip()
    info = MERCHANT_DB.get(name_lower)
    if info:
        return info.category
    return Category.OTHER


def detect_recurring(charges: list[Charge]) -> list[Subscription]:
    """Identify which charges are recurring subscriptions.

    Groups charges by merchant name, then checks for recurrence.
    At least 2 occurrences = recurring subscription.
    """
    # Group charges by merchant (resolved)
    merchant_charges: dict[str, list[Charge]] = defaultdict(list)
    for charge in charges:
        key = charge.merchant or charge.description
        merchant_charges[key].append(charge)

    # Also group unresolved descriptions by similarity
    # (handles unknown merchants that still show pattern)
    description_charges: dict[str, list[Charge]] = defaultdict(list)
    for charge in charges:
        if not charge.merchant:
            description_charges[charge.description].append(charge)

    subscriptions: list[Subscription] = []

    # Known merchants
    for merchant, charge_list in merchant_charges.items():
        if not _is_likely_recurring(charge_list, merchant):
            continue

        dates = [c.transaction_date for c in charge_list]
        amounts = sorted(set(c.amount for c in charge_list))
        avg_amount = sum(amounts) / len(amounts)

        subs = Subscription(
            merchant=merchant.title() if merchant.islower() else merchant,
            amount=round(avg_amount, 2),
            frequency=_detect_frequency(dates),
            first_seen=min(dates) if dates else None,
            last_seen=max(dates),
            occurrences=len(charge_list),
        )
        subscriptions.append(subs)

    # Unknown merchants that look recurring (same description, 2+ times)
    for desc, charge_list in description_charges.items():
        if len(charge_list) < 2:
            continue

        dates = [c.transaction_date for c in charge_list]
        amounts = sorted(set(c.amount for c in charge_list))
        avg_amount = sum(amounts) / len(amounts)

        # Check if this resolves now
        merchant_name, _ = resolve_merchant(desc)
        display_name = (
            merchant_name.title() if merchant_name
            else (desc.title() if desc.islower() or desc.isupper() else desc)
        )

        subs = Subscription(
            merchant=display_name,
            amount=round(avg_amount, 2),
            frequency=_detect_frequency(dates),
            first_seen=min(dates) if dates else None,
            last_seen=max(dates),
            occurrences=len(charge_list),
        )
        subscriptions.append(subs)

    # Deduplicate by merchant name
    seen: set[str] = set()
    deduped: list[Subscription] = []
    for sub in subscriptions:
        key = sub.merchant.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(sub)
        else:
            # Merge occurrences
            for existing in deduped:
                if existing.merchant.lower() == key:
                    existing.occurrences += sub.occurrences
                    existing.amount = max(existing.amount, sub.amount)
                    if sub.first_seen and (existing.first_seen is None or sub.first_seen < existing.first_seen):
                        existing.first_seen = sub.first_seen
                    if sub.last_seen > existing.last_seen:
                        existing.last_seen = sub.last_seen
                    break

    return sorted(deduped, key=lambda s: -s.amount)


def categorize(subscriptions: list[Subscription]) -> list[CategorizedSub]:
    """Enrich subscriptions with category and annual cost estimates."""
    results: list[CategorizedSub] = []
    for sub in subscriptions:
        category = _assign_category(sub.merchant)
        annual_cost = _compute_annual_cost(sub.amount, sub.frequency)

        results.append(
            CategorizedSub(
                merchant=sub.merchant,
                amount=sub.amount,
                frequency=sub.frequency,
                category=category,
                annual_cost=annual_cost,
                first_seen=sub.first_seen,
                last_seen=sub.last_seen,
                occurrences=sub.occurrences,
            )
        )
    return sorted(results, key=lambda s: -s.annual_cost)


def estimate_annual_cost(subscriptions: list[CategorizedSub]) -> str:
    """Produce a human-readable annual cost summary per category and overall."""
    if not subscriptions:
        return "No subscriptions found."

    category_totals: dict[Category, float] = defaultdict(float)
    overall_total = 0.0

    for sub in subscriptions:
        category_totals[sub.category] += sub.annual_cost
        overall_total += sub.annual_cost

    lines = ["── Annual Cost Summary ──", ""]
    for cat in Category:
        total = category_totals.get(cat, 0)
        if total > 0:
            label = cat.value.replace("_", " ").title()
            lines.append(f"  {label:20s} ${total:>8.2f}/yr")

    lines.append("")
    lines.append(f"  {'TOTAL':20s} ${overall_total:>8.2f}/yr")
    lines.append(f"  {'Monthly equivalent':20s} ${overall_total/12:>8.2f}/mo")
    lines.append("")
    return "\n".join(lines)


def identify_unused(
    subscriptions: list[CategorizedSub],
    user_answers: dict[str, bool],
) -> list[str]:
    """Cross-reference user answers to find unused subscriptions.

    user_answers: {merchant_name_lower: uses_it (True=use, False=forgotten)}
    Returns list of merchant names identified as unused/forgotten.
    """
    forgotten: list[str] = []
    for sub in subscriptions:
        key = sub.merchant.lower()
        if key in user_answers and not user_answers[key]:
            forgotten.append(sub.merchant)
    return forgotten


def track_trials(subscriptions: list[CategorizedSub]) -> list[str]:
    """Identify subscriptions that are still in trial or about to convert."""
    warnings: list[str] = []
    today = date.today()
    warning_window = timedelta(days=3)

    for sub in subscriptions:
        if sub.is_trial and sub.trial_end:
            days_left = (sub.trial_end - today).days
            if days_left <= 0:
                warnings.append(
                    f"⚠ {sub.merchant} trial CONVERTED today — you're now being charged ${sub.amount}/mo. "
                    f"Cancel now to avoid the first charge."
                )
            elif days_left <= warning_window.days:
                warnings.append(
                    f"⚠ {sub.merchant} trial ends in {days_left} day(s) on {sub.trial_end}. "
                    f"Will convert to ${sub.amount}/{sub.frequency.value}. Cancel ahead if unwanted."
                )
            else:
                warnings.append(
                    f"ℹ {sub.merchant} trial runs until {sub.trial_end} ({days_left} days remaining). "
                    f"After that: ${sub.amount}/{sub.frequency.value}."
                )

    if not warnings:
        warnings.append("No active trials detected.")

    return warnings