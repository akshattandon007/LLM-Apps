"""Open-Meteo API client — geocoding + air quality + pollen.

Uses a synchronous httpx.Client (injected, so tests can swap in
httpx.MockTransport and never touch the network).  Open-Meteo requires no
API key; rate limits are permissive and the service is free.

Documented endpoints (verified live 2026-10-10):
  GET https://air-quality-api.open-meteo.com/v1/air-quality
      ?latitude=..&longitude=..&current=<vars>&hourly=<vars>
      &forecast_days=N&timezone=auto
  GET https://geocoding-api.open-meteo.com/v1/search
      ?name=..&count=5&language=en&format=json
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .advice import POLLEN_TYPES

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

CURRENT_VARIABLES = "us_aqi,european_aqi,pm2_5,pm10,ozone"
AIR_HOURLY_VARIABLES = "us_aqi,european_aqi,pm2_5,pm10"
POLLEN_VARIABLES = ",".join(key for key, _ in POLLEN_TYPES)
HOURLY_VARIABLES = f"{AIR_HOURLY_VARIABLES},{POLLEN_VARIABLES}"

DEFAULT_TIMEOUT_SECONDS = 15.0


@dataclass(frozen=True)
class GeoResult:
    name: str
    latitude: float
    longitude: float
    country: str = ""
    admin1: str = ""


class OpenMeteoClient:
    """Thin, typed wrapper over the two Open-Meteo endpoints."""

    def __init__(self, http_client: httpx.Client | None = None):
        if http_client is None:
            http_client = httpx.Client(
                timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True
            )
        self._http = http_client

    # -- endpoints --------------------------------------------------------

    def geocode(self, query: str) -> list[GeoResult]:
        """Search for a place name; results ordered by the API's relevance."""
        params = {"name": query, "count": 5, "language": "en", "format": "json"}
        data = self._get_json(GEOCODING_URL, params)
        results: list[GeoResult] = []
        for item in data.get("results") or []:
            results.append(
                GeoResult(
                    name=item.get("name") or "",
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    country=item.get("country") or "",
                    admin1=item.get("admin1") or "",
                )
            )
        return results

    def air_quality(
        self, latitude: float, longitude: float, days: int = 1
    ) -> dict:
        """Fetch current + hourly air quality and pollen for coordinates.

        Pollen variables may be NULL outside Europe / outside pollen
        season — callers handle that gracefully (see pollen_peak_per_type).
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": CURRENT_VARIABLES,
            "hourly": HOURLY_VARIABLES,
            "forecast_days": max(1, int(days)),
            "timezone": "auto",
        }
        return self._get_json(AIR_QUALITY_URL, params)

    def _get_json(self, url: str, params: dict) -> dict:
        resp = self._http.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


# -- Derived data helpers (pure functions over API payloads) --------------

def aqi_series(hourly: dict) -> list:
    """Hourly AQI series — US AQI, falling back to European AQI."""
    us = hourly.get("us_aqi") or []
    if any(v is not None for v in us):
        return us
    return hourly.get("european_aqi") or []


def daily_max_aqi(hourly: dict) -> list[tuple[str, int]]:
    """[(date, max_aqi), ...] sorted by date, from hourly arrays."""
    times = hourly.get("time") or []
    series = aqi_series(hourly)
    by_day: dict[str, list[int]] = {}
    for t, value in zip(times, series):
        if value is None:
            continue
        day = str(t)[:10]
        by_day.setdefault(day, []).append(int(value))
    return [(day, max(vals)) for day, vals in sorted(by_day.items())]


def worst_hour_today(
    hourly: dict, today: str
) -> tuple[str, int] | None:
    """(HH:MM, aqi) of the worst hour on `today`, or None."""
    times = hourly.get("time") or []
    series = aqi_series(hourly)
    best: tuple[str, int] | None = None
    for t, value in zip(times, series):
        if value is None or str(t)[:10] != today:
            continue
        candidate = (str(t)[11:16], int(value))
        if best is None or candidate[1] > best[1]:
            best = candidate
    return best


def today_from_payload(data: dict) -> str:
    """The payload's 'today' — the current time's date (or first hour)."""
    current_time = (data.get("current") or {}).get("time") or ""
    if current_time:
        return str(current_time)[:10]
    times = (data.get("hourly") or {}).get("time") or []
    return str(times[0])[:10] if times else ""


def pollen_peak_per_type(hourly: dict) -> dict[str, float]:
    """{api_key: peak over the window}; only types with any non-null value.

    Returns {} when no pollen variable is present or every value is NULL —
    the caller renders the "no data for this region/season" message.
    """
    peaks: dict[str, float] = {}
    for key, _ in POLLEN_TYPES:
        values = [v for v in (hourly.get(key) or []) if v is not None]
        if values:
            peaks[key] = max(float(v) for v in values)
    return peaks