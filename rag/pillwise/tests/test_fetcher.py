"""Tests for PillWise fetcher module."""

import json
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pillwise.fetcher import _extract_field, prepare_chunks, USEFUL_FIELDS


def test_extract_field_simple_value():
    """_extract_field returns a string for a simple nested value."""
    result = {"openfda": {"brand_name": ["Advil"]}}
    val = _extract_field(result, "openfda.brand_name")
    assert val == "Advil"


def test_extract_field_none():
    """_extract_field returns None for missing field."""
    result = {"openfda": {"brand_name": ["Advil"]}}
    val = _extract_field(result, "openfda.generic_name")
    assert val is None


def test_extract_field_multiple_values():
    """_extract_field joins list values."""
    result = {"indications_and_usage": ["For pain relief.", "For fever reduction."]}
    val = _extract_field(result, "indications_and_usage")
    assert "pain relief" in val
    assert "fever" in val


def test_prepare_chunks_creates_chunks():
    """prepare_chunks creates chunks from drug label records."""
    records = [
        {
            "openfda.brand_name": "TestDrug",
            "indications_and_usage": "Used for testing purposes only.",
            "adverse_reactions": "May cause test failure. Rare but serious.",
        }
    ]
    chunks = prepare_chunks(records)
    assert len(chunks) >= 2  # At least 2 fields with text
    sources = [c["source"] for c in chunks]
    assert any("TestDrug" in s for s in sources)


def test_prepare_chunks_short_text_skipped():
    """prepare_chunks skips fields with very short text."""
    records = [
        {
            "openfda.brand_name": "TestDrug",
            "indications_and_usage": "X",  # Too short
        }
    ]
    chunks = prepare_chunks(records)
    assert len(chunks) == 0  # "X" is < 10 chars


def test_prepare_chunks_metadata():
    """prepare_chunks sets correct metadata fields."""
    records = [
        {
            "openfda.brand_name": "TestBrand",
            "warnings": "This is a test warning that should be long enough to pass the length check.",
        }
    ]
    chunks = prepare_chunks(records)
    assert len(chunks) == 1
    c = chunks[0]
    assert c["drug_name"] == "TestBrand"
    assert c["field"] == "warnings"
    assert "Warning" in c["field_label"]


def test_useful_fields_exists():
    """USEFUL_FIELDS contains expected drug label fields."""
    assert "indications_and_usage" in USEFUL_FIELDS
    assert "adverse_reactions" in USEFUL_FIELDS
    assert "drug_interactions" in USEFUL_FIELDS
    assert "dosage_and_administration" in USEFUL_FIELDS
    assert "contraindications" in USEFUL_FIELDS
    assert "warnings" in USEFUL_FIELDS
