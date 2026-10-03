"""Scale recipe ingredient quantities to a target number of servings.

Takes a fully-loaded Recipe and a target serving count. Computes
a scaling factor and re-calculates each ingredient measure.

Handles common measure formats: decimals (1.5 cups), fractions (1/2 cup),
and whole numbers. Preserves the unit string and attempts to make the
output readable.
"""

from __future__ import annotations

import math
import re

from src.models import Recipe, ScaledRecipe

# Regex to find a numeric value (including fractions) at the start of a measure.
_NUM_PATTERN = re.compile(r"^(\d+(?:\.\d+)?(?:\s*/\s*\d+)?)\s*(.*)")


def _parse_quantity(raw: str) -> float:
    """Parse a measure string like '1.5', '1/2', or '2' into a float."""
    m = _NUM_PATTERN.match(raw.strip())
    if not m:
        return 0.0
    num_str, _ = m.groups()
    if "/" in num_str:
        parts = num_str.split("/")
        try:
            return float(parts[0]) / float(parts[1])
        except (ValueError, ZeroDivisionError):
            return 0.0
    try:
        return float(num_str)
    except ValueError:
        return 0.0


def _format_quantity(qty: float) -> str:
    """Format a quantity nicely: 2 -> '2', 1.5 -> '1.5', 0.33 -> '1/3'."""
    if qty == 0:
        return ""
    # Round to 2 decimal places first
    rounded = round(qty, 2)
    if rounded == int(rounded):
        return str(int(rounded))
    # Check common fractions
    fractions = {
        0.25: "1/4",
        0.33: "1/3",
        0.5: "1/2",
        0.67: "2/3",
        0.75: "3/4",
        0.2: "1/5",
    }
    for val, frac in fractions.items():
        if abs(rounded - val) < 0.02:
            return frac
    return f"{rounded:.2f}"


def _get_measure(ingredient: tuple[str, str]) -> str:
    """Return the measure part."""
    return ingredient[1] if len(ingredient) > 1 else ""


def scale_recipe(recipe: Recipe, target_servings: int, original_servings: int = 4) -> ScaledRecipe:
    """Scale a recipe to target servings.

    Args:
        recipe: Fully populated Recipe object (with ingredients).
        target_servings: Number of servings desired.
        original_servings: Default 4 — adjust if the recipe specifies another.

    Returns:
        ScaledRecipe with recalculated ingredient measures.
    """
    if target_servings <= 0:
        raise ValueError("Target servings must be positive.")
    if original_servings <= 0:
        raise ValueError("Original servings must be positive.")

    factor = target_servings / original_servings
    scaled: list[tuple[str, str]] = []

    for ing_name, measure in recipe.ingredients:
        qty = _parse_quantity(measure)
        if qty > 0:
            new_qty = qty * factor
            # Extract the unit part (everything after the number)
            unit_match = _NUM_PATTERN.match(measure.strip())
            unit = unit_match.group(2).strip() if unit_match else ""
            formatted = _format_quantity(new_qty)
            new_measure = f"{formatted} {unit}".strip() if unit else formatted
            scaled.append((ing_name, new_measure))
        else:
            # Can't parse — pass through as-is
            scaled.append((ing_name, measure))

    return ScaledRecipe(
        original_id=recipe.id,
        original_servings=original_servings,
        target_servings=target_servings,
        name=recipe.name,
        scaled_ingredients=scaled,
        instructions=recipe.instructions or "",
    )


def format_scaled(sr: ScaledRecipe) -> str:
    """Pretty-print a scaled recipe."""
    lines = [
        f"{sr.name} (scaled from {sr.original_servings} to {sr.target_servings} servings)",
        "",
        "Ingredients:",
    ]
    for name, measure in sr.scaled_ingredients:
        lines.append(f"  - {measure} {name}".strip())
    lines.append("")
    lines.append("Instructions:")
    if sr.instructions:
        steps = [s.strip() for s in sr.instructions.split("\r\n") if s.strip()]
        for i, step in enumerate(steps, 1):
            lines.append(f"  {i}. {step}")
    else:
        lines.append("  (No instructions available.)")
    return "\n".join(lines)