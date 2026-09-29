"""Open-Meteo weather client — free, zero-auth weather API.

API docs: https://open-meteo.com/en/docs
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import requests

# Open-Meteo free tier — no API key required, 10 000 req/day non-commercial limit
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass
class DayWeather:
    """Weather summary for a single day of the trip."""
    date: date
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    weather_code: int      # WMO weather code
    uv_index_max: float
    wind_speed_max_kmh: float
    daylight_hours: float

    @property
    def weather_label(self) -> str:
        """Return a human-readable label for the WMO weather code."""
        return WMO_CODES.get(self.weather_code, f"Code {self.weather_code}")


# Simplified WMO weather interpretation codes
WMO_CODES: dict[int, str] = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class GeocodeError(Exception):
    """Raised when a city name cannot be geocoded."""


class ForecastError(Exception):
    """Raised when the weather forecast API returns an error."""


class WeatherClient:
    """Client for the free Open-Meteo API (no auth required)."""

    def geocode(self, city: str) -> tuple[float, float, str]:
        """Resolve a city name to (lat, lon, resolved_name).

        Raises GeocodeError if the city cannot be found.
        """
        params: dict[str, Any] = {
            "name": city,
            "count": 3,
            "language": "en",
            "format": "json",
        }
        try:
            resp = requests.get(GEOCODING_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise GeocodeError(f"API request failed: {e}") from e

        results = data.get("results", [])
        if not results:
            raise GeocodeError(f"No results for '{city}'")

        best = results[0]
        lat = best["latitude"]
        lon = best["longitude"]
        resolved = f"{best.get('name', city)}, {best.get('country', '')}"
        if best.get("admin1"):
            resolved += f" ({best['admin1']})"
        return lat, lon, resolved

    def get_forecast(
        self,
        lat: float,
        lon: float,
        date_from: date,
        date_to: date,
    ) -> list[DayWeather]:
        """Fetch daily weather for a date range.

        Returns a list of DayWeather, one per day between date_from and date_to.
        Raises ForecastError on API failure.
        """
        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,weather_code,"
                "uv_index_max,wind_speed_10m_max,"
                "daylight_duration"
            ),
            "timezone": "auto",
            "forecast_days": 16,
        }
        try:
            resp = requests.get(FORECAST_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise ForecastError(f"API error: {e}") from e
        except ValueError as e:
            raise ForecastError(f"Invalid JSON response: {e}") from e

        daily_data = data.get("daily", {})
        if not daily_data:
            raise ForecastError("No daily data in API response")

        times = daily_data.get("time", [])
        t_max = daily_data.get("temperature_2m_max", [])
        t_min = daily_data.get("temperature_2m_min", [])
        precip = daily_data.get("precipitation_sum", [])
        codes = daily_data.get("weather_code", [])
        uv = daily_data.get("uv_index_max", [])
        wind = daily_data.get("wind_speed_10m_max", [])
        daylight = daily_data.get("daylight_duration", [])

        results: list[DayWeather] = []
        for i, day_str in enumerate(times):
            day = date.fromisoformat(day_str)
            if date_from <= day <= date_to:
                results.append(DayWeather(
                    date=day,
                    temp_max_c=t_max[i] if i < len(t_max) else 0.0,
                    temp_min_c=t_min[i] if i < len(t_min) else 0.0,
                    precipitation_mm=precip[i] if i < len(precip) else 0.0,
                    weather_code=codes[i] if i < len(codes) else 0,
                    uv_index_max=uv[i] if i < len(uv) else 0.0,
                    wind_speed_max_kmh=wind[i] if i < len(wind) else 0.0,
                    daylight_hours=(
                        daylight[i] / 3600.0 if i < len(daylight) else 0.0
                    ),
                ))

        if not results:
            raise ForecastError(
                f"No forecast data available for {date_from}–{date_to}"
            )
        return results