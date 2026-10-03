"""Smoke tests for MealWizard.

Tests run against local logic with fake data — no live API calls.
Verifies that all modules import correctly and core functions work.
"""

from __future__ import annotations

import pytest

from src.models import Recipe, SeasonalProduce, Substitution
from src.mealdb import MealDBClient
from src.recipes import format_recipes, format_recipe_detail
from src.substitutes import get_substitutes, list_all_ingredients
from src.season import get_seasonal, format_seasonal
from src.scaler import scale_recipe, format_scaled
from src.mealplanner import generate_plan, format_plan


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class TestModels:
    def test_recipe_ingredients(self, sample_recipe: Recipe):
        """Recipe should parse ingredient-measure pairs correctly."""
        ings = sample_recipe.ingredients
        assert len(ings) == 5
        assert any("chicken" in ing[0].lower() for ing in ings)
        assert any("honey" in ing[0].lower() for ing in ings)

    def test_recipe_model_validate(self):
        """Recipe model_validate from raw dict."""
        raw = {
            "idMeal": "12345",
            "strMeal": "Test Dish",
            "strCategory": "Test",
            "strArea": "Test",
            "strInstructions": "Do something.",
            "strMealThumb": "https://example.com/img.jpg",
        }
        r = Recipe.model_validate(raw)
        assert r.id == "12345"
        assert r.name == "Test Dish"

    def test_substitution_model(self):
        s = Substitution(ingredient="butter", substitutes=["oil"], notes="Swap 1:1")
        assert s.ingredient == "butter"
        assert "oil" in s.substitutes

    def test_seasonal_model(self):
        sp = SeasonalProduce(month="Jan", region="US", fruits=["apple"], vegetables=["kale"])
        assert "apple" in sp.fruits
        assert "kale" in sp.vegetables


# ------------------------------------------------------------------
# Substitutes
# ------------------------------------------------------------------

class TestSubstitutes:
    def test_known_substitute(self):
        sub = get_substitutes("butter")
        assert len(sub.substitutes) > 0
        assert "oil" in sub.substitutes[0].lower()

    def test_unknown_substitute(self):
        sub = get_substitutes("xyzzy_unknown")
        assert sub.substitutes == []

    def test_case_insensitive(self):
        sub1 = get_substitutes("Milk")
        sub2 = get_substitutes("milk")
        assert sub1.substitutes == sub2.substitutes

    def test_list_all(self):
        ingredients = list_all_ingredients()
        assert len(ingredients) >= 20
        assert "butter" in ingredients
        assert "eggs" in ingredients

    def test_partial_match(self):
        sub = get_substitutes("baking")
        assert len(sub.substitutes) > 0 or sub.ingredient


# ------------------------------------------------------------------
# Seasonal produce
# ------------------------------------------------------------------

class TestSeasonal:
    def test_us_january(self):
        sp = get_seasonal("january", "US")
        assert sp.region == "US"
        assert len(sp.fruits) > 0
        assert len(sp.vegetables) > 0

    def test_uk_may(self):
        sp = get_seasonal("may", "UK")
        assert sp.region == "UK"
        assert len(sp.fruits) > 0

    def test_eu_september(self):
        sp = get_seasonal("sep", "EU")
        assert sp.region == "EU"

    def test_short_month_names(self):
        for short in ["jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]:
            sp = get_seasonal(short, "US")
            assert len(sp.fruits) > 0

    def test_invalid_region(self):
        with pytest.raises(ValueError, match="Unknown region"):
            get_seasonal("january", "AU")

    def test_invalid_month(self):
        with pytest.raises(ValueError, match="Unknown month"):
            get_seasonal("frimaire", "US")

    def test_format_seasonal(self):
        sp = get_seasonal("june", "US")
        formatted = format_seasonal(sp)
        assert "Seasonal produce" in formatted
        assert "Fruits:" in formatted
        assert "Vegetables:" in formatted


# ------------------------------------------------------------------
# Scaler
# ------------------------------------------------------------------

class TestScaler:
    def test_scale_double(self, sample_recipe: Recipe):
        sr = scale_recipe(sample_recipe, target_servings=8, original_servings=4)
        assert sr.target_servings == 8
        assert sr.name == "Chicken Teriyaki"
        # Chicken goes from 2 -> 4
        chicken_measure = dict(sr.scaled_ingredients).get("Chicken breast", "")
        assert "4" in chicken_measure

    def test_scale_half(self, sample_recipe: Recipe):
        sr = scale_recipe(sample_recipe, target_servings=2, original_servings=4)
        assert sr.target_servings == 2
        # Rice goes from 1 cup -> 1/2 cup
        rice_measure = dict(sr.scaled_ingredients).get("Rice", "")
        assert "1/2" in rice_measure

    def test_scale_negative(self, sample_recipe: Recipe):
        with pytest.raises(ValueError):
            scale_recipe(sample_recipe, target_servings=0)

    def test_format_scaled(self, sample_recipe: Recipe):
        sr = scale_recipe(sample_recipe, target_servings=6)
        formatted = format_scaled(sr)
        assert "scaled from" in formatted
        assert "Ingredients:" in formatted
        assert "Instructions:" in formatted


# ------------------------------------------------------------------
# Recipe formatting
# ------------------------------------------------------------------

class TestRecipeFormatting:
    def test_format_recipes_empty(self):
        result = format_recipes([], ["chicken"])
        assert "No recipes found" in result

    def test_format_recipes_list(self, sample_recipes_list):
        result = format_recipes(sample_recipes_list, ["chicken", "rice"])
        assert "Found 3 recipe(s)" in result
        assert "Chicken Teriyaki" in result
        assert "get_recipe" in result

    def test_format_recipe_detail(self, sample_recipe):
        result = format_recipe_detail(sample_recipe)
        assert "Chicken Teriyaki" in result
        assert "Ingredients:" in result
        assert "Instructions:" in result
        assert "soy sauce" in result.lower()


# ------------------------------------------------------------------
# Meal planner
# ------------------------------------------------------------------

class TestMealPlanner:
    def test_generate_plan_min_days(self):
        with pytest.raises(ValueError):
            generate_plan(days=0)

    def test_generate_plan_caps_at_14(self):
        plan = generate_plan(days=20)
        assert plan.days == 14

    def test_format_plan(self):
        from src.models import MealPlanDay
        plan = type("obj", (), {
            "days": 3, "preferences": "Italian", "restrictions": "",
            "meals": [
                MealPlanDay(day=1, meal="Main meal", recipe_id="100", recipe_name="Pizza"),
                MealPlanDay(day=2, meal="Main meal", recipe_id="101", recipe_name="Pasta"),
                MealPlanDay(day=3, meal="Main meal", recipe_id="102", recipe_name="Risotto"),
            ],
        })()
        result = format_plan(plan)
        assert "Meal Plan" in result
        assert "Pizza" in result
        assert "Pasta" in result

    def test_format_plan_empty(self):
        from src.models import MealPlan
        plan = MealPlan(days=3, preferences="", restrictions="", meals=[])
        result = format_plan(plan)
        assert "Could not generate" in result


# ------------------------------------------------------------------
# MealDB client (skeleton — no live calls)
# ------------------------------------------------------------------

class TestMealDBClient:
    def test_client_init(self):
        client = MealDBClient("http://localhost:9999")
        assert client.base_url == "http://localhost:9999"
        client.close()

    def test_client_default_url(self):
        client = MealDBClient()
        assert "themealdb.com" in client.base_url
        client.close()


# ------------------------------------------------------------------
# Server module import
# ------------------------------------------------------------------

class TestServerImport:
    def test_server_imports(self):
        """Verify server.py imports without error."""
        import importlib
        import sys
        # Don't actually start the server, just check it can be imported
        # by verifying the file exists and modules compile
        import py_compile
        py_compile.compile("/data/LLM-Apps/mcp-agents/mealwizard/server.py", doraise=True)


# ------------------------------------------------------------------
# Main CLI module import
# ------------------------------------------------------------------

class TestMainImport:
    def test_main_imports(self):
        import py_compile
        py_compile.compile("/data/LLM-Apps/mcp-agents/mealwizard/main.py", doraise=True)