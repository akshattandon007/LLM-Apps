"""Tests for SunGuard MCP server.

Uses pytest-httpx to mock all external API calls, plus tests the
simulated fallback path by temporarily disabling the mock.
"""

from __future__ import annotations

import json
from typing import Generator
from unittest.mock import patch

import httpx
import pytest
import pytest_httpx

from sunguard.models import RiskLevel, SkinType
from sunguard.server import (
    air_quality_check,
    heat_safety,
    hourly_uv,
    outdoor_plan,
    skin_burn_time,
    sun_safety,
)
from sunguard.weather import (
    _simulate_air_quality,
    _simulate_geocode,
    _simulate_uv_forecast,
    aqi_risk_level,
    calculate_burn_time,
    calculate_heat_index,
    geocode,
    get_air_quality,
    get_uv_forecast,
    heat_index_risk,
    set_client,
    uv_risk_level,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client() -> Generator[httpx.Client, None, None]:
    """Create a mock httpx client that returns canned responses."""
    client = httpx.Client(
        transport=httpx.MockTransport(lambda req: _mock_handler(req))
    )
    set_client(client)
    yield client
    # Reset to default client
    set_client(httpx.Client(timeout=15.0))


def _mock_handler(request: httpx.Request) -> httpx.Response:
    """Route mocked requests to appropriate canned responses."""
    url = str(request.url)

    if "geocoding-api.open-meteo.com" in url:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Portland",
                        "latitude": 45.5152,
                        "longitude": -122.6784,
                        "country": "US",
                        "admin1": "Oregon",
                    }
                ]
            },
        )

    if "api.open-meteo.com/v1/forecast" in url:
        return httpx.Response(
            200,
            json={
                "hourly": {
                    "time": [f"2025-07-15T{h:02d}:00" for h in range(24)],
                    "uv_index": [round(0.5 + (6.5 * max(0, 1 - abs(h - 13) / 6)), 1) for h in range(24)],
                },
                "daily": {
                    "uv_index_max": [6.5],
                    "temperature_2m_max": [30.0],
                },
            },
        )

    if "air-quality-api.open-meteo.com" in url:
        return httpx.Response(
            200,
            json={
                "hourly": {
                    "time": [f"2025-07-15T{h:02d}:00" for h in range(24)],
                    "european_aqi": [50 + 10 * (h % 5) for h in range(24)],
                }
            },
        )

    if "api.weather.gov" in url:
        return httpx.Response(
            200,
            json={
                "features": [
                    {
                        "properties": {
                            "headline": "Heat Advisory issued July 15 until 8pm PDT",
                            "severity": "Moderate",
                            "description": "Heat advisory in effect...",
                        }
                    }
                ]
            },
        )

    return httpx.Response(404, json={"error": "not found"})


# ---------------------------------------------------------------------------
# Unit tests — weather.py
# ---------------------------------------------------------------------------

class TestGeocode:
    def test_geocode_city(self, mock_client):
        result = geocode("Portland")
        assert result.name == "Portland"
        assert result.latitude == 45.5152
        assert result.longitude == -122.6784
        assert result.country == "US"

    def test_geocode_fallback(self):
        # Without mock, it should fall back to simulated Portland
        set_client(httpx.Client(timeout=5))
        result = geocode("Nowhereville")
        assert abs(result.latitude - 45.5152) < 0.01
        assert abs(result.longitude - -122.6784) < 0.01

    def test_simulate_geocode(self):
        result = _simulate_geocode("Austin")
        assert result.name == "Austin"
        assert result.latitude == 45.5152
        assert result.admin1 == "Oregon"


class TestUVForecast:
    def test_get_uv_forecast(self, mock_client):
        result = get_uv_forecast(45.5152, -122.6784)
        assert result.max_uv == 6.5
        assert result.max_temp == 30.0
        assert len(result.hourly_uv) == 24
        assert result.hourly_uv[13]["uv_index"] == 7.0  # peak at 13:00

    def test_uv_forecast_fallback(self):
        result = get_uv_forecast(99.0, 99.0)
        assert result.max_uv > 0
        assert len(result.hourly_uv) == 24

    def test_simulate_uv_forecast(self):
        result = _simulate_uv_forecast()
        assert result.max_uv == 6.5
        assert result.max_temp == 30.0
        assert len(result.hourly_uv) == 24


class TestAirQuality:
    def test_get_air_quality(self, mock_client):
        result = get_air_quality(45.5152, -122.6784)
        assert result.aqi > 0
        assert len(result.hourly_values) == 24

    def test_air_quality_fallback(self):
        result = get_air_quality(99.0, 99.0)
        assert result.aqi == 50  # simulated value

    def test_simulate_air_quality(self):
        result = _simulate_air_quality()
        assert result.aqi == 50


class TestBurnTime:
    def test_type_1_uv_1(self):
        minutes, desc = calculate_burn_time("I", 1.0)
        assert minutes > 0
        assert "burns" in desc.lower()

    def test_type_6_uv_11(self):
        minutes, desc = calculate_burn_time("VI", 11.0)
        assert minutes >= 45  # even at high UV, type VI is resilient
        assert "never" in desc.lower()

    def test_invalid_type_defaults_to_3(self):
        minutes, desc = calculate_burn_time("X", 3.0)
        assert minutes > 0

    def test_zero_uv(self):
        minutes, desc = calculate_burn_time("I", 0)
        assert minutes > 0


class TestHeatIndex:
    def test_below_threshold(self):
        hi = calculate_heat_index(20.0)
        assert hi == 20.0  # below 27°C, returns temp

    def test_above_threshold(self):
        hi = calculate_heat_index(30.0)
        assert hi > 30.0  # heat index should be higher than temp

    def test_high_temperature(self):
        hi = calculate_heat_index(40.0)
        assert hi > 40.0

    def test_risk_level(self):
        assert heat_index_risk(20.0) == "low"
        assert heat_index_risk(25.0) == "moderate"
        assert heat_index_risk(28.0) == "high"
        assert heat_index_risk(35.0) == "very_high"
        assert heat_index_risk(42.0) == "extreme"


class TestRiskLevels:
    def test_uv_risk(self):
        assert uv_risk_level(0) == "low"
        assert uv_risk_level(3) == "moderate"
        assert uv_risk_level(6) == "high"
        assert uv_risk_level(8) == "very_high"
        assert uv_risk_level(11) == "extreme"

    def test_aqi_risk(self):
        assert aqi_risk_level(0) == "low"
        assert aqi_risk_level(50) == "low"
        assert aqi_risk_level(60) == "moderate"
        assert aqi_risk_level(101) == "high"


# ---------------------------------------------------------------------------
# Integration tests — server.py tools
# ---------------------------------------------------------------------------

class TestSunSafety:
    def test_basic(self, mock_client):
        result = sun_safety("Portland")
        assert result.location == "Portland"
        assert result.uv_index == 6.5
        assert result.overall_risk in (RiskLevel.HIGH, RiskLevel.MODERATE)
        assert len(result.recommendation) > 0
        assert result.source == "live"

    def test_fallback(self):
        # Force failure by injecting a client that always errors
        fail_client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
        set_client(fail_client)
        result = sun_safety("Failsville")
        assert result.location
        assert result.uv_index > 0
        assert result.source == "simulated"


class TestHourlyUV:
    def test_basic(self, mock_client):
        result = hourly_uv(45.5152, -122.6784, "2025-07-15")
        assert len(result.hours) == 24
        assert result.peak_uv == 7.0
        assert result.peak_hour == "13:00"
        assert result.source == "live"

    def test_fallback(self):
        result = hourly_uv(99.0, 99.0, "2025-07-15")
        assert len(result.hours) == 24
        assert result.source == "simulated"


class TestSkinBurnTime:
    def test_type_1(self):
        result = skin_burn_time("I", 6.5)
        assert result.skin_type == SkinType.I
        assert result.uv_index == 6.5
        assert result.burn_time_minutes > 0
        assert len(result.recommendation) > 0

    def test_type_6(self):
        result = skin_burn_time("VI", 1.0)
        assert result.burn_time_minutes >= 90


class TestHeatSafety:
    def test_basic(self, mock_client):
        result = heat_safety("Portland")
        assert result.location == "Portland"
        assert result.temperature == 30.0
        assert result.heat_index > 30.0
        assert len(result.advisories) > 0
        assert result.source == "live"

    def test_fallback(self):
        fail_client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
        set_client(fail_client)
        result = heat_safety("Failsville")
        assert result.location
        assert result.temperature > 0
        assert result.source == "simulated"


class TestAirQualityCheck:
    def test_basic(self, mock_client):
        result = air_quality_check("Portland")
        assert result.location == "Portland"
        assert result.aqi > 0
        assert result.aqi_level
        assert result.source == "live"

    def test_fallback(self):
        fail_client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
        set_client(fail_client)
        result = air_quality_check("Failsville")
        assert result.location
        assert result.aqi == 50
        assert result.source == "simulated"


class TestOutdoorPlan:
    def test_safe(self, mock_client):
        result = outdoor_plan("Portland", "walking", "07:00")
        assert result.location == "Portland"
        assert result.activity == "walking"
        assert len(result.concerns) == 0 or not result.is_safe

    def test_unsafe_midday(self, mock_client):
        result = outdoor_plan("Portland", "beach", "14:00")
        assert result.activity == "beach"
        assert result.time == "14:00"
        assert result.uv_index > 0

    def test_fallback(self):
        fail_client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
        set_client(fail_client)
        result = outdoor_plan("Failsville", "hiking", "12:00")
        assert result.location
        assert result.source == "simulated"