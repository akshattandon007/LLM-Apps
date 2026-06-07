"""Tests for OpenSky parsing + radius filtering, using mocked HTTP."""

import httpx
import pytest

from flights_over_me.config import Settings
from flights_over_me.services.opensky import OpenSkyClient

# A realistic OpenSky state vector (Lufthansa near Cologne, from the docs).
SAMPLE_STATE = [
    "3c6444", "DLH9LF  ", "Germany", 1458564120, 1458564120,
    6.1546, 50.1964, 9639.3, False, 232.88, 98.26, 4.55,
    None, 9547.86, "1000", False, 0,
]


def test_parse_state_maps_fields():
    flight = OpenSkyClient._parse_state(SAMPLE_STATE)
    assert flight.icao24 == "3c6444"
    assert flight.callsign == "DLH9LF"
    assert flight.airline == "Lufthansa"
    assert flight.airline_icao == "DLH"
    assert flight.origin_country == "Germany"
    assert flight.lat == 50.1964
    assert flight.lon == 6.1546
    assert flight.on_ground is False
    assert flight.altitude_ft == round(9547.86 * 3.28084)
    assert flight.speed_kts == round(232.88 * 1.94384)


def test_parse_handles_short_vector():
    # Some sensors omit trailing fields; parser must not crash.
    flight = OpenSkyClient._parse_state(["abc123", "TEST  ", "UK"])
    assert flight.icao24 == "abc123"
    assert flight.callsign == "TEST"
    assert flight.lat is None


@pytest.mark.asyncio
async def test_flights_near_filters_to_circle():
    # Two aircraft: one ~5km away, one far outside a 50km radius.
    near = list(SAMPLE_STATE)
    near[5], near[6] = -0.12, 51.50  # central London
    far = list(SAMPLE_STATE)
    far[0] = "ffffff"
    far[5], far[6] = -2.0, 53.0       # ~250km north-west

    payload = {"time": 1, "states": [near, far]}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenSkyClient(Settings(), http)
        results = await client.flights_near(51.5, -0.12, 50)

    assert len(results) == 1
    assert results[0].icao24 == "3c6444"
    assert results[0].distance_km is not None
    assert results[0].distance_km < 50
    # look-angle enrichment is attached relative to the observer
    assert results[0].bearing_deg is not None
    assert 0 <= results[0].bearing_deg < 360
    assert results[0].elevation_deg is not None
    assert results[0].slant_range_km is not None
