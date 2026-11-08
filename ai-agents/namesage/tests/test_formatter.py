"""Tests for the NameSage formatter module."""

from typing import Any
from unittest.mock import patch

from namesage.formatter import print_profile


def test_print_profile_full_data(capsys):
    """print_profile prints all sections with complete data."""
    data: dict[str, Any] = {
        "age": {"name": "john", "age": 40, "count": 1000},
        "gender": {"name": "john", "gender": "male", "probability": 0.98},
        "nationality": {
            "name": "john",
            "country": [
                {"country_id": "US", "probability": 0.5},
                {"country_id": "GB", "probability": 0.3},
            ],
        },
        "rhymes": [{"word": "don", "score": 100}, {"word": "ron", "score": 80}],
        "llm_profile": "**Era vibes:** A timeless classic.",
    }
    print_profile("john", data)
    captured = capsys.readouterr()
    assert "NameSage" in captured.out
    assert "john" in captured.out
    assert "40" in captured.out
    assert "Male" in captured.out or "male" in captured.out
    assert "US" in captured.out
    assert "don" in captured.out
    assert "Era vibes" in captured.out


def test_print_profile_no_llm(capsys):
    """print_profile works without LLM profile."""
    data: dict[str, Any] = {
        "age": {},
        "gender": {},
        "nationality": {},
        "rhymes": [],
        "llm_profile": "",
    }
    print_profile("alex", data)
    captured = capsys.readouterr()
    assert "NameSage" in captured.out
    assert "No age data" in captured.out
    assert "No gender data" in captured.out
    assert "No nationality data" in captured.out


def test_print_profile_error_data(capsys):
    """print_profile handles error return values from APIs."""
    data: dict[str, Any] = {
        "age": {"error": "Connection refused"},
        "gender": {"error": "Timeout"},
        "nationality": {"error": "500 error"},
        "rhymes": [{"error": "timeout"}],
        "llm_profile": "",
    }
    print_profile("error", data)
    captured = capsys.readouterr()
    assert "Connection refused" in captured.out
    assert "Timeout" in captured.out
    assert "500 error" in captured.out


def test_print_profile_partial_countries(capsys):
    """print_profile handles nationality with empty country list."""
    data: dict[str, Any] = {
        "age": {"age": None, "count": 0},
        "gender": {"gender": None, "probability": 0},
        "nationality": {"country": []},
        "rhymes": [],
        "llm_profile": "",
    }
    print_profile("test", data)
    captured = capsys.readouterr()
    assert "No age data" in captured.out
    assert "No gender data" in captured.out
    assert "No nationality data" in captured.out