"""MCP server tests — tool registration + tool behavior against injected
fixture clients (no network). Tools return markdown or friendly error
strings, never raise."""

import asyncio

import httpx
import pytest

import breatheasy.server as server
from breatheasy.api import OpenMeteoClient
from tests import load_fixture, make_http_client


def run_tool(coro):
    return asyncio.run(coro)


@pytest.fixture()
def fixture_client():
    return OpenMeteoClient(make_http_client())


@pytest.fixture()
def use_client(monkeypatch):
    def _wire(client):
        monkeypatch.setattr(server, "get_client", lambda: client)
        return client

    return _wire


def test_server_registers_exactly_four_tools():
    tools = asyncio.run(server.mcp.list_tools())
    names = sorted(tool.name for tool in tools)
    assert names == [
        "get_air_forecast",
        "get_air_quality",
        "get_pollen_forecast",
        "get_wildfire_smoke_alert",
    ]


def test_get_air_quality_tool(fixture_client, use_client):
    use_client(fixture_client)
    out = run_tool(server.get_air_quality("Brooklyn"))
    assert "## 🌬️ Air quality in Brooklyn, New York, United States" in out
    assert "**US AQI:** **61** — Moderate 🙂" in out
    assert "**European AQI:** 60" in out
    assert "**Top pollutant:** PM2.5 (19.9 µg/m³)" in out
    assert "Unusually sensitive people" in out


def test_get_air_quality_falls_back_to_european(use_client):
    payload = load_fixture("air_quality_sample.json")
    payload["current"]["us_aqi"] = None
    client = OpenMeteoClient(make_http_client(air_quality=payload))
    use_client(client)
    out = run_tool(server.get_air_quality("Brooklyn"))
    assert "European AQI (US AQI not reported)" in out
    assert "**60**" in out


def test_get_air_quality_no_data_at_all(use_client):
    payload = load_fixture("air_quality_sample.json")
    payload["current"] = {"time": "2026-10-10T08:00"}
    client = OpenMeteoClient(make_http_client(air_quality=payload))
    use_client(client)
    out = run_tool(server.get_air_quality("Brooklyn"))
    assert "No current air quality data" in out


def test_get_air_quality_unknown_place_returns_error_string(use_client):
    client = OpenMeteoClient(make_http_client(geocode={"results": []}))
    use_client(client)
    out = run_tool(server.get_air_quality("Atlantis"))
    assert "Could not find 'Atlantis'" in out
    assert "lat,lon" in out


def test_get_air_quality_api_failure_returns_error_string(use_client):
    client = OpenMeteoClient(
        httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(500, json={})
            )
        )
    )
    use_client(client)
    out = run_tool(server.get_air_quality("Brooklyn"))
    # The 500 fires during geocoding here; any API failure must still
    # come back as a friendly string, never an exception.
    assert "could not fetch" in out.lower()


def test_get_air_forecast_tool(fixture_client, use_client):
    use_client(fixture_client)
    out = run_tool(server.get_air_forecast("Brooklyn", days=3))
    assert "(3-day forecast)" in out
    assert "| 2026-10-10 | 66 | Moderate" in out
    assert "| 2026-10-11 | 69 | Moderate" in out
    assert "**Worst hour today (2026-10-10):** 23:00 — AQI 66" in out
    assert "**Advice:**" in out


def test_get_air_forecast_days_clamped_to_7(fixture_client, use_client):
    use_client(fixture_client)
    out = run_tool(server.get_air_forecast("Brooklyn", days=99))
    assert "(7-day forecast)" in out


def test_get_air_forecast_no_data(use_client):
    payload = load_fixture("air_quality_sample.json")
    payload["hourly"] = {"time": [], "us_aqi": []}
    client = OpenMeteoClient(make_http_client(air_quality=payload))
    use_client(client)
    out = run_tool(server.get_air_forecast("Brooklyn", days=3))
    assert "No air quality forecast data" in out


def test_get_pollen_forecast_tool(use_client):
    pollen = load_fixture("pollen_sample.json")
    client = OpenMeteoClient(make_http_client(air_quality=pollen))
    use_client(client)
    out = run_tool(server.get_pollen_forecast("Chicago", days=1))
    assert "(1-day peak)" in out
    assert "| Grass | 80 | high 🟠 |" in out
    assert "| Mugwort | 120 | high 🟠 |" in out
    assert "| Birch | 30 | low 🟢 |" in out
    assert "| Olive | 0 | none 🟢 |" in out
    assert "| Ragweed | — | no data 🚫 |" in out


def test_get_pollen_forecast_no_data_region(fixture_client, use_client):
    use_client(fixture_client)  # plain sample: no pollen variables
    out = run_tool(server.get_pollen_forecast("Brooklyn", days=1))
    assert "No pollen data is available for this region/season" in out


def test_pollen_days_clamped(fixture_client, use_client):
    use_client(fixture_client)
    out = run_tool(server.get_pollen_forecast("Brooklyn", days=42))
    assert "(7-day peak)" in out


def test_get_wildfire_smoke_alert_clear(fixture_client, use_client):
    use_client(fixture_client)  # us_aqi 61, pm2_5 19.9 → clear
    out = run_tool(server.get_wildfire_smoke_alert("Brooklyn"))
    assert "Air looks clear" in out
    assert "no elevated smoke signals" in out


def test_get_wildfire_smoke_alert_elevated_via_aqi(use_client):
    payload = load_fixture("air_quality_sample.json")
    payload["current"]["us_aqi"] = 172
    payload["current"]["pm2_5"] = 90.0
    client = OpenMeteoClient(make_http_client(air_quality=payload))
    use_client(client)
    out = run_tool(server.get_wildfire_smoke_alert("Brooklyn"))
    assert "may include wildfire smoke" in out
    assert "US AQI **172**" in out


def test_get_wildfire_smoke_alert_elevated_via_pm25(use_client):
    payload = load_fixture("air_quality_sample.json")
    payload["current"]["us_aqi"] = 100  # below 151...
    payload["current"]["pm2_5"] = 60.0  # ...but PM2.5 >= 55.4 triggers
    client = OpenMeteoClient(make_http_client(air_quality=payload))
    use_client(client)
    out = run_tool(server.get_wildfire_smoke_alert("Brooklyn"))
    assert "may include wildfire smoke" in out


def test_tools_return_str():
    tools = asyncio.run(server.mcp.list_tools())
    for tool in tools:
        assert "str" in str(tool.outputSchema)