"""Address geocoding via the US Census Geocoder API.

Zero-auth, free, and returns lat/lon coordinates for US street addresses.
"""

from __future__ import annotations

import httpx

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# Cache simple lookups in-process (session scope)
_geocode_cache: dict[str, tuple[float, float, str]] = {}


def geocode(address: str) -> tuple[float, float, str]:
    """Resolve a US street address to (latitude, longitude, formatted_address).

    Returns lat, lon, and the Census-normalised address string.
    Raises ValueError if the address cannot be resolved.
    """
    cached = _geocode_cache.get(address)
    if cached:
        return cached

    params = {
        "address": address,
        "benchmark": "2020",
        "format": "json",
    }
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(CENSUS_GEOCODER_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    matches = (data.get("result") or {}).get("addressMatches") or []
    if not matches:
        raise ValueError(
            f"Could not geocode address '{address}'. "
            "Try a more specific address (street number + street name + city + state)."
        )

    best = matches[0]
    coords = best["coordinates"]
    lat = coords["y"]
    lon = coords["x"]
    formatted = best.get("matchedAddress", address)

    result = (lat, lon, formatted)
    _geocode_cache[address] = result
    return result


def get_county_for_point(lat: float, lon: float) -> str | None:
    """Reverse-geocode lat/lon to a county name using Census."""
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon,
        "y": lat,
        "benchmark": "2020",
        "vintage": "2020",
        "format": "json",
    }
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    geos = (data.get("result") or {}).get("geographies") or {}
    counties = geos.get("Counties") or geos.get("counties") or []
    if counties:
        return counties[0].get("NAME")
    return None