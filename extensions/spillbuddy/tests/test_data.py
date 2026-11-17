"""Tests for SpillBuddy data module."""

import pytest
from spillbuddy.data import lookup, list_stains, list_fabrics, STAIN_DB


class TestLookup:
    def test_red_wine_cotton(self):
        result = lookup("red wine", "cotton")
        assert result is not None
        assert result["stain"] == "red wine"
        assert result["fabric"] == "cotton"
        assert "blot" in result["method"].lower()
        assert result["caution"]  # non-empty

    def test_coffee_carpet(self):
        result = lookup("coffee", "carpet")
        assert result is not None
        assert result["stain"] == "coffee"

    def test_blood_silk(self):
        result = lookup("blood", "silk")
        assert result is not None
        assert "cold water" in result["method"].lower()

    def test_grease_oil_cotton(self):
        result = lookup("grease_oil", "cotton")
        assert result is not None
        assert "cornstarch" in result["method"] or "baking soda" in result["method"]

    def test_unknown_stain(self):
        result = lookup("unicorn_juice", "cotton")
        assert result is None

    def test_unknown_fabric_falls_to_all(self):
        result = lookup("coffee", "linen")
        assert result is not None
        assert result["fabric"] == "linen"

    def test_case_insensitive(self):
        r1 = lookup("Red Wine", "Cotton")
        r2 = lookup("red wine", "cotton")
        assert r1 == r2

    def test_all_stains_have_all_fallback(self):
        for stain in STAIN_DB:
            assert "all" in STAIN_DB[stain], f"{stain} missing 'all' fallback"

    def test_all_entries_have_method_and_caution(self):
        for stain, fabrics in STAIN_DB.items():
            for fabric, (method, caution) in fabrics.items():
                assert method, f"{stain}/{fabric} has empty method"
                assert caution, f"{stain}/{fabric} has empty caution"

    def test_ink_synthetic(self):
        result = lookup("ink", "synthetic")
        assert result is not None
        assert "rubbing alcohol" in result["method"].lower() or "hairspray" in result["method"].lower()

    def test_mud_cotton(self):
        result = lookup("mud", "cotton")
        assert result is not None
        assert "dry" in result["method"].lower()

    def test_pet_stains_carpet(self):
        result = lookup("pet_stains", "carpet")
        assert result is not None
        assert "enzyme" in result["method"].lower() or "vinegar" in result["method"].lower()


class TestListFunctions:
    def test_list_stains(self):
        stains = list_stains()
        assert len(stains) >= 10
        assert "red wine" in stains
        assert "coffee" in stains
        assert "blood" in stains
        assert stains == sorted(stains)

    def test_list_fabrics(self):
        fabrics = list_fabrics()
        assert "cotton" in fabrics
        assert "silk" in fabrics
        assert "carpet" in fabrics


class TestDataIntegrity:
    def test_no_empty_methods(self):
        for stain, fabrics in STAIN_DB.items():
            for fabric, (method, caution) in fabrics.items():
                assert len(method) > 10, f"{stain}/{fabric} method too short"
                assert len(caution) > 5, f"{stain}/{fabric} caution too short"