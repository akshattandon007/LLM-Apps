"""Fixtures and mock data for MealWizard tests."""

from __future__ import annotations

from typing import Any

import pytest

from src.models import Recipe


SAMPLE_RECIPE_RAW: dict[str, Any] = {
    "idMeal": "52772",
    "strMeal": "Chicken Teriyaki",
    "strCategory": "Chicken",
    "strArea": "Japanese",
    "strInstructions": (
        "Mix soy sauce and honey.\r\n"
        "Cook chicken in a pan.\r\n"
        "Add sauce and simmer.\r\n"
        "Serve with rice."
    ),
    "strTags": "Quick,Easy",
    "strMealThumb": "https://example.com/chicken-teriyaki.jpg",
    "strYoutube": "https://youtube.com/watch?v=123",
    "strSource": "https://example.com/recipe",
    "strIngredient1": "Chicken breast",
    "strMeasure1": "2",
    "strIngredient2": "Soy sauce",
    "strMeasure2": "4 tbsp",
    "strIngredient3": "Honey",
    "strMeasure3": "2 tbsp",
    "strIngredient4": "Rice",
    "strMeasure4": "1 cup",
    "strIngredient5": "Bell pepper",
    "strMeasure5": "1",
    "strIngredient6": None,
    "strMeasure6": None,
}


@pytest.fixture
def sample_recipe() -> Recipe:
    return Recipe.model_validate(SAMPLE_RECIPE_RAW)


@pytest.fixture
def sample_recipes_list() -> list[Recipe]:
    """Return a small list of sample recipes for testing."""
    recipes = []
    base = dict(SAMPLE_RECIPE_RAW)
    for i, name in enumerate(["Chicken Teriyaki", "Fried Rice", "Chicken Soup"], 1):
        r = dict(base)
        r["idMeal"] = f"52{i:03d}"
        r["strMeal"] = name
        recipes.append(Recipe.model_validate(r))
    return recipes


@pytest.fixture
def mock_mealdb_response() -> dict[str, Any]:
    """Simulated TheMealDB filter response."""
    return {
        "meals": [
            {"idMeal": "52772", "strMeal": "Chicken Teriyaki", "strMealThumb": ""},
            {"idMeal": "52801", "strMeal": "Chicken Fried Rice", "strMealThumb": ""},
        ]
    }


@pytest.fixture
def mock_empty_response() -> dict[str, Any]:
    return {"meals": None}