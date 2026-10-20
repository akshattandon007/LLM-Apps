"""Agent: Progress Agent — tracks payoff progress over time."""
from __future__ import annotations
from datetime import datetime, date
from ..models import PayoffPlan


class ProgressAgent:
    """Monitors progress toward debt payoff and generates status reports."""

    @staticmethod
    def progress_summary(plan: PayoffPlan, payments_made: int = 0) -> dict:
        """Generate a progress summary based on the plan and payments made."""
        pct_complete = min(
            100.0, round((payments_made / plan.months_to_payoff) * 100, 1)
        ) if plan.months_to_payoff > 0 else 0.0

        months_remaining = max(0, plan.months_to_payoff - payments_made)

        return {
            "method": plan.method,
            "total_months": plan.months_to_payoff,
            "months_completed": payments_made,
            "months_remaining": months_remaining,
            "percent_complete": pct_complete,
            "projected_completion": self._projected_date(plan.months_to_payoff),
            "total_interest_estimated": plan.total_interest,
            "interest_paid_so_far": round(
                plan.total_interest * (payments_made / plan.months_to_payoff), 2
            ) if plan.months_to_payoff > 0 else 0.0,
            "on_track": pct_complete >= self._expected_progress(plan.months_to_payoff, payments_made),
        }

    @staticmethod
    def _projected_date(months_remaining: int) -> str:
        from calendar import month_name
        d = date.today()
        target_month = (d.month - 1 + months_remaining) % 12 + 1
        target_year = d.year + ((d.month - 1 + months_remaining) // 12)
        return f"{month_name[target_month]} {target_year}"

    @staticmethod
    def _expected_progress(total_months: int, elapsed: int) -> float:
        """What percentage should be complete by now (linear)."""
        if total_months <= 0:
            return 100.0
        return round((elapsed / total_months) * 100, 1)