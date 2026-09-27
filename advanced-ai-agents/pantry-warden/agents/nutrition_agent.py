"""NutritionAgent — dietary analysis, restriction checking, and nutrition profiling."""

from typing import Dict, List, Optional


class DietaryProfile:
    """A person's dietary needs and restrictions."""
    def __init__(self, restrictions: Optional[List[str]] = None,
                 max_calories: Optional[int] = None,
                 min_protein_g: Optional[float] = None,
                 max_carbs_g: Optional[float] = None,
                 max_fat_g: Optional[float] = None,
                 allergies: Optional[List[str]] = None):
        self.restrictions = restrictions or []
        self.max_calories = max_calories      # per meal
        self.min_protein_g = min_protein_g
        self.max_carbs_g = max_carbs_g
        self.max_fat_g = max_fat_g
        self.allergies = allergies or []


class NutritionAgent:
    """Specialized agent for nutrition profiling and restriction checking.

    Capabilities:
    - Calculate meal nutrition totals
    - Check against dietary restrictions
    - Identify allergen conflicts
    - Suggest swaps to meet nutrition goals
    """

    def __init__(self, profile: Optional[DietaryProfile] = None):
        self.profile = profile or DietaryProfile()

    def set_profile(self, profile: DietaryProfile):
        self.profile = profile

    def check_compatibility(self, nutrition: Dict[str, float]) -> Dict[str, str]:
        """Check if a meal's nutrition fits within the dietary profile.
        Returns a dict of field -> warning message (empty if all clear)."""
        warnings = {}
        if self.profile.max_calories and nutrition.get("calories", 0) > self.profile.max_calories:
            warnings["calories"] = (
                f"Exceeds limit of {self.profile.max_calories} kcal "
                f"(meal has {nutrition.get('calories', 0)} kcal)"
            )
        if self.profile.min_protein_g and nutrition.get("protein_g", 0) < self.profile.min_protein_g:
            warnings["protein"] = (
                f"Below target of {self.profile.min_protein_g}g "
                f"(meal has {nutrition.get('protein_g', 0)}g)"
            )
        if self.profile.max_carbs_g and nutrition.get("carbs_g", 0) > self.profile.max_carbs_g:
            warnings["carbs"] = (
                f"Exceeds limit of {self.profile.max_carbs_g}g "
                f"(meal has {nutrition.get('carbs_g', 0)}g)"
            )
        if self.profile.max_fat_g and nutrition.get("fat_g", 0) > self.profile.max_fat_g:
            warnings["fat"] = (
                f"Exceeds limit of {self.profile.max_fat_g}g "
                f"(meal has {nutrition.get('fat_g', 0)}g)"
            )
        return warnings

    def estimate_weekly_nutrition(self, meals: List[Dict]) -> Dict[str, float]:
        """Sum nutrition across a week of planned meals."""
        totals: Dict[str, float] = {"calories": 0, "protein_g": 0,
                                     "carbs_g": 0, "fat_g": 0}
        for meal in meals:
            for key in totals:
                totals[key] += meal.get(key, 0)
        # Average daily
        days = max(len(meals), 1)
        return {k: round(v / days, 1) for k, v in totals.items()}

    def score_meal_nutrition(self, nutrition: Dict[str, float]) -> float:
        """0.0–1.0 score: how well this meal fits the dietary profile.
        1.0 = perfect match, 0.0 = completely unsuitable."""
        warnings = self.check_compatibility(nutrition)
        if not warnings:
            return 1.0
        # More warnings = lower score
        deduction = len(warnings) * 0.25
        return max(0.0, 1.0 - deduction)