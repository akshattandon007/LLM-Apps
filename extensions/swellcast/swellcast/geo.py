"""Geocoding via Open-Meteo free API (no key required)."""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from .models import Location

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json"


def geocode(query: str) -> Location | None:
    """Resolve a place name to lat/lon via Open-Meteo Geocoding."""
    url = GEOCODING_URL.format(q=urllib.request.quote(query))
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None

    results = data.get("results", [])
    if not results:
        return None

    best = results[0]
    return Location(
        name=best.get("name", query),
        country=best.get("country", ""),
        lat=best.get("latitude", 0.0),
        lon=best.get("longitude", 0.0),
        admin1=best.get("admin1", ""),
        timezone=best.get("timezone", "UTC"),
    )