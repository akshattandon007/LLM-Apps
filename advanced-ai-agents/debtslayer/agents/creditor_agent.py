"""Agent: Creditor Agent — tracks and manages individual debt accounts."""
from __future__ import annotations
from ..models import Debt


class CreditorAgent:
    """Specialist agent that manages a user's debt inventory."""

    def __init__(self):
        self.debts: list[Debt] = []

    def add_debt(self, label: str, balance: float, apr: float, min_payment: float) -> Debt:
        """Add a single debt account."""
        debt = Debt(label=label, balance=balance, apr=apr, min_payment=min_payment)
        self.debts.append(debt)
        return debt

    def remove_debt(self, label: str) -> bool:
        """Remove a debt by label. Returns True if found and removed."""
        before = len(self.debts)
        self.debts = [d for d in self.debts if d.label.lower() != label.lower()]
        return len(self.debts) < before

    def total_balance(self) -> float:
        return sum(d.balance for d in self.debts)

    def total_min_payments(self) -> float:
        return sum(d.min_payment for d in self.debts)

    def summary_lines(self) -> list[str]:
        """Return human-readable inventory lines."""
        lines = []
        for i, d in enumerate(self.debts, 1):
            lines.append(
                f"{i}. {d.label:15s}  ${d.balance:>8,.2f} @ {d.apr:.2f}%  "
                f"(min ${d.min_payment:.2f}/mo)"
            )
        return lines

    def sort_by_apr(self, reverse: bool = True) -> list[Debt]:
        """Sort debts by APR descending (avalanche order) or ascending."""
        return sorted(self.debts, key=lambda d: d.apr, reverse=reverse)

    def sort_by_balance(self, reverse: bool = False) -> list[Debt]:
        """Sort debts by balance ascending (snowball order) or descending."""
        return sorted(self.debts, key=lambda d: d.balance, reverse=reverse)