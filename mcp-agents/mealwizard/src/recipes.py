"""Recipe search and filtering.

Provides the core 'find_recipes' flow: given a list of ingredients the user
has, optionally filtered by diet (category) and cuisine (area), hit TheMealDB
and return matching recipes.

Strategy:
  1. For each ingredient, call filter.php?i=<ingredient> to get meal summaries.
  2. Union all results and count how many user ingredients each recipe uses.
  3. Optionally filter by cuisine (area) and/or category (diet).
  4. Sort by ingredient-match count descending.
  5. Fetch full details for top results.
"""

from __future__ import annotations

from collections import Counter

from src.mealdb import MealDBClient
from src.models import Recipe

# TheMealDB categories commonly used as diet proxies
_DIET_CATEGORIES = {
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "seafood": "Seafood",
    "chicken": "Chicken",
    "pork": "Pork",
    "beef": "Beef",
    "lamb": "Lamb",
    "pasta": "Pasta",
    "dessert": "Dessert",
}


def find_recipes(
    ingredients: list[str],
    diet: str = "",
    cuisine: str = "",
    max_results: int = 10,
) -> list[Recipe]:
    """Find recipes using the given ingredients.

    Args:
        ingredients: Ingredients the user has (e.g. ["chicken", "rice", "bell pepper"]).
        diet: Optional diet filter — maps to TheMealDB category (e.g. "Vegetarian").
        cuisine: Optional cuisine filter — maps to TheMealDB area (e.g. "Italian").
        max_results: Max detailed recipes to return.

    Returns:
        List of full Recipe objects, sorted by ingredient match count desc.
    """
    if not ingredients:
        return []

    client = MealDBClient()
    try:
        # 1. Collect meal IDs from each ingredient filter
        meal_scores: Counter[str] = Counter()
        for ing in ingredients:
            try:
                meals = client.filter_by_ingredient(ing)
                for m in meals:
                    mid = m.get("idMeal", "")
                    if mid:
                        meal_scores[mid] += 1
            except Exception:
                continue  # Skip problematic ingredients gracefully

        if not meal_scores:
            return []

        # 2. Get top candidates by score
        ranked = meal_scores.most_common(max_results * 2)
        candidate_ids = [mid for mid, _ in ranked]

        # 3. Fetch full details
        recipes = client.lookup_batch(candidate_ids)

        # 4. Apply cuisine filter (area)
        if cuisine:
            cuisine_lower = cuisine.strip().lower()
            recipes = [
                r for r in recipes
                if r.area and r.area.lower() == cuisine_lower
            ]

        # 5. Apply diet filter (category)
        if diet:
            diet_lower = diet.strip().lower()
            # Map common diet terms to TheMealDB categories
            target_cat = _DIET_CATEGORIES.get(diet_lower, diet_lower.capitalize())
            recipes = [
                r for r in recipes
                if r.category and r.category.lower() == target_cat.lower()
            ]

        # 6. Sort by ingredient match count
        recipes.sort(key=lambda r: meal_scores.get(r.id, 0), reverse=True)

        return recipes[:max_results]

    finally:
        client.close()


def format_recipes(recipes: list[Recipe], ingredients: list[str]) -> str:
    """Pretty-print a list of recipes with match info."""
    if not recipes:
        return "No recipes found for those ingredients. Try broadening your search."

    lines = [
        f"Found {len(recipes)} recipe(s) using your ingredients:",
        "",
    ]
    for i, r in enumerate(recipes, 1):
        matched = sum(
            1 for ing in ingredients
            if ing.lower() in [x[0].lower() for x in r.ingredients]
        )
        lines.append(
            f"  {i}. {r.name}"
        )
        lines.append(f"     Cuisine: {r.area or 'Unknown'} | Category: {r.category or 'Unknown'}")
        lines.append(f"     Ingredients matched: {matched}/{len(ingredients)}")
        lines.append(f"     ID: {r.id}")
        if r.image:
            lines.append(f"     Image: {r.image}")
        lines.append("")

    lines.append("Tip: Use get_recipe(id) for full details and instructions.")
    return "\n".join(lines)


def format_recipe_detail(recipe: Recipe) -> str:
    """Pretty-print a single recipe with full details."""
    lines = [
        f"=== {recipe.name} ===",
        f"Cuisine: {recipe.area or 'Unknown'}",
        f"Category: {recipe.category or 'Unknown'}",
        "",
        "Ingredients:",
    ]
    for name, measure in recipe.ingredients:
        lines.append(f"  - {measure} {name}".strip())

    lines.append("")
    lines.append("Instructions:")
    if recipe.instructions:
        steps = [s.strip() for s in recipe.instructions.split("\r\n") if s.strip()]
        for i, step in enumerate(steps, 1):
            lines.append(f"  {i}. {step}")
    else:
        lines.append("  (No instructions available.)")

    if recipe.image:
        lines.append(f"\nImage: {recipe.image}")
    if recipe.youtube:
        lines.append(f"YouTube: {recipe.youtube}")
    if recipe.source:
        lines.append(f"Source: {recipe.source}")

    return "\n".join(lines)