"""Weather logic — pure decision tables, no HTTP."""

from __future__ import annotations

import pytest

from commutecrafter.weather import (
    describe_code,
    is_cold,
    is_wet,
    recommend_mode,
    weather_note,
)


@pytest.mark.parametrize(
    "transport,expected",
    [
        ("drive", "listen"),
        ("car", "listen"),
        ("cycle", "listen"),
        ("run", "listen"),
        ("train", "read"),
        ("bus", "read"),
        ("metro", "read"),
        ("walk", "either"),
        (None, "either"),
    ],
)
def test_mode_by_transport(transport, expected):
    mode, reason = recommend_mode({"temp_c": 15.0, "precipitation_mm": 0.0}, transport)
    assert mode == expected
    assert reason


def test_rain_forces_listen_even_on_a_train():
    mode, reason = recommend_mode({"temp_c": 15.0, "precipitation_mm": 1.4}, "train")
    assert mode == "listen"
    assert "wet" in reason


def test_cold_forces_listen():
    mode, reason = recommend_mode({"temp_c": -3.0, "precipitation_mm": 0.0}, "walk")
    assert mode == "listen"
    assert "cold" in reason


def test_busy_hands_beats_weather():
    mode, _ = recommend_mode({"temp_c": 22.0, "precipitation_mm": 0.0}, "cycle")
    assert mode == "listen"


def test_none_weather_is_safe():
    mode, reason = recommend_mode(None, "walk")
    assert mode == "either"
    assert reason


def test_is_wet_threshold():
    assert is_wet(0.2) is True
    assert is_wet(0.19) is False
    assert is_wet(None) is False


def test_is_cold():
    assert is_cold(2.0) is True
    assert is_cold(2.1) is False
    assert is_cold(None) is False


def test_describe_code_known_and_unknown():
    assert describe_code(0) == "clear sky"
    assert describe_code(63) == "rain"
    assert describe_code(12345) == "mixed conditions"
    assert describe_code(None) == "unknown conditions"


def test_weather_note_includes_city_and_temp():
    note = weather_note({"city": "Mumbai", "temp_c": 29.4, "code": 2}, "read")
    assert "Mumbai" in note
    assert "29" in note
    assert "read" in note


def test_weather_note_without_data():
    assert "No weather data" in weather_note(None, "listen")
