"""Agent: Spending Agent — analyzes income vs expenses to find surplus."""
from __future__ import annotations
from ..models import SpendingProfile


class SpendingAgent:
    """Analyzes a user's income and spending to determine available surplus."""

    def __init__(self, income: float = 0.0, expenses: float = 0.0):
        self.profile = SpendingProfile(income=income, expenses=expenses)

    def set_profile(self, income: float, expenses: float) -> None:
        self.profile = SpendingProfile(income=income, expenses=expenses)

    @property
    def surplus(self) -> float:
        return self.profile.surplus

    @property
    def is_deficit(self) -> bool:
        return self.profile.deficit

    def analyze(self) -> dict:
        """Return structured analysis of the spending situation."""
        return {
            "monthly_income": self.profile.income,
            "monthly_expenses": self.profile.expenses,
            "monthly_surplus": self.profile.surplus,
            "deficit": self.profile.deficit,
            "savings_rate_pct": round(
                (self.profile.surplus / self.profile.income) * 100, 1
            ) if self.profile.income > 0 else 0.0,
        }

    def suggestions(self) -> list[str]:
        """Generate cost-saving suggestions (rule-of-thumb based)."""
        tips = []
        ratio = self.profile.expenses / self.profile.income if self.profile.income > 0 else 1
        if ratio > 0.5:
            tips.append("Your essential expenses exceed 50% of income — consider trimming subscriptions.")
        if self.profile.income < 2000:
            tips.append("Increasing income (side gig, OT) would accelerate debt payoff significantly.")
        if self.profile.surplus < 100:
            tips.append("Very tight surplus — every dollar counts. Look for small recurring charges.")
        if not tips:
            tips.append("Your budget looks manageable. Stick to the plan and you'll see progress.")
        return tips