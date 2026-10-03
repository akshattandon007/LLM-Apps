"""Ingredient substitution database.

Provides common swaps for 20+ everyday ingredients. Used when the user
is out of something and needs a viable alternative.

Source: established culinary knowledge (Joy of Cooking, Cook's Illustrated,
Serious Eats). No external API needed — this is a curated static table.

Format: ingredient -> list of (substitute, notes) pairs.
"""

from __future__ import annotations

from src.models import Substitution

# Static substitution table.
# Each entry is (ingredient, list_of_substitutes, usage_notes).
_SUBSTITUTIONS: dict[str, tuple[list[str], str]] = {
    "butter": (
        ["oil (vegetable/canola)", "margarine", "shortening", "coconut oil"],
        "Swap 1:1 for most baking and sautéing. Unsalted preferred.",
    ),
    "milk": (
        ["almond milk", "soy milk", "oat milk", "coconut milk (canned)"],
        "Swap 1:1. For baking, thin yoghurt with water also works.",
    ),
    "eggs": (
        ["flax egg (1 tbsp flax meal + 3 tbsp water)", "chia egg",
         "1/4 cup applesauce", "1/4 cup mashed banana"],
        "Flax/chia works for baking. Applesauce for moisture; banana adds flavour.",
    ),
    "flour": (
        ["almond flour", "coconut flour", "oat flour (blended oats)",
         "gluten-free all-purpose blend"],
        "Almond flour 1:1. Coconut flour needs 1/4 the amount + extra liquid.",
    ),
    "sugar": (
        ["honey", "maple syrup", "agave nectar", "coconut sugar"],
        "Honey/maple: use 3/4 cup per 1 cup sugar, reduce liquid by 1/4.",
    ),
    "sour cream": (
        ["plain yogurt (Greek or regular)", "crème fraîche", "buttermilk"],
        "Yogurt swaps 1:1. Buttermilk works in baking (add 1 tbsp butter per cup).",
    ),
    "heavy cream": (
        ["coconut cream (chilled can top)", "full-fat milk + 1 tbsp butter",
         "evaporated milk"],
        "Coconut cream whips. Milk+butter works for sauces, not whipping.",
    ),
    "buttermilk": (
        ["milk + 1 tbsp lemon juice or vinegar (let sit 5 min)",
         "yogurt thinned with water", "kefir"],
        "Acidified milk works 1:1 in all baking recipes.",
    ),
    "cream cheese": (
        ["Greek yogurt (strained)", "tofu (silken, blended)",
         "cottage cheese (blended smooth)"],
        "Yogurt is tangier. Tofu needs salt + lemon. Cottage cheese: blend well.",
    ),
    "breadcrumbs": (
        ["panko", "crushed crackers", "rolled oats (blitzed)",
         "almond meal"],
        "Panko is the closest. Oats for coating; almond meal for binding.",
    ),
    "tomato sauce": (
        ["crushed tomatoes + herbs", "tomato paste + water (1:2 ratio)",
         "roasted red peppers (blended)"],
        "Crushed tomatoes are closest. Pepper purée is sweeter.",
    ),
    "soy sauce": (
        ["tamari (GF)", "coconut aminos", "liquid aminos",
         "1/2 tsp salt + 1 tsp Worcestershire per tbsp"],
        "Tamari swaps 1:1. Coconut aminos are sweeter, use 1:1.",
    ),
    "olive oil": (
        ["avocado oil", "grapeseed oil", "vegetable oil"],
        "Avocado oil is closest for high heat. Grapeseed for neutral flavour.",
    ),
    "lemon juice": (
        ["lime juice", "white wine vinegar", "apple cider vinegar",
         "1/4 tsp citric acid + 2 tbsp water"],
        "Lime is 1:1. Vinegars: use half the amount and adjust.",
    ),
    "garlic": (
        ["1/8 tsp garlic powder per clove", "1/2 tsp jarred minced garlic",
         "1/4 tsp asafoetida (for FODMAP)"],
        "Fresh: 1 clove = 1/2 tsp minced = 1/8 tsp powder.",
    ),
    "onion": (
        ["1 tbsp onion powder per medium onion", "shallots (1:1)",
         "leeks (white parts, 1:1 by volume chopped)"],
        "Onion powder: rehydrate with a little water. Shallots are milder.",
    ),
    "baking powder": (
        ["1/4 tsp baking soda + 1/2 tsp cream of tartar per tsp",
         "1/4 tsp baking soda + 1/2 cup buttermilk (reduce liquid)"],
        "Homemade swap works 1:1 for the baking powder amount.",
    ),
    "baking soda": (
        ["baking powder (triple the amount)",
         "potassium bicarbonate (if restricting sodium)"],
        "Baking powder has acid built in. Triple amount, remove acid from recipe.",
    ),
    "honey": (
        ["maple syrup", "agave nectar", "golden syrup", "brown rice syrup"],
        "Swap 1:1. Maple is thinner — reduce other liquid slightly.",
    ),
    "yogurt": (
        ["sour cream", "buttermilk", "kefir", "cottage cheese (blended)"],
        "Sour cream 1:1. Kefir is thinner — reduce other liquids.",
    ),
    "parmesan": (
        ["nutritional yeast", "pecorino romano", "asiago",
         "grana padano"],
        "Nutritional yeast for dairy-free. Pecorino is saltier.",
    ),
    "chocolate": (
        ["carob powder (1:1 for cocoa)", "cacao nibs (for texture)",
         "1 tbsp cocoa + 1 tbsp butter per 25g chocolate"],
        "Cocoa+butter swap works for baking where texture isn't critical.",
    ),
    "coconut milk": (
        ["almond milk + 1 tbsp coconut oil", "oat milk + 1 tbsp coconut oil",
         "evaporated milk (not dairy-free)"],
        "Add coconut oil for richness to mimic canned coconut milk.",
    ),
    "wine (cooking)": (
        ["broth (chicken/veg) + 1 tbsp vinegar",
         "grape juice + 1 tsp lemon juice (for sweetness)",
         "verjuice"],
        "Broth+vinegar for savoury dishes. Grape juice for sweet.",
    ),
}


def get_substitutes(ingredient: str) -> Substitution:
    """Look up substitutes for a given ingredient (case-insensitive)."""
    key = ingredient.strip().lower()
    for known, (subs, notes) in _SUBSTITUTIONS.items():
        if key == known:
            return Substitution(ingredient=ingredient, substitutes=subs, notes=notes)
    # Fallback: try partial match
    for known, (subs, notes) in _SUBSTITUTIONS.items():
        if key in known or known in key:
            return Substitution(ingredient=ingredient, substitutes=subs, notes=notes)
    return Substitution(
        ingredient=ingredient,
        substitutes=[],
        notes=f"No known substitution for '{ingredient}' in our database.",
    )


def list_all_ingredients() -> list[str]:
    """Return all ingredients we have substitutions for (sorted)."""
    return sorted(_SUBSTITUTIONS.keys())


def format_substitutes(sub: Substitution) -> str:
    """Pretty-print a substitution result."""
    lines = [f"Ingredient: {sub.ingredient}"]
    if sub.substitutes:
        lines.append("Substitutes:")
        for s in sub.substitutes:
            lines.append(f"  - {s}")
    lines.append(f"Notes: {sub.notes}")
    return "\n".join(lines)