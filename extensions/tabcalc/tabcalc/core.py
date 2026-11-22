"""Core expense-splitting and debt-settlement logic."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Expense:
    """A single expense paid by one person on behalf of the group."""

    description: str
    paid_by: str              # who fronted the money
    amount: Decimal           # total amount paid
    split_among: List[str]    # people who share this expense (incl. payer)


@dataclass
class Settlement:
    """One transfer to settle a debt."""

    from_person: str
    to_person: str
    amount: Decimal


@dataclass
class ParticipantBalance:
    name: str
    net_balance: Decimal      # positive = owed money, negative = owes money


@dataclass
class SettlementPlan:
    """Complete settlement plan for a group."""

    participants: List[ParticipantBalance] = field(default_factory=list)
    transfers: List[Settlement] = field(default_factory=list)
    total_spent: Decimal = Decimal("0")
    per_person: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def compute_balances(expenses: List[Expense]) -> List[ParticipantBalance]:
    """Compute each person's net balance from a list of expenses.

    Positive balance = they are owed money (paid more than their share).
    Negative balance = they owe money (paid less than their share).
    """
    balances: dict[str, Decimal] = {}

    for expense in expenses:
        share = expense.amount / len(expense.split_among)
        # The payer gets credit for the full amount they paid
        balances[expense.paid_by] = (
            balances.get(expense.paid_by, Decimal("0")) + expense.amount
        )
        for person in expense.split_among:
            # Everyone (including the payer) gets debited their share
            balances[person] = balances.get(person, Decimal("0")) - share

    return [
        ParticipantBalance(name=name, net_balance=bal.quantize(Decimal("0.01")))
        for name, bal in sorted(balances.items())
    ]


def compute_minimum_transfers(balances: List[ParticipantBalance]) -> List[Settlement]:
    """Compute the minimum number of transfers to settle all debts.

    Uses the standard greedy algorithm: sort by balance, match the
    biggest creditor with the biggest debtor iteratively.
    """
    # Separate creditors (positive) and debtors (negative)
    creditors: list[Tuple[str, Decimal]] = []
    debtors: list[Tuple[str, Decimal]] = []

    for p in balances:
        if p.net_balance > 0:
            creditors.append((p.name, p.net_balance))
        elif p.net_balance < 0:
            debtors.append((p.name, -p.net_balance))  # store as positive debt

    # Sort: largest first
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    transfers: List[Settlement] = []
    ci = di = 0

    while ci < len(creditors) and di < len(debtors):
        name_c, amount_c = creditors[ci]
        name_d, amount_d = debtors[di]

        transfer_amount = min(amount_c, amount_d)
        transfer_amount = transfer_amount.quantize(Decimal("0.01"))

        if transfer_amount > 0:
            transfers.append(
                Settlement(
                    from_person=name_d,
                    to_person=name_c,
                    amount=transfer_amount,
                )
            )

        # Reduce balances
        creditors[ci] = (name_c, amount_c - transfer_amount)
        debtors[di] = (name_d, amount_d - transfer_amount)

        if creditors[ci][1] == 0:
            ci += 1
        if debtors[di][1] == 0:
            di += 1

    return transfers


def compute_settlement(expenses: List[Expense]) -> SettlementPlan:
    """Full pipeline: compute balances → minimum transfers."""
    balances = compute_balances(expenses)
    transfers = compute_minimum_transfers(balances)

    total_spent = sum(e.amount for e in expenses) if expenses else Decimal("0")
    total_spent = total_spent.quantize(Decimal("0.01"))

    # Per-person share (if everyone splits everything equally — simplified)
    # For heterogeneous splits, per_person will vary; use the average as a guide
    all_names = sorted({p.name for p in balances})
    per_person = (total_spent / len(all_names)).quantize(Decimal("0.01")) if all_names else Decimal("0")

    return SettlementPlan(
        participants=balances,
        transfers=transfers,
        total_spent=total_spent,
        per_person=per_person,
    )