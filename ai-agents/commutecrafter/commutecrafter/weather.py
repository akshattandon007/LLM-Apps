"""Weather-aware mode selection (Open-Meteo, keyless).

The rule is simple and physical: if your eyes or hands are busy, or the
weather is hostile, the plan must be audio. Otherwise you may read.
"""

from __future__ import annotations

from typing import Any

import requests

from .sources.base import USER_AGENT

GEOCODE_API = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API = "https://api.open-meteo.com/v1/forecast"

#: Subset of WMO weather interpretation codes that matter to a commuter.
WMO_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "rain showers",
    82: "violent rain showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}

WET_MM = 0.2
COLD_C = 2.0

#: Transport modes where your eyes/hands are already committed.
HANDS_BUSY = {"drive", "car", "cycle", "bike", "run", "running", "motorcycle"}
#: Modes where reading is comfortable.
READ_FRIENDLY = {"train", "subway", "metro", "bus", "ferry", "tram"}


def describe_code(code: int | None) -> str:
    """Human description for a WMO weather code."""
    if code is None:
        return "unknown conditions"
    return WMO_CODES.get(int(code), "mixed conditions")


def is_wet(precipitation_mm: float | None) -> bool:
    return (precipitation_mm or 0.0) >= WET_MM


def is_cold(temp_c: float | None) -> bool:
    return temp_c is not None and temp_c <= COLD_C


def recommend_mode(
    weather: dict[str, Any] | None, transport: str | None = None
) -> tuple[str, str]:
    """Return ``(mode, reason)`` where mode is 'listen', 'read' or 'either'.

    Precedence: hands busy > wet > cold > read-friendly > either.
    """
    transport = (transport or "").strip().lower()
    weather = weather or {}

    if transport in HANDS_BUSY:
        return "listen", f"{transport}: eyes and hands are busy"
    if is_wet(weather.get("precipitation_mm")):
        return "listen", "wet weather — hands stay free under a hood or umbrella"
    if is_cold(weather.get("temp_c")):
        return "listen", "gloves-on cold — tapping a screen is miserable"
    if transport in READ_FRIENDLY:
        return "read", f"{transport}: hands free, seats usually available"
    return "either", "conditions allow reading or listening"


def weather_note(weather: dict[str, Any] | None, mode: str) -> str:
    """One-line plan footnote combining conditions and chosen mode."""
    if not weather:
        return "No weather data — defaulting to audio-friendly pacing."
    temp = weather.get("temp_c")
    desc = weather.get("description") or describe_code(weather.get("code"))
    city = weather.get("city") or "your area"
    temp_txt = f"{temp:.0f}°C" if isinstance(temp, (int, float)) else "?"
    return f"{city}: {desc}, {temp_txt}. Plan is {mode}-first."


def geocode(city: str, timeout: int = 12) -> dict[str, Any] | None:
    """Resolve a city name to coordinates via Open-Meteo geocoding."""
    if not city:
        return None
    resp = requests.get(
        GEOCODE_API,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    results = (resp.json() or {}).get("results") or []
    if not results:
        return None
    top = results[0]
    return {
        "city": top.get("name"),
        "country": top.get("country_code"),
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
    }


def current_weather(lat: float, lon: float, timeout: int = 12) -> dict[str, Any]:
    """Current conditions for a coordinate pair."""
    resp = requests.get(
        FORECAST_API,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    current = (resp.json() or {}).get("current") or {}
    return {
        "temp_c": current.get("temperature_2m"),
        "precipitation_mm": current.get("precipitation", 0.0),
        "wind_kmh": current.get("wind_speed_10m"),
        "code": current.get("weather_code"),
        "description": describe_code(current.get("weather_code")),
    }


def weather_for_city(city: str, timeout: int = 12) -> dict[str, Any] | None:
    """Combined geocode + current conditions. Returns ``None`` on any failure."""
    try:
        place = geocode(city, timeout=timeout)
        if not place:
            return None
        conditions = current_weather(place["latitude"], place["longitude"], timeout=timeout)
    except Exception:  # noqa: BLE001 - weather is a nice-to-have, never fatal
        return None
    return {**place, **conditions}
