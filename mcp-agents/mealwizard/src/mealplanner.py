"""Multi-day meal planning.

Generates a meal plan for N days based on preferences and restrictions.
Currently uses a simple strategy:
  1. Fetch random recipes from TheMealDB.
  2. Filter by preferences (category/cuisine) — skip mismatches.
  3. Assign one meal per day.

Future: richer strategies (leftover reuse, nutritional balance, ingredient bank).
"""

from __future__ import annotations

from src.mealdb import MealDBClient
from src.models import MealPlan, MealPlanDay


# Simple category->diet mapping (same as recipes.py)
_DIET_CATEGORIES = {
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "seafood": "Seafood",
}

# Popular cuisines to filter by
_VALID_CUISINES = [
    "american", "british", "canadian", "chinese", "croatian", "dutch",
    "egyptian", "french", "greek", "indian", "irish", "italian",
    "jamaican", "japanese", "kenyan", "malaysian", "mexican", "moroccan",
    "polish", "portuguese", "russian", "spanish", "thai", "tunisian",
    "turkish", "vietnamese",
]


def generate_plan(
    days: int = 3,
    preferences: str = "",
    restrictions: str = "",
) -> MealPlan:
    """Generate a multi-day meal plan.

    Args:
        days: Number of days (default 3).
        preferences: e.g. "Italian" or "Vegetarian" — narrows random picks.
        restrictions: e.g. "no dairy" — noted but not enforced against TheMealDB.

    Returns:
        MealPlan with one meal per day.
    """
    if days < 1:
        raise ValueError("Days must be at least 1.")
    if days > 14:
        days = 14  # Sanity cap

    client = MealDBClient()
    try:
        pref_lower = preferences.strip().lower()
        rest_lower = restrictions.strip().lower()
        meals: list[MealPlanDay] = []

        # Check if preference is a cuisine or a diet category
        is_cuisine = pref_lower in _VALID_CUISINES
        is_diet = pref_lower in _DIET_CATEGORIES

        attempts = 0
        max_attempts = days * 20  # Safety valve

        while len(meals) < days and attempts < max_attempts:
            attempts += 1
            recipe = client.random()
            if not recipe:
                continue

            # Apply preference filter
            if preferences:
                if is_diet:
                    target = _DIET_CATEGORIES[pref_lower].lower()
                    if not recipe.category or recipe.category.lower() != target:
                        continue
                elif is_cuisine:
                    if not recipe.area or recipe.area.lower() != pref_lower:
                        continue
                else:
                    # Fallback: check if preference string matches name, area, or category
                    match_str = f"{recipe.name} {recipe.area or ''} {recipe.category or ''}".lower()
                    if pref_lower not in match_str:
                        continue

            # Deduplicate by name
            if any(m.recipe_name == recipe.name for m in meals):
                continue

            meals.append(MealPlanDay(
                day=len(meals) + 1,
                meal="Main meal",
                recipe_id=recipe.id,
                recipe_name=recipe.name,
            ))

        return MealPlan(
            days=days,
            preferences=preferences,
            restrictions=restrictions,
            meals=meals,
        )

    finally:
        client.close()


def format_plan(plan: MealPlan) -> str:
    """Pretty-print a meal plan."""
    lines = [
        f"Meal Plan — {plan.days} day(s)",
    ]
    if plan.preferences:
        lines.append(f"Preferences: {plan.preferences}")
    if plan.restrictions:
        lines.append(f"Restrictions: {plan.restrictions}")
    lines.append("")

    if not plan.meals:
        lines.append("Could not generate a plan. Try fewer days or broader preferences.")
        return "\n".join(lines)

    for m in plan.meals:
        lines.append(f"Day {m.day} — {m.meal}")
        lines.append(f"  {m.recipe_name}")
        lines.append(f"  ID: {m.recipe_id}")
        lines.append("")

    lines.append("Use get_recipe(id) to view full details for any recipe.")
    return "\n".join(lines)