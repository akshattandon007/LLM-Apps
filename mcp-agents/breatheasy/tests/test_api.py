"""Tests for the OpenMeteoClient and payload helpers — fixture-driven,
no network."""

import httpx
import pytest

from breatheasy.api import (
    OpenMeteoClient,
    daily_max_aqi,
    pollen_peak_per_type,
    today_from_payload,
    worst_hour_today,
)
from tests import load_fixture, make_http_client


def test_geocode_parses_geo_sample():
    client = OpenMeteoClient(make_http_client())
    results = client.geocode("Brooklyn")
    assert len(results) == 1
    result = results[0]
    assert result.name == "Brooklyn"
    assert result.latitude == 40.6501
    assert result.longitude == -73.94958
    assert result.country == "United States"
    assert result.admin1 == "New York"


def test_geocode_empty_results():
    client = OpenMeteoClient(make_http_client(geocode={"results": []}))
    assert client.geocode("Nowhereville") == []


def test_geocode_sends_expected_params():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"results": []})

    client = OpenMeteoClient(
        httpx.Client(transport=httpx.MockTransport(handler))
    )
    client.geocode("Brooklyn, NY")
    assert captured["params"]["name"] == "Brooklyn, NY"
    assert captured["params"]["count"] == "5"
    assert captured["params"]["language"] == "en"
    assert captured["params"]["format"] == "json"


def test_air_quality_parses_aq_sample():
    client = OpenMeteoClient(make_http_client())
    data = client.air_quality(40.6501, -73.94958, days=2)
    current = data["current"]
    assert current["us_aqi"] == 61
    assert current["european_aqi"] == 60
    assert current["pm2_5"] == 19.9
    assert current["pm10"] == 20.2
    assert current["ozone"] == 0.0
    hourly = data["hourly"]
    assert len(hourly["time"]) == 48
    assert len(hourly["us_aqi"]) == 48
    assert len(hourly["pm2_5"]) == 48


def test_air_quality_sends_forecast_days_and_variables():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["day"] = request.url.params["forecast_days"]
        seen["hourly"] = request.url.params["hourly"]
        return httpx.Response(200, json=load_fixture("air_quality_sample.json"))

    client = OpenMeteoClient(
        httpx.Client(transport=httpx.MockTransport(handler))
    )
    client.air_quality(40.0, -74.0, days=4)
    assert seen["day"] == "4"
    assert "us_aqi" in seen["hourly"]
    assert "grass_pollen" in seen["hourly"]
    assert "ragweed_pollen" in seen["hourly"]


def test_http_error_raises_for_api():
    client = OpenMeteoClient(
        httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(500, json={"error": "boom"})
            )
        )
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.air_quality(1.0, 2.0, days=1)


# -- Derived-data helpers --------------------------------------------------

@pytest.fixture()
def aq_hourly():
    return load_fixture("air_quality_sample.json")["hourly"]


def test_daily_max_aqi_from_sample(aq_hourly):
    daily = daily_max_aqi(aq_hourly)
    assert daily == [("2026-10-10", 66), ("2026-10-11", 69)]


def test_daily_max_aqi_falls_back_to_european():
    hourly = {
        "time": ["2026-10-10T00:00", "2026-10-10T01:00"],
        "us_aqi": [None, None],
        "european_aqi": [40, 55],
    }
    assert daily_max_aqi(hourly) == [("2026-10-10", 55)]


def test_daily_max_aqi_skips_null_hours():
    hourly = {
        "time": ["2026-10-10T00:00", "2026-10-10T01:00"],
        "us_aqi": [None, 45],
    }
    assert daily_max_aqi(hourly) == [("2026-10-10", 45)]


def test_worst_hour_today_from_sample(aq_hourly):
    assert worst_hour_today(aq_hourly, "2026-10-10") == ("23:00", 66)


def test_worst_hour_today_returns_none_for_unknown_date(aq_hourly):
    assert worst_hour_today(aq_hourly, "1999-01-01") is None


def test_today_from_payload_uses_current_time():
    data = load_fixture("air_quality_sample.json")
    assert today_from_payload(data) == "2026-10-10"


def test_missing_pollen_keys_yield_empty_peaks(aq_hourly):
    # The plain air-quality sample carries no pollen variables at all —
    # helpers must not crash and must report "no data" via {}.
    assert pollen_peak_per_type(aq_hourly) == {}


def test_pollen_peaks_skip_null_values():
    hourly = load_fixture("pollen_sample.json")["hourly"]
    peaks = pollen_peak_per_type(hourly)
    assert peaks == {
        "alder_pollen": 5.0,
        "birch_pollen": 30.0,
        "grass_pollen": 80.0,
        "mugwort_pollen": 120.0,
        "olive_pollen": 0.0,
        # ragweed_pollen is all-NULL → excluded
    }
    assert "ragweed_pollen" not in peaks