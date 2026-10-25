"""Tests for the Weather Agent."""

import httpx

from saferide.agents.weather_agent import (
    _classify_condition,
    _assess_hazard,
    geocode,
    get_forecast,
    set_client,
)


def test_classify_condition():
    assert _classify_condition(0, 10, 20, 20) == "clear"
    assert _classify_condition(10, 10, 20, 20) == "rain"
    assert _classify_condition(30, 10, 20, 20) == "storm"
    assert _classify_condition(0, 10, 0.5, 20) == "fog"
    assert _classify_condition(0, 10, 20, -10) == "snow"
    assert _classify_condition(0, 40, 20, 20) == "windy"
    assert _classify_condition(0, 80, 20, 20) == "storm"


def test_assess_hazard():
    hazard, note = _assess_hazard(0, 10, 20, 20, "clear")
    assert not hazard
    assert note == ""

    hazard, note = _assess_hazard(30, 10, 20, 20, "storm")
    assert hazard
    assert "Heavy precipitation" in note
    assert "Storm conditions" in note

    hazard, note = _assess_hazard(0, 10, 80, 10, "clear")
    assert hazard
    assert "Dangerous wind gusts" in note


def test_get_forecast_api_error_fallback():
    """When Open-Meteo is unreachable, return simulated forecast."""
    def handler(request):
        return httpx.Response(500)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        fc = get_forecast(40.7128, -74.0060, "New York")

    assert fc.source == "simulated"
    assert fc.condition == "clear"
    assert fc.temp_c == 22.0  # simulated default


def test_get_forecast_success():
    """When Open-Meteo returns valid data, parse it."""
    def handler(request):
        return httpx.Response(200, json={
            "current": {
                "temperature_2m": 15.3,
                "apparent_temperature": 13.1,
                "precipitation": 0.2,
                "wind_speed_10m": 12.5,
                "wind_gusts_10m": 20.0,
                "visibility": 18000.0,
            }
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        fc = get_forecast(40.7128, -74.0060, "New York")

    assert fc.source == "live"
    assert fc.temp_c == 15.3
    assert fc.feels_like_c == 13.1
    assert fc.visibility_km == 18.0
    assert not fc.hazard


def test_geocode_fallback():
    """When geocoding fails, return None (caller handles)."""
    def handler(request):
        return httpx.Response(500)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        result = geocode("Failsville")

    assert result is None