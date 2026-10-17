"""Nutrition parsing, verdict generation, and ANSI colour formatting.

Thresholds (per 100 g / 100 ml):
  - High sugar:       > 15 g
  - High fat:         > 20 g
  - High sodium:      > 1.5 g  (1500 mg)
  - Good protein:     > 15 g
  - High fibre:       > 5 g
  - Low calorie:      < 40 kcal
"""

from typing import Optional

# ANSI colour codes
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def parse_nutriments(nutriments: Optional[dict]) -> dict:
    """Extract known nutrition keys from the Open Food Facts nutriments dict.

    Returns a normalised dict with keys:
      energy-kcal, fat, saturated-fat, carbohydrates, sugars, fiber,
      proteins, salt, sodium
    Values are floats; missing keys are None.
    """
    if not nutriments:
        return {}

    keys = [
        "energy-kcal", "energy-kcal_100g",
        "fat", "fat_100g",
        "saturated-fat", "saturated-fat_100g",
        "carbohydrates", "carbohydrates_100g",
        "sugars", "sugars_100g",
        "fiber", "fiber_100g",
        "proteins", "proteins_100g",
        "salt", "salt_100g",
        "sodium", "sodium_100g",
    ]

    result = {}
    for key in keys:
        raw = nutriments.get(key)
        if raw is not None:
            result[key] = float(raw)
    return result


def get_serving_values(nutriments: dict, servings: float = 1.0) -> dict:
    """Return per-serving nutrition values (per 100 g scaled by servings).

    Uses the per-100 g keys (falling back to the unqualified key) and
    multiplies by servings.
    """
    parsed = parse_nutriments(nutriments)

    # Map conceptual keys to the per-100 g field name
    field_map = {
        "energy-kcal": "energy-kcal_100g",
        "fat": "fat_100g",
        "saturated-fat": "saturated-fat_100g",
        "carbohydrates": "carbohydrates_100g",
        "sugars": "sugars_100g",
        "fiber": "fiber_100g",
        "proteins": "proteins_100g",
        "salt": "salt_100g",
        "sodium": "sodium_100g",
    }

    out = {}
    for name, field in field_map.items():
        # Prefer the _100g key, fall back to unqualified
        raw = parsed.get(field) if field in parsed else parsed.get(name)
        if raw is not None:
            out[name] = round(raw * servings, 2)
    return out


def generate_verdicts(nutriments: dict, servings: float = 1.0) -> list[dict]:
    """Generate colour-coded health verdicts from nutriments data.

    Returns a list of dicts: {label, value, level, verdict, color}.
    level is one of 'good', 'warning', 'bad', or None.
    """
    sv = get_serving_values(nutriments, servings)
    verdicts = []

    # --- energy / calories ---
    kcal = sv.get("energy-kcal")
    if kcal is not None:
        if kcal < 40:
            verdicts.append(_make("Calories", f"{kcal} kcal", "good",
                                  "Low calorie"))
        elif kcal < 200:
            verdicts.append(_make("Calories", f"{kcal} kcal", None,
                                  "Moderate"))
        else:
            verdicts.append(_make("Calories", f"{kcal} kcal", "warning",
                                  "High calorie"))

    # --- sugars ---
    sugars = sv.get("sugars")
    if sugars is not None:
        if sugars > 15:
            verdicts.append(_make("Sugars", f"{sugars}g", "bad",
                                  "High sugar"))
        elif sugars > 5:
            verdicts.append(_make("Sugars", f"{sugars}g", "warning",
                                  "Moderate sugar"))
        else:
            verdicts.append(_make("Sugars", f"{sugars}g", "good",
                                  "Low sugar"))

    # --- fat ---
    fat = sv.get("fat")
    if fat is not None:
        if fat > 20:
            verdicts.append(_make("Fat", f"{fat}g", "bad",
                                  "High fat"))
        elif fat > 10:
            verdicts.append(_make("Fat", f"{fat}g", "warning",
                                  "Moderate fat"))
        else:
            verdicts.append(_make("Fat", f"{fat}g", "good",
                                  "Low fat"))

    # --- saturated fat ---
    sat = sv.get("saturated-fat")
    if sat is not None:
        if sat > 5:
            verdicts.append(_make("Saturated Fat", f"{sat}g", "bad",
                                  "High saturated fat"))
        elif sat > 1.5:
            verdicts.append(_make("Saturated Fat", f"{sat}g", "warning",
                                  "Moderate saturated fat"))
        else:
            verdicts.append(_make("Saturated Fat", f"{sat}g", "good",
                                  "Low saturated fat"))

    # --- sodium ---
    sodium = sv.get("sodium")
    if sodium is not None:
        if sodium > 1.5:
            verdicts.append(_make("Sodium", f"{sodium}g", "bad",
                                  "High sodium"))
        elif sodium > 0.4:
            verdicts.append(_make("Sodium", f"{sodium}g", "warning",
                                  "Moderate sodium"))
        else:
            verdicts.append(_make("Sodium", f"{sodium}g", "good",
                                  "Low sodium"))

    # --- protein ---
    protein = sv.get("proteins")
    if protein is not None:
        if protein > 15:
            verdicts.append(_make("Protein", f"{protein}g", "good",
                                  "Good protein"))
        elif protein > 5:
            verdicts.append(_make("Protein", f"{protein}g", None,
                                  "Fair protein"))
        else:
            verdicts.append(_make("Protein", f"{protein}g", "warning",
                                  "Low protein"))

    # --- fiber ---
    fiber = sv.get("fiber")
    if fiber is not None:
        if fiber > 5:
            verdicts.append(_make("Fiber", f"{fiber}g", "good",
                                  "High fiber"))
        elif fiber > 2:
            verdicts.append(_make("Fiber", f"{fiber}g", None,
                                  "Fair fiber"))
        else:
            verdicts.append(_make("Fiber", f"{fiber}g", "warning",
                                  "Low fiber"))

    return verdicts


def _make(label: str, value: str, level: Optional[str],
          verdict: str) -> dict:
    """Build a verdict record with the correct ANSI colour."""
    colour_map = {
        "good": _GREEN,
        "warning": _YELLOW,
        "bad": _RED,
    }
    color = colour_map.get(level, _RESET)
    return {
        "label": label,
        "value": value,
        "level": level,
        "verdict": verdict,
        "color": color,
    }


def format_verdicts(verdicts: list[dict]) -> str:
    """Render verdicts as a coloured table."""
    if not verdicts:
        return "  No nutrition data available."

    lines = []
    for v in verdicts:
        icon = {"good": "✓", "warning": "⚠", "bad": "✗"}.get(v["level"], "·")
        lines.append(
            f"  {v['color']}{icon} {v['label']:20s} {v['value']:>10s}"
            f"  — {v['verdict']}{_RESET}"
        )
    return "\n".join(lines)