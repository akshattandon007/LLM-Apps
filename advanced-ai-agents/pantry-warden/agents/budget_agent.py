"""BudgetAgent — estimates meal costs and optimizes for budget."""

from typing import Dict, List, Optional


class WeeklyBudget:
    """User's weekly grocery budget."""
    def __init__(self, weekly_total: float = 100.0,
                 max_per_meal: float = 7.0,
                 currency: str = "$"):
        self.weekly_total = weekly_total
        self.max_per_meal = max_per_meal
        self.currency = currency


class BudgetAgent:
    """Specialized agent that estimates and optimizes meal costs.

    Capabilities:
    - Estimate per-meal cost
    - Check against per-meal and weekly budget
    - Suggest cheaper ingredient substitutions
    - Track weekly spend
    """

    def __init__(self, budget: Optional[WeeklyBudget] = None):
        self.budget = budget or WeeklyBudget()
        self._weekly_spend = 0.0

    def set_budget(self, budget: WeeklyBudget):
        self.budget = budget

    def estimate_meal_cost(self, recipe_ingredients: List[str],
                            cost_per_serving: float) -> float:
        """Return cost estimate for a single serving."""
        return cost_per_serving

    def within_budget(self, meal_cost: float) -> bool:
        """Check if a meal is within per-meal budget."""
        return meal_cost <= self.budget.max_per_meal

    def check_weekly_budget(self, planned_meals: List[Dict]) -> Dict:
        """Check if a week of meals fits the weekly budget."""
        total = sum(m.get("cost_per_serving", 0) for m in planned_meals)
        remaining = self.budget.weekly_total - total
        return {
            "planned_spend": round(total, 2),
            "budget_limit": self.budget.weekly_total,
            "remaining": round(remaining, 2),
            "within_budget": remaining >= 0,
        }

    def suggest_cheaper_meals(self, meals: List[Dict],
                              max_cost: Optional[float] = None) -> List[Dict]:
        """Filter meals under a cost threshold."""
        limit = max_cost or self.budget.max_per_meal
        return [m for m in meals if m.get("cost_per_serving", 0) <= limit]

    def record_spend(self, cost: float):
        """Add a meal cost to the weekly running total."""
        self._weekly_spend += cost

    def reset_weekly(self):
        self._weekly_spend = 0.0