"""Pydantic models for MealWizard."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Recipe(BaseModel):
    """A recipe returned by TheMealDB.
    
    Uses extra='allow' to preserve raw TheMealDB fields (strIngredient1..20,
    strMeasure1..20) that don't map to named fields.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(alias="idMeal")
    name: str = Field(alias="strMeal")
    category: Optional[str] = Field(default=None, alias="strCategory")
    area: Optional[str] = Field(default=None, alias="strArea")
    instructions: Optional[str] = Field(default=None, alias="strInstructions")
    tags: Optional[str] = Field(default=None, alias="strTags")
    image: Optional[str] = Field(default=None, alias="strMealThumb")
    youtube: Optional[str] = Field(default=None, alias="strYoutube")
    source: Optional[str] = Field(default=None, alias="strSource")

    @property
    def ingredients(self) -> list[tuple[str, str]]:
        """Extract ingredient-measure pairs from the raw response.
        
        Raw TheMealDB fields like strIngredient1 live in model_extra
        (because extra='allow' keeps them) rather than __dict__.
        """
        raw = self.__dict__
        extra = self.model_extra or {}
        items: list[tuple[str, str]] = []
        for i in range(1, 21):
            ing = raw.get(f"strIngredient{i}") or extra.get(f"strIngredient{i}")
            meas = raw.get(f"strMeasure{i}") or extra.get(f"strMeasure{i}")
            if ing and ing.strip():
                items.append((ing.strip(), meas.strip() if meas else ""))
        return items


class Ingredient(BaseModel):
    """Single ingredient returned by TheMealDB lookup."""
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="idIngredient")
    name: str = Field(alias="strIngredient")
    description: Optional[str] = Field(default=None, alias="strDescription")
    type: Optional[str] = Field(default=None, alias="strType")


class Substitution(BaseModel):
    """An ingredient swap suggestion."""
    ingredient: str
    substitutes: list[str]
    notes: str = ""


class SeasonalProduce(BaseModel):
    """Produce available in a given month and region."""
    month: str
    region: str
    fruits: list[str]
    vegetables: list[str]


class MealPlanDay(BaseModel):
    """A single day in a meal plan."""
    day: int
    meal: str
    recipe_id: str
    recipe_name: str


class MealPlan(BaseModel):
    """Multi-day meal plan."""
    days: int
    preferences: str = ""
    restrictions: str = ""
    meals: list[MealPlanDay]


class ScaledRecipe(BaseModel):
    """A recipe scaled to a given number of servings."""
    original_id: str
    original_servings: int
    target_servings: int
    name: str
    scaled_ingredients: list[tuple[str, str]]
    instructions: str