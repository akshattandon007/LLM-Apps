"""Scenario Engine — pure financial math engine. No LLM calls.

Handles: amortization, compound interest, PMT, FV, inflation adjustment,
opportunity cost, debt snowball projections."""

import math
from models import FinancialProfile, Goal, ScenarioResult


class ScenarioEngine:
    """Workhorse financial calculator. Runs the numbers for any 'what-if'."""

    def __init__(self):
        self.name = "ScenarioEngine"

    # ── Public API ──────────────────────────────────────────────────────

    def project(self, profile: FinancialProfile, goal: Goal, years: int = 5,
                adjustments: dict | None = None) -> ScenarioResult:
        """Project financial outcome under a given adjustment scenario."""
        adj = adjustments or {}
        adj_profile = self._apply_adjustments(profile, adj)

        monthly_surplus = adj_profile.compute_surplus()
        # Debt impact
        debt_monthly = self._debt_payment(adj_profile.debt, adj_profile.debt_interest)

        # Project savings growth month by month
        savings_trajectory = []
        balance = adj_profile.savings
        target = goal.amount_needed()

        for m in range(1, years * 12 + 1):
            available = monthly_surplus - debt_monthly
            if available > 0:
                balance += available
            # Compound interest on savings (conservative 4% APY)
            if m % 12 == 0 and balance > 0:
                balance *= 1.04

            # Debt snowball — once debt is gone, that payment adds to savings
            if adj_profile.debt > 0 and m % 12 == 0:
                adj_profile.debt = max(0, adj_profile.debt - debt_monthly * 12)
                if adj_profile.debt <= 0:
                    debt_monthly = 0

            if m % 12 == 0:
                savings_trajectory.append({"year": m // 12, "savings": round(balance, 2),
                                           "surplus": round(monthly_surplus, 2)})

        total_savings = balance
        goal_progress = min(100.0, (total_savings / target * 100)) if target > 0 else 0.0
        goal_met = total_savings >= target

        # Risk assessment
        risk = self._assess_risk(monthly_surplus, adj_profile.savings,
                                 adj_profile.debt, goal_met)

        return ScenarioResult(
            scenario_name=list(adjustments.keys())[0] if adjustments else "Baseline",
            projected_surplus_5y=round(monthly_surplus, 2),
            total_savings_5y=round(total_savings, 2),
            goal_met=goal_met,
            goal_progress_pct=round(goal_progress, 1),
            risk_level=risk,
            summary=self._generate_summary(monthly_surplus, total_savings,
                                            target, goal_met, risk),
            monthly_breakdown=savings_trajectory,
        )

    def project_comparison(self, profile: FinancialProfile, goal: Goal,
                           scenarios: list[tuple[str, dict]]) -> list[ScenarioResult]:
        """Run multiple scenarios and return all results."""
        results = []
        # Baseline (no adjustments)
        results.append(self.project(profile, goal, adjustments={}))
        for name, adj in scenarios:
            results.append(self.project(profile, goal, years=5, adjustments=adj))
        return results

    # ── Internal ────────────────────────────────────────────────────────

    def _apply_adjustments(self, profile: FinancialProfile,
                           adjustments: dict) -> FinancialProfile:
        """Return a modified profile copy with adjustments applied."""
        import copy
        p = copy.deepcopy(profile)

        if "income_boost" in adjustments:
            # Add extra annual income
            p.income_streams[0].amount += adjustments["income_boost"]

        if "cut_expenses" in adjustments:
            # Reduce monthly expenses by dollar amount or percentage
            cut = adjustments["cut_expenses"]
            if isinstance(cut, str) and cut.endswith("%"):
                pct = float(cut.rstrip("%")) / 100.0
                for e in p.expenses:
                    e.amount *= (1 - pct)
            else:
                # Distribute cuts proportionally across non-essential items
                cut_amount = float(cut)
                non_ess = [e for e in p.expenses if not e.essential]
                if non_ess:
                    per_item = cut_amount / len(non_ess)
                    for e in non_ess:
                        e.amount = max(0, e.amount - per_item)
                else:
                    # cut essential too
                    per_item = cut_amount / len(p.expenses)
                    for e in p.expenses:
                        e.amount = max(0, e.amount - per_item)

        if "save_more" in adjustments:
            extra_save = adjustments["save_more"]
            p.monthly_surplus += extra_save  # effectively adds to savings

        if "debt_paydown" in adjustments:
            paydown = adjustments["debt_paydown"]
            p.debt = max(0, p.debt - paydown)

        if "new_expense" in adjustments:
            from models import Expense
            p.expenses.append(Expense(
                name="new_expense",
                amount=float(adjustments["new_expense"]),
                essential=True,
            ))

        return p

    def _debt_payment(self, debt: float, interest_rate: float,
                      term_months: int = 60) -> float:
        """Monthly payment for fully amortizing a debt (standard loan formula)."""
        if debt <= 0 or interest_rate <= 0:
            return 0.0
        r = interest_rate / 12
        if r <= 0:
            return debt / term_months
        payment = debt * (r * (1 + r) ** term_months) / ((1 + r) ** term_months - 1)
        return payment

    def _assess_risk(self, surplus: float, savings: float,
                     debt: float, goal_met: bool) -> str:
        """Assess financial risk level."""
        risks = 0
        if surplus < 0:
            risks += 2  # negative cash flow is high risk
        elif surplus < 200:
            risks += 1
        if savings < 1000:
            risks += 1
        if debt > 10000:
            risks += 1
        if not goal_met:
            risks += 1
        if risks >= 3:
            return "high"
        elif risks >= 1:
            return "medium"
        return "low"

    def _generate_summary(self, surplus: float, savings: float,
                          target: float, goal_met: bool, risk: str) -> str:
        lines = [
            f"Monthly surplus: ${surplus:,.0f}",
            f"Projected savings (5yr): ${savings:,.0f}",
            f"Goal target: ${target:,.0f}",
            f"Goal met: {'Yes' if goal_met else 'No'}",
            f"Risk level: {risk.upper()}",
        ]
        if not goal_met and target > 0:
            gap = target - savings
            lines.append(f"Shortfall: ${gap:,.0f} ({'-' if gap < 0 else ''}{(gap/target*100):.0f}%)")
        return " | ".join(lines)