"""
Open-Meteo Geo API — geocode a city name to lat/lon for location-based search.
Free, no auth, no rate limit.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_USER_AGENT = "triallight/1.0"


def geocode_city(city_name: str) -> Optional[dict]:
    """Geocode a city name to {'lat', 'lon', 'name', 'country', 'admin1'}."""
    resp = requests.get(
        GEOCODING_URL,
        params={"name": city_name, "count": 3, "language": "en", "format": "json"},
        headers={"User-Agent": _USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    # Return the most relevant (highest population) match
    best = max(results, key=lambda r: r.get("population", 0) or 0)
    return {
        "lat": best["latitude"],
        "lon": best["longitude"],
        "name": best.get("name", ""),
        "country": best.get("country", ""),
        "region": best.get("admin1", ""),
    }


def format_location_query(city: str) -> str:
    """Format a location query for ClinicalTrials.gov API."""
    return f"{quote(city)} United States"