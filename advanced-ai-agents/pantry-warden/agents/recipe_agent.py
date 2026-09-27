"""RecipeAgent — searches and filters recipes by ingredients, dietary needs, and cook time."""

import json
import os
from typing import Dict, List, Optional

from .nutrition_agent import NutritionAgent


class Recipe:
    """A single recipe with metadata."""
    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.ingredients: List[str] = data["ingredients"]
        self.cook_time_min: int = data.get("cook_time_min", 30)
        self.difficulty: str = data.get("difficulty", "easy")
        self.meal_type: str = data.get("meal_type", "dinner")
        self.cost_per_serving: float = data.get("cost_per_serving", 0.0)
        self.nutrition: dict = data.get("nutrition", {})
        self.dietary_tags: List[str] = data.get("dietary_tags", [])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients,
            "cook_time_min": self.cook_time_min,
            "difficulty": self.difficulty,
            "meal_type": self.meal_type,
            "cost_per_serving": self.cost_per_serving,
            "nutrition": self.nutrition,
            "dietary_tags": self.dietary_tags,
        }


class RecipeAgent:
    """Specialized agent that finds and filters recipes.

    Capabilities:
    - Search recipes by available ingredients
    - Filter by dietary restrictions
    - Filter by cook time, meal type, difficulty
    - Score recipes by ingredient overlap
    - Fetch from OpenFoodFacts recipe data or fallback DB
    """

    def __init__(self, recipes_path: str = ""):
        path = recipes_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "default_recipes.json"
        )
        self.recipes: List[Recipe] = []
        self._load(path)

    def _load(self, path: str):
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.recipes = [Recipe(r) for r in data.get("recipes", [])]

    def find_by_ingredients(self, available: List[str],
                            min_coverage: float = 0.3) -> List[Recipe]:
        """Find recipes that use mostly available ingredients."""
        available_set = {a.lower().strip() for a in available}
        scored: List[tuple] = []
        for recipe in self.recipes:
            needed = {i.lower().strip() for i in recipe.ingredients}
            if not needed:
                continue
            overlap = len(available_set & needed)
            coverage = overlap / len(needed)
            missing = needed - available_set
            if coverage >= min_coverage:
                scored.append((coverage, -len(missing), recipe))
        scored.sort(reverse=True, key=lambda x: (x[0], x[1]))
        return [r for _, _, r in scored]

    def filter_by_diet(self, recipes: List[Recipe],
                       nutrition_agent: NutritionAgent,
                       restrictions: Optional[List[str]] = None,
                       max_calories: Optional[int] = None,
                       min_protein: Optional[float] = None) -> List[Recipe]:
        """Filter recipes by dietary restrictions and nutrition goals."""
        if not restrictions and max_calories is None and min_protein is None:
            return recipes
        results = []
        for r in recipes:
            ok = True
            if restrictions:
                tag_set = set(r.dietary_tags)
                for rest in restrictions:
                    rest_lower = rest.lower().strip()
                    # e.g. "vegan" — recipe must have "vegan" tag
                    if rest_lower not in tag_set:
                        ok = False
                        break
            if max_calories and r.nutrition.get("calories", 0) > max_calories:
                ok = False
            if min_protein and r.nutrition.get("protein_g", 0) < min_protein:
                ok = False
            if ok:
                results.append(r)
        return results

    def filter_by_time(self, recipes: List[Recipe],
                       max_cook_time: int) -> List[Recipe]:
        return [r for r in recipes if r.cook_time_min <= max_cook_time]

    def filter_by_meal_type(self, recipes: List[Recipe],
                            meal_type: str) -> List[Recipe]:
        return [r for r in recipes if r.meal_type == meal_type]

    def sort_by_cost(self, recipes: List[Recipe],
                     ascending: bool = True) -> List[Recipe]:
        return sorted(recipes,
                      key=lambda r: r.cost_per_serving,
                      reverse=not ascending)

    def get_missing_ingredients(self, recipe: Recipe,
                                available: List[str]) -> List[str]:
        """Return ingredients the user needs to buy."""
        available_set = {a.lower().strip() for a in available}
        return [i for i in recipe.ingredients
                if i.lower().strip() not in available_set]