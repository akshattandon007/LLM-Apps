"""Goal Tracker — monitors goal progress, suggests contribution adjustments."""

from models import FinancialProfile, Goal


class GoalTracker:
    """Evaluates goal feasibility and recommends monthly contribution targets."""

    def __init__(self):
        self.name = "GoalTracker"

    def process(self, profile: FinancialProfile, goal: Goal,
                projected_surplus: float) -> dict:
        """Analyze goal feasibility given current financial reality."""
        monthly_needed = goal.amount_needed() / (goal.target_date_years * 12)
        feasible = projected_surplus >= monthly_needed
        gap = monthly_needed - projected_surplus

        result = {
            "goal": goal.name,
            "target": goal.target_amount,
            "monthly_needed": round(monthly_needed, 2),
            "monthly_surplus": round(projected_surplus, 2),
            "feasible": feasible,
            "gap_per_month": round(max(0, gap), 2),
        }

        status = "ON TRACK" if feasible else "NEEDS ADJUSTMENT"
        print(f"  [GoalTracker] '{goal.name}': {status} "
              f"(${projected_surplus:,.0f}/mo surplus vs ${monthly_needed:,.0f}/mo needed)")
        return result

    def suggest_contribution(self, goal: Goal, surplus: float) -> dict:
        """Suggest optimal monthly contribution toward goal."""
        months = goal.target_date_years * 12
        needed_per_month = goal.amount_needed() / months
        suggested = min(surplus * 0.7, needed_per_month * 1.1)  # leave 30% buffer
        years_to_goal = months / 12 if suggested > 0 else float('inf')

        return {
            "goal": goal.name,
            "suggested_monthly": round(suggested, 2),
            "estimated_years": round(years_to_goal, 1) if years_to_goal != float('inf') else None,
            "surplus_used_pct": round((suggested / surplus) * 100, 0) if surplus > 0 else 0,
        }