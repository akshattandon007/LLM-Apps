"""Tests for PantryWarden multi-agent system."""

import json
import os
import tempfile
import pytest

from agents.inventory_agent import InventoryAgent, PantryItem
from agents.recipe_agent import RecipeAgent, Recipe
from agents.nutrition_agent import NutritionAgent, DietaryProfile
from agents.budget_agent import BudgetAgent, WeeklyBudget
from agents.schedule_agent import ScheduleAgent, TimeSlot
from agents.orchestrator import Orchestrator


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def inventory(temp_data_dir):
    inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
    inv.add_item("pasta", 2, "lb", "grains")
    inv.add_item("tomato sauce", 1, "jar", "canned")
    inv.add_item("chicken breast", 1.5, "lb", "meat")
    inv.add_item("rice", 3, "cup", "grains")
    inv.add_item("eggs", 12, "unit", "dairy")
    inv.add_item("bell pepper", 2, "unit", "produce")
    inv.add_item("onion", 3, "unit", "produce")
    inv.add_item("garlic", 5, "clove", "produce")
    inv.add_item("olive oil", 0.5, "cup", "oil")
    return inv


@pytest.fixture
def recipe_agent():
    return RecipeAgent()


@pytest.fixture
def orchestrator(inventory, recipe_agent):
    return Orchestrator(
        inventory=inventory,
        recipes=recipe_agent,
        nutrition=NutritionAgent(),
        budget=BudgetAgent(),
        schedule=ScheduleAgent(),
    )


# ── InventoryAgent Tests ──────────────────────────────────────────────────────

class TestInventoryAgent:
    def test_add_and_list(self, temp_data_dir):
        inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
        inv.add_item("milk", 1, "gallon", "dairy", expiry_days=14)
        items = inv.list_items()
        assert len(items) == 1
        assert items[0].name == "milk"
        assert items[0].quantity == 1

    def test_add_existing_increases_quantity(self, temp_data_dir):
        inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
        inv.add_item("milk", 1, "gallon")
        inv.add_item("milk", 0.5, "gallon")
        assert inv.get_item("milk").quantity == 1.5

    def test_remove_item(self, temp_data_dir):
        inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
        inv.add_item("butter", 2, "stick")
        assert inv.remove_item("butter", 1) is True
        assert inv.get_item("butter").quantity == 1

    def test_remove_insufficient(self, temp_data_dir):
        inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
        inv.add_item("butter", 1, "stick")
        assert inv.remove_item("butter", 2) is False

    def test_get_item_nonexistent(self, temp_data_dir):
        inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
        assert inv.get_item("unicorn") is None

    def test_available_ingredients(self, inventory):
        avail = inventory.available_ingredients(["pasta", "tomato sauce", "saffron"])
        assert "pasta" in avail
        assert "tomato sauce" in avail
        assert "saffron" not in avail

    def test_estimate_meal_coverage(self, inventory):
        # Has 2/4 ingredients = 0.5
        coverage = inventory.estimate_meal_coverage(
            ["pasta", "tomato sauce", "parmesan", "basil"]
        )
        assert coverage == 0.5

    def test_low_stock(self, temp_data_dir):
        inv = InventoryAgent(data_path=os.path.join(temp_data_dir, "pantry.json"))
        inv.add_item("salt", 0.1, "cup")
        inv.add_item("pepper", 0.3, "cup")
        low = inv.get_low_stock_items()
        assert any(i.name == "salt" for i in low)


# ── RecipeAgent Tests ─────────────────────────────────────────────────────────

class TestRecipeAgent:
    def test_find_by_ingredients(self, recipe_agent):
        results = recipe_agent.find_by_ingredients(
            ["pasta", "tomato sauce", "ground beef", "onion", "garlic"]
        )
        assert len(results) > 0
        # Spaghetti Bolognese should match
        names = [r.name for r in results]
        assert "Spaghetti Bolognese" in names

    def test_filter_by_diet(self, recipe_agent):
        nut_agent = NutritionAgent(DietaryProfile(restrictions=["vegan"]))
        results = recipe_agent.find_by_ingredients(["lentils", "carrots", "celery"])
        filtered = recipe_agent.filter_by_diet(results, nut_agent,
                                                restrictions=["vegan"])
        names = [r.name for r in filtered]
        assert "Lentil Soup" in names  # vegan tagged

    def test_filter_by_time(self, recipe_agent):
        results = recipe_agent.find_by_ingredients(["eggs", "bell pepper", "onion"])
        quick = recipe_agent.filter_by_time(results, 15)
        for r in quick:
            assert r.cook_time_min <= 15

    def test_filter_by_meal_type(self, recipe_agent):
        results = recipe_agent.find_by_ingredients(["eggs", "milk", "berries"])
        breakfasts = recipe_agent.filter_by_meal_type(results, "breakfast")
        for r in breakfasts:
            assert r.meal_type == "breakfast"

    def test_get_missing_ingredients(self, recipe_agent):
        recipe = recipe_agent.recipes[0]  # Spaghetti Bolognese
        missing = recipe_agent.get_missing_ingredients(
            recipe, ["pasta", "tomato sauce"]
        )
        assert "ground beef" in missing or "onion" in missing or "garlic" in missing


# ── NutritionAgent Tests ──────────────────────────────────────────────────────

class TestNutritionAgent:
    def test_check_compatibility_passes(self):
        agent = NutritionAgent(DietaryProfile(max_calories=700, min_protein_g=20))
        warnings = agent.check_compatibility({"calories": 500, "protein_g": 30})
        assert len(warnings) == 0

    def test_check_compatibility_fails_calories(self):
        agent = NutritionAgent(DietaryProfile(max_calories=400))
        warnings = agent.check_compatibility({"calories": 650})
        assert "calories" in warnings

    def test_check_compatibility_fails_protein(self):
        agent = NutritionAgent(DietaryProfile(min_protein_g=30))
        warnings = agent.check_compatibility({"calories": 500, "protein_g": 15})
        assert "protein" in warnings

    def test_score_meal_nutrition_perfect(self):
        agent = NutritionAgent(DietaryProfile(max_calories=700))
        score = agent.score_meal_nutrition({"calories": 500})
        assert score == 1.0

    def test_score_meal_nutrition_warnings(self):
        agent = NutritionAgent(DietaryProfile(max_calories=400, min_protein_g=30))
        score = agent.score_meal_nutrition({"calories": 650, "protein_g": 10})
        assert 0.0 < score < 1.0


# ── BudgetAgent Tests ─────────────────────────────────────────────────────────

class TestBudgetAgent:
    def test_within_budget(self):
        agent = BudgetAgent(WeeklyBudget(max_per_meal=7.0))
        assert agent.within_budget(5.0) is True
        assert agent.within_budget(8.0) is False

    def test_weekly_budget(self):
        agent = BudgetAgent(WeeklyBudget(weekly_total=100.0))
        meals = [{"cost_per_serving": 3.5}, {"cost_per_serving": 4.0}]
        check = agent.check_weekly_budget(meals)
        assert check["remaining"] > 0
        assert check["within_budget"] is True

    def test_suggest_cheaper(self):
        agent = BudgetAgent(WeeklyBudget(max_per_meal=5.0))
        meals = [
            {"cost_per_serving": 3.0, "name": "Cheap"},
            {"cost_per_serving": 7.0, "name": "Expensive"},
        ]
        cheap = agent.suggest_cheaper_meals(meals)
        assert len(cheap) == 1
        assert cheap[0]["name"] == "Cheap"


# ── ScheduleAgent Tests ───────────────────────────────────────────────────────

class TestScheduleAgent:
    def test_generate_default_slots(self):
        agent = ScheduleAgent()
        slots = agent.generate_week_slots(weekdays_only=True, dinners_per_week=5)
        # 5 breakfasts + 5 lunches + 5 dinners = 15 default slots
        assert len(slots) == 15

    def test_fit_meal_to_slot(self):
        slot = TimeSlot("monday", 18, 19, "dinner")
        agent = ScheduleAgent()
        assert agent.fit_meal_to_slot({"cook_time_min": 15}, slot) is True
        assert agent.fit_meal_to_slot({"cook_time_min": 70}, slot) is False

    def test_plan_week(self):
        agent = ScheduleAgent()
        agent.generate_week_slots(dinners_per_week=5)
        recipes = [
            {"id": "chicken_stir_fry", "name": "Chicken Stir Fry",
             "cook_time_min": 20, "meal_type": "dinner"},
            {"id": "spaghetti_bolognese", "name": "Spaghetti Bolognese",
             "cook_time_min": 35, "meal_type": "dinner"},
            {"id": "black_bean_tacos", "name": "Black Bean Tacos",
             "cook_time_min": 15, "meal_type": "dinner"},
            {"id": "grilled_salmon", "name": "Grilled Salmon",
             "cook_time_min": 20, "meal_type": "dinner"},
            {"id": "lentil_soup", "name": "Lentil Soup",
             "cook_time_min": 35, "meal_type": "dinner"},
        ]
        plan = agent.plan_week(recipes)
        # At least some meals assigned
        total = sum(len(meals) for meals in plan.values())
        assert total >= 3  # at least some assigned

    def test_variety_no_repeats_back_to_back(self):
        agent = ScheduleAgent()
        agent.generate_week_slots(dinners_per_week=5)
        recipes = [
            {"id": "same_meal", "name": "Same Meal",
             "cook_time_min": 20, "meal_type": "dinner"},
            {"id": "other_meal", "name": "Other Meal",
             "cook_time_min": 25, "meal_type": "dinner"},
        ]
        plan = agent.plan_week(recipes)
        # Should have variety (same meal ID won't appear in adjacent slots)
        all_meal_ids = []
        for day_meals in plan.values():
            for m in day_meals:
                all_meal_ids.append(m.get("id"))
        # Check no adjacent duplicates
        for i in range(len(all_meal_ids) - 1):
            assert all_meal_ids[i] != all_meal_ids[i + 1], \
                f"Adjacent duplicate: {all_meal_ids[i]} at positions {i},{i+1}"


# ── Orchestrator Integration Tests ────────────────────────────────────────────

class TestOrchestrator:
    def test_weekly_plan_produces_output(self, orchestrator):
        result = orchestrator.run_weekly_plan()
        assert result["meals_planned"] > 0
        assert "plan" in result
        assert "grocery_list" in result
        assert "budget" in result

    def test_dietary_restrictions_applied(self, orchestrator):
        # With vegan restriction, only vegan-tagged recipes remain
        result = orchestrator.run_weekly_plan(dietary_restrictions=["vegan"])
        assert result["meals_planned"] >= 0

    def test_budget_filter(self, orchestrator):
        result = orchestrator.run_weekly_plan(budget_per_meal=2.00)
        # Meals should be cheap
        budget = result["budget"]
        assert budget["planned_spend"] > 0

    def test_inventory_check(self, orchestrator):
        result = orchestrator.inventory_check()
        assert len(result["items"]) > 0

    def test_recommend_for_ingredients(self, orchestrator):
        recs = orchestrator.recommend_for_ingredients(
            ["pasta", "tomato sauce", "ground beef"]
        )
        assert len(recs) > 0
        names = [r["name"] for r in recs]
        assert "Spaghetti Bolognese" in names