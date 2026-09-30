"""
Core expense-splitting and debt-settlement logic.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Tuple


@dataclass
class Expense:
    """A single expense paid by one person for a group."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: str = ""
    amount: Decimal = Decimal("0")
    paid_by: str = ""
    participants: List[str] = field(default_factory=list)
    date: str = field(default_factory=lambda: date.today().isoformat())


@dataclass
class Settlement:
    """A recommended transfer from one person to another."""

    from_person: str = ""
    to_person: str = ""
    amount: Decimal = Decimal("0")

    def __str__(self) -> str:
        return f"{self.from_person} owes {self.to_person}: ${self.amount:.2f}"


def compute_balances(expenses: List[Expense]) -> dict[str, Decimal]:
    """
    Calculate net balance for each person.

    Positive = they are owed money (creditor).
    Negative = they owe money (debtor).
    """
    balances: dict[str, Decimal] = {}

    for exp in expenses:
        if not exp.participants:
            continue

        # The payer is credited the full amount
        balances[exp.paid_by] = balances.get(exp.paid_by, Decimal("0")) + exp.amount

        # Each participant (including the payer if listed) owes their share
        share = exp.amount / len(exp.participants)
        for p in exp.participants:
            balances[p] = balances.get(p, Decimal("0")) - share

    return balances


def settle_debts(expenses: List[Expense]) -> List[Settlement]:
    """
    Determine the minimum number of transactions needed to settle all debts.

    Uses a greedy algorithm:
    1. Sort creditors by amount owed to them (descending).
    2. Sort debtors by amount they owe (descending — most negative first).
    3. Match the largest debtor to the largest creditor.
    """
    balances = compute_balances(expenses)

    creditors: List[Tuple[str, Decimal]] = []
    debtors: List[Tuple[str, Decimal]] = []

    for person, balance in balances.items():
        if balance > Decimal("0.009"):
            creditors.append((person, balance))
        elif balance < -Decimal("0.009"):
            debtors.append((person, -balance))  # store as positive amount owed

    # Sort descending
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    settlements: List[Settlement] = []

    ci, di = 0, 0
    while ci < len(creditors) and di < len(debtors):
        c_person, c_amount = creditors[ci]
        d_person, d_amount = debtors[di]

        transfer = min(c_amount, d_amount)
        transfer = transfer.quantize(Decimal("0.01"))

        if transfer >= Decimal("0.01"):
            settlements.append(
                Settlement(from_person=d_person, to_person=c_person, amount=transfer)
            )

        creditors[ci] = (c_person, c_amount - transfer)
        debtors[di] = (d_person, d_amount - transfer)

        if creditors[ci][1] < Decimal("0.01"):
            ci += 1
        if debtors[di][1] < Decimal("0.01"):
            di += 1

    return settlements


def format_report(expenses: List[Expense], settlements: List[Settlement]) -> str:
    """Build a human-readable settlement report."""
    lines = ["═══════════════════════════════════", "  TALLYUP — SETTLEMENT REPORT", "═══════════════════════════════════", ""]

    if expenses:
        lines.append("Expenses:")
        for e in expenses:
            parts = ", ".join(e.participants) if e.participants else "(none)"
            lines.append(f"  • {e.description}: ${e.amount:.2f} (paid by {e.paid_by} — shared by {parts})")
        lines.append("")

    if settlements:
        lines.append("Settlements:")
        for s in settlements:
            lines.append(f"  • {s}")
        lines.append("")
        total = sum(s.amount for s in settlements)
        lines.append(f"Total to transfer: ${total:.2f}")
    else:
        lines.append("All settled! No transfers needed.")
        lines.append("")

    return "\n".join(lines)