"""Unit tests for nutrition verdict rules — NO network calls."""

import sys
import os

# Ensure the project root is on sys.path so pocketdiet is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json

from pocketdiet.nutrition import (
    parse_nutriments,
    get_serving_values,
    generate_verdicts,
    format_verdicts,
)

# =========================================================================
# Helpers
# =========================================================================


def _make_nutriments(**kwargs) -> dict:
    """Build a nutriments dict that looks like what the OFF API returns.

    Open Food Facts returns both unqualified and _100g keys.  We set
    both so parsing works regardless of which key the code prefers.
    """
    data = {}
    for key, val in kwargs.items():
        data[key] = val
        # Also set the _100g variant for per-100 g keys
        if not key.endswith("_100g") and not key.endswith("_serving"):
            data[f"{key}_100g"] = val
    return data


# =========================================================================
# Tests: parse_nutriments
# =========================================================================


class TestParseNutriments:
    def test_empty_nutriments(self):
        assert parse_nutriments(None) == {}
        assert parse_nutriments({}) == {}

    def test_parses_known_keys(self):
        raw = {
            "energy-kcal_100g": 95,
            "fat_100g": 3.5,
            "proteins_100g": 10,
        }
        result = parse_nutriments(raw)
        assert result["energy-kcal_100g"] == 95
        assert result["fat_100g"] == 3.5
        assert result["proteins_100g"] == 10

    def test_ignores_unknown_keys(self):
        raw = {"foo": "bar", "energy-kcal_100g": 50}
        result = parse_nutriments(raw)
        assert "foo" not in result
        assert result["energy-kcal_100g"] == 50


# =========================================================================
# Tests: get_serving_values
# =========================================================================


class TestGetServingValues:
    def test_single_serving(self):
        nm = _make_nutriments(proteins=12, fat=8, sugars=4)
        sv = get_serving_values(nm, 1.0)
        assert sv["proteins"] == 12
        assert sv["fat"] == 8
        assert sv["sugars"] == 4

    def test_two_servings_doubles_values(self):
        nm = _make_nutriments(proteins=10, fat=5, sugars=2)
        sv = get_serving_values(nm, 2.0)
        assert sv["proteins"] == 20
        assert sv["fat"] == 10
        assert sv["sugars"] == 4

    def test_half_serving(self):
        nm = _make_nutriments(proteins=10, fat=5)
        sv = get_serving_values(nm, 0.5)
        assert sv["proteins"] == 5
        assert sv["fat"] == 2.5

    def test_missing_nutriments(self):
        assert get_serving_values(None, 1.0) == {}
        assert get_serving_values({}, 1.0) == {}


# =========================================================================
# Tests: generate_verdicts — threshold rules
# =========================================================================


class TestGenerateVerdicts:
    """Verify every threshold rule from the spec."""

    # -- Sugars --
    def test_sugar_high(self):
        v = generate_verdicts(_make_nutriments(sugars=16))
        vv = {v["label"]: v for v in v}
        assert vv["Sugars"]["level"] == "bad"
        assert vv["Sugars"]["verdict"] == "High sugar"

    def test_sugar_moderate(self):
        v = generate_verdicts(_make_nutriments(sugars=10))
        vv = {v["label"]: v for v in v}
        assert vv["Sugars"]["level"] == "warning"

    def test_sugar_low(self):
        v = generate_verdicts(_make_nutriments(sugars=4))
        vv = {v["label"]: v for v in v}
        assert vv["Sugars"]["level"] == "good"

    # -- Fat --
    def test_fat_high(self):
        v = generate_verdicts(_make_nutriments(fat=25))
        vv = {v["label"]: v for v in v}
        assert vv["Fat"]["level"] == "bad"
        assert vv["Fat"]["verdict"] == "High fat"

    def test_fat_moderate(self):
        v = generate_verdicts(_make_nutriments(fat=15))
        vv = {v["label"]: v for v in v}
        assert vv["Fat"]["level"] == "warning"

    def test_fat_low(self):
        v = generate_verdicts(_make_nutriments(fat=8))
        vv = {v["label"]: v for v in v}
        assert vv["Fat"]["level"] == "good"

    # -- Sodium --
    def test_sodium_high(self):
        v = generate_verdicts(_make_nutriments(sodium=2.0))
        vv = {v["label"]: v for v in v}
        assert vv["Sodium"]["level"] == "bad"
        assert vv["Sodium"]["verdict"] == "High sodium"

    def test_sodium_moderate(self):
        v = generate_verdicts(_make_nutriments(sodium=0.8))
        vv = {v["label"]: v for v in v}
        assert vv["Sodium"]["level"] == "warning"

    def test_sodium_low(self):
        v = generate_verdicts(_make_nutriments(sodium=0.2))
        vv = {v["label"]: v for v in v}
        assert vv["Sodium"]["level"] == "good"

    # -- Protein --
    def test_protein_good(self):
        v = generate_verdicts(_make_nutriments(proteins=16))
        vv = {v["label"]: v for v in v}
        assert vv["Protein"]["level"] == "good"
        assert vv["Protein"]["verdict"] == "Good protein"

    def test_protein_fair(self):
        v = generate_verdicts(_make_nutriments(proteins=10))
        vv = {v["label"]: v for v in v}
        assert vv["Protein"]["level"] is None

    def test_protein_low(self):
        v = generate_verdicts(_make_nutriments(proteins=3))
        vv = {v["label"]: v for v in v}
        assert vv["Protein"]["level"] == "warning"

    # -- Fiber --
    def test_fiber_high(self):
        v = generate_verdicts(_make_nutriments(fiber=6))
        vv = {v["label"]: v for v in v}
        assert vv["Fiber"]["level"] == "good"
        assert vv["Fiber"]["verdict"] == "High fiber"

    def test_fiber_fair(self):
        v = generate_verdicts(_make_nutriments(fiber=3))
        vv = {v["label"]: v for v in v}
        assert vv["Fiber"]["level"] is None

    def test_fiber_low(self):
        v = generate_verdicts(_make_nutriments(fiber=1))
        vv = {v["label"]: v for v in v}
        assert vv["Fiber"]["level"] == "warning"

    # -- Calories --
    def test_calories_low(self):
        v = generate_verdicts(_make_nutriments(**{"energy-kcal": 30}))
        vv = {v["label"]: v for v in v}
        assert vv["Calories"]["level"] == "good"
        assert vv["Calories"]["verdict"] == "Low calorie"

    def test_calories_moderate(self):
        v = generate_verdicts(_make_nutriments(**{"energy-kcal": 100}))
        vv = {v["label"]: v for v in v}
        assert vv["Calories"]["level"] is None

    def test_calories_high(self):
        v = generate_verdicts(_make_nutriments(**{"energy-kcal": 300}))
        vv = {v["label"]: v for v in v}
        assert vv["Calories"]["level"] == "warning"

    # -- Saturated fat --
    def test_satfat_high(self):
        v = generate_verdicts(_make_nutriments(**{"saturated-fat": 8}))
        vv = {v["label"]: v for v in v}
        assert vv["Saturated Fat"]["level"] == "bad"

    def test_satfat_moderate(self):
        v = generate_verdicts(_make_nutriments(**{"saturated-fat": 3}))
        vv = {v["label"]: v for v in v}
        assert vv["Saturated Fat"]["level"] == "warning"

    def test_satfat_low(self):
        v = generate_verdicts(_make_nutriments(**{"saturated-fat": 1}))
        vv = {v["label"]: v for v in v}
        assert vv["Saturated Fat"]["level"] == "good"

    # -- Serving multiplier on thresholds --
    def test_serving_doubles_affects_verdict(self):
        """2 servings of 12 g sugars = 24 g -> bad (was moderate at 1x)."""
        nm = _make_nutriments(sugars=12)
        v = generate_verdicts(nm, servings=2.0)
        vv = {v["label"]: v for v in v}
        assert vv["Sugars"]["level"] == "bad"

    def test_verdict_boundary_exact(self):
        """Exact 15 g sugars is moderate (not bad), exact 15 g protein is
        fair (not good)."""
        v = generate_verdicts(_make_nutriments(sugars=15))
        vv = {v["label"]: v for v in v}
        assert vv["Sugars"]["level"] == "warning"

        v2 = generate_verdicts(_make_nutriments(proteins=15))
        vv2 = {v2["label"]: v2 for v2 in v2}
        assert vv2["Protein"]["level"] is None

    def test_empty_nutriments_no_verdicts(self):
        assert generate_verdicts(None, 1.0) == []
        assert generate_verdicts({}, 1.0) == []


# =========================================================================
# Tests: format_verdicts
# =========================================================================


class TestFormatVerdicts:
    def test_empty(self):
        assert "No nutrition data" in format_verdicts([])

    def test_contains_labels(self):
        v = generate_verdicts(_make_nutriments(sugars=4, fat=8, proteins=16))
        output = format_verdicts(v)
        assert "Calories" not in output  # only sugars, fat, protein set
        assert "Sugars" in output
        assert "Fat" in output
        assert "Protein" in output