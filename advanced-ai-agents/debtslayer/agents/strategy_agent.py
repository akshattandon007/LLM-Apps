"""Agent: Strategy Agent — computes avalanche vs snowball payoff plans."""
from __future__ import annotations
from math import ceil
from ..models import Debt, PayoffPlan


class StrategyAgent:
    """Computes debt payoff strategies: avalanche (lowest total interest) vs snowball (quickest wins)."""

    MIN_MONTHLY_SURPLUS = 5.0  # at least $5/mo extra to matter

    def compute_plan(
        self,
        debts: list[Debt],
        monthly_surplus: float,
        method: str = "avalanche",
    ) -> PayoffPlan:
        """Compute a complete payoff timeline for the given method.
        
        Args:
            debts: List of debt accounts
            monthly_surplus: Monthly amount available beyond minimum payments
            method: "avalanche" (highest APR first) or "snowball" (smallest balance first)
        
        Returns:
            PayoffPlan with timeline and total interest.
        """
        if method == "avalanche":
            ordered = sorted(debts, key=lambda d: d.apr, reverse=True)
        else:
            ordered = sorted(debts, key=lambda d: d.balance)

        # Simulate month-by-month payoff
        balances = {d.label: d.balance for d in ordered}
        aprs = {d.label: d.apr for d in ordered}
        min_pays = {d.label: d.min_payment for d in ordered}
        debt_labels_in_order = [d.label for d in ordered]

        total_interest = 0.0
        month = 0
        schedule = []
        payoff_months: dict[str, int] = {}
        target_index = 0  # which debt we're currently throwing surplus at

        while any(b > 0.01 for b in balances.values()):
            month += 1
            month_data = {"month": month, "payments": {}, "balances": {}}

            # Apply interest to all active debts
            for label in debt_labels_in_order:
                if balances[label] > 0.01:
                    interest = balances[label] * (aprs[label] / 100.0 / 12.0)
                    balances[label] += interest
                    total_interest += interest

            # Make minimum payments on all debts
            remaining = 0.0
            for label in debt_labels_in_order:
                if balances[label] > 0.01:
                    pmt = min(min_pays[label], balances[label])
                    balances[label] -= pmt
                    remaining += pmt
                    month_data["payments"][label] = round(pmt, 2)

            # Apply surplus to the target debt
            surplus_this_month = monthly_surplus
            # Find the current target (first non-paid-off debt in order)
            while (target_index < len(debt_labels_in_order) and
                   balances[debt_labels_in_order[target_index]] <= 0.01):
                if debt_labels_in_order[target_index] not in payoff_months:
                    payoff_months[debt_labels_in_order[target_index]] = month
                target_index += 1

            if target_index < len(debt_labels_in_order):
                target = debt_labels_in_order[target_index]
                extra = min(surplus_this_month, balances[target])
                balances[target] -= extra
                if label not in month_data["payments"]:
                    month_data["payments"][label] = 0.0
                month_data["payments"][target] = round(month_data["payments"].get(target, 0) + extra, 2)

            # Record balances
            for label in debt_labels_in_order:
                month_data["balances"][label] = round(max(balances[label], 0), 2)

            schedule.append(month_data)

            # Safety valve
            if month > 1200:
                break

        # Record final payoff months
        for label in debt_labels_in_order:
            if label not in payoff_months:
                payoff_months[label] = month

        return PayoffPlan(
            debts=ordered,
            monthly_surplus=monthly_surplus,
            method=method,
            months_to_payoff=month,
            total_interest=round(total_interest, 2),
            payment_schedule=schedule,
        )

    def compare_strategies(
        self, debts: list[Debt], monthly_surplus: float
    ) -> dict:
        """Compare avalanche vs snowball and recommend the best."""
        if monthly_surplus < self.MIN_MONTHLY_SURPLUS:
            return {
                "recommendation": "none",
                "reason": "Monthly surplus too small for any strategy to work.",
                "avalanche": None,
                "snowball": None,
            }

        av_plan = self.compute_plan(debts, monthly_surplus, "avalanche")
        sb_plan = self.compute_plan(debts, monthly_surplus, "snowball")

        interest_saved_av = max(0, av_plan.total_interest - sb_plan.total_interest)

        # Avalanche is better if it saves meaningful interest
        # Snowball is better if it's close in interest but pays off faster psychologically
        if av_plan.total_interest <= sb_plan.total_interest * 0.95:
            recommendation = "avalanche"
            reason = "Avalanche saves the most in total interest paid."
        elif sb_plan.months_to_payoff <= av_plan.months_to_payoff * 0.9:
            recommendation = "snowball"
            reason = "Snowball delivers quicker psychological wins."
        else:
            recommendation = "avalanche"
            reason = "Avalanche and snowball are nearly tied — avalanche saves slightly more."

        return {
            "recommendation": recommendation,
            "reason": reason,
            "interest_saved_vs_alternative": round(interest_saved_av, 2),
            "avalanche": {
                "months": av_plan.months_to_payoff,
                "total_interest": av_plan.total_interest,
            },
            "snowball": {
                "months": sb_plan.months_to_payoff,
                "total_interest": sb_plan.total_interest,
            },
        }