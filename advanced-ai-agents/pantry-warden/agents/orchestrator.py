"""Orchestrator — coordinates all specialized agents into a unified workflow."""

import json
from typing import Dict, List, Optional

from .inventory_agent import InventoryAgent
from .recipe_agent import RecipeAgent, Recipe
from .nutrition_agent import NutritionAgent, DietaryProfile
from .budget_agent import BudgetAgent, WeeklyBudget
from .schedule_agent import ScheduleAgent, TimeSlot


class Orchestrator:
    """Central coordinator that manages the multi-agent meal planning pipeline.

    Workflow:
    1. INVENTORY: Check what's in the pantry
    2. RECOMMEND: Find recipes matching available ingredients
    3. FILTER: Apply dietary restrictions and nutrition goals
    4. BUDGET: Check costs and optimize
    5. SCHEDULE: Fit meals into weekly time slots
    6. OUTPUT: Generate grocery list and weekly plan
    """

    def __init__(self,
                 inventory: Optional[InventoryAgent] = None,
                 recipes: Optional[RecipeAgent] = None,
                 nutrition: Optional[NutritionAgent] = None,
                 budget: Optional[BudgetAgent] = None,
                 schedule: Optional[ScheduleAgent] = None):
        self.inventory = inventory or InventoryAgent()
        self.recipes = recipes or RecipeAgent()
        self.nutrition = nutrition or NutritionAgent()
        self.budget = budget or BudgetAgent()
        self.schedule = schedule or ScheduleAgent()

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def run_weekly_plan(self,
                        dietary_restrictions: Optional[List[str]] = None,
                        max_calories_per_meal: Optional[int] = None,
                        min_protein_g: Optional[float] = None,
                        weekdays_only: bool = True,
                        dinners_per_week: int = 5,
                        budget_per_meal: Optional[float] = None) -> Dict:
        """Run the full multi-agent orchestration pipeline.

        Returns a complete weekly plan with grocery list.
        """
        # Step 1: Inventory — what do we have?
        available = [i.name for i in self.inventory.list_items()]
        low_stock = self.inventory.get_low_stock_items()
        expiring = self.inventory.get_expiring_items(within_days=3)

        # Step 2: Recipe Agent — find best recipes
        candidates = self.recipes.find_by_ingredients(available, min_coverage=0.3)

        # Step 3: Nutrition Agent — filter by diet
        if dietary_restrictions or max_calories_per_meal or min_protein_g:
            dp = DietaryProfile(
                restrictions=dietary_restrictions,
                max_calories=max_calories_per_meal,
                min_protein_g=min_protein_g,
            )
            self.nutrition.set_profile(dp)
            candidates = self.recipes.filter_by_diet(
                candidates, self.nutrition,
                restrictions=dietary_restrictions,
                max_calories=max_calories_per_meal,
                min_protein=min_protein_g,
            )

        # Step 4: Budget Agent — filter by cost
        if budget_per_meal:
            self.budget.budget.max_per_meal = budget_per_meal
        budget_friendly = []
        for r in candidates:
            if self.budget.within_budget(r.cost_per_serving):
                budget_friendly.append(r)
        candidates = budget_friendly or candidates  # fallback if all excluded

        # Step 5: Schedule Agent — fit into week
        slots = self.schedule.generate_week_slots(
            weekdays_only=weekdays_only,
            dinners_per_week=dinners_per_week,
        )
        recipe_dicts = [r.to_dict() for r in candidates]
        plan = self.schedule.plan_week(recipe_dicts)

        # Step 6: Build grocery list (missing ingredients)
        planned_ids = set()
        for day_meals in plan.values():
            for meal in day_meals:
                planned_ids.add(meal.get("id"))
        planned_recipes = [r for r in self.recipes.recipes if r.id in planned_ids]

        grocery_list = {}
        for r in planned_recipes:
            missing = self.recipes.get_missing_ingredients(r, available)
            for ing in missing:
                grocery_list[ing] = grocery_list.get(ing, 0) + 1

        # Budget check
        meal_dicts = []
        for day_meals in plan.values():
            for m in day_meals:
                meal_dicts.append(m)
        budget_check = self.budget.check_weekly_budget(meal_dicts)

        return {
            "plan": {
                day: [m.get("name", m.get("id")) for m in meals]
                for day, meals in plan.items()
                if meals
            },
            "grocery_list": sorted(grocery_list.items(),
                                    key=lambda x: x[1], reverse=True),
            "budget": budget_check,
            "inventory_summary": {
                "total_items": len(available),
                "low_stock": [i.name for i in low_stock],
                "expiring_soon": [i.name for i in expiring],
            },
            "meals_planned": sum(len(v) for v in plan.values()),
        }

    def inventory_check(self) -> Dict:
        """Quick inventory status — single agent query."""
        return {
            "items": [{"name": i.name, "qty": i.quantity, "unit": i.unit}
                      for i in self.inventory.list_items()],
            "low_stock": [i.name for i in self.inventory.get_low_stock_items()],
            "expiring": [i.name for i in self.inventory.get_expiring_items()],
        }

    def recommend_for_ingredients(self, ingredients: List[str]) -> List[Dict]:
        """Quick recipe recommendation — uses Recipe + Nutrition agents."""
        candidates = self.recipes.find_by_ingredients(ingredients)
        # Score each by nutrition fit
        scored = []
        for r in candidates:
            nutrition_score = self.nutrition.score_meal_nutrition(r.nutrition)
            coverage = sum(1 for i in r.ingredients
                           if i.lower().strip() in {x.lower() for x in ingredients})
            combined = (coverage / len(r.ingredients)) * 0.6 + nutrition_score * 0.4
            scored.append((combined, r))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [r.to_dict() for _, r in scored[:5]]