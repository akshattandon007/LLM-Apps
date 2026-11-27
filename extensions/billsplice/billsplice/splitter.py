"""
BillSplice — core splitting logic.

Splits a bill among people, handling:
- Individual items assigned to specific people
- Shared items split equally among all
- Tax and tip distributed proportionally to each person's subtotal
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List

from .models import Bill, Item, Person, SplitResult


def split_bill(bill: Bill) -> List[SplitResult]:
    """Split a bill among its people and return per-person results.

    Shared items are divided equally. Tax and tip are prorated by each
    person's share of the subtotal (including their share of shared items).
    """
    if not bill.people:
        return []

    subtotals = _calculate_subtotals(bill)
    total_subtotal = sum(subtotals.values(), Decimal("0.00"))

    results: List[SplitResult] = []
    for person in bill.people:
        sub = subtotals.get(person.name, Decimal("0.00"))
        # Prorate tax & tip by each person's fraction of subtotal
        if total_subtotal > Decimal("0.00"):
            fraction = sub / total_subtotal
            tax_share = (bill.tax_amount * fraction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            tip_share = (bill.tip_amount * fraction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            tax_share = Decimal("0.00")
            tip_share = Decimal("0.00")

        total = sub + tax_share + tip_share
        results.append(SplitResult(
            person_name=person.name,
            items=person.items,
            subtotal=sub,
            tax_share=tax_share,
            tip_share=tip_share,
            total=total,
        ))

    return results


def _calculate_subtotals(bill: Bill) -> dict[str, Decimal]:
    """Calculate each person's subtotal including their share of shared items."""
    subtotals: dict[str, Decimal] = {}
    n = len(bill.people)

    for person in bill.people:
        subtotals[person.name] = sum(
            (i.price for i in person.items if not i.shared),
            Decimal("0.00"),
        )

    # Distribute shared items equally
    for item in bill.items:
        if item.shared and n > 0:
            share = (item.price / Decimal(str(n))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            for person in bill.people:
                subtotals[person.name] = subtotals.get(person.name, Decimal("0.00")) + share

    return subtotals