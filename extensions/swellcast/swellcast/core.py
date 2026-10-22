"""Core surf analysis: fetch marine + weather data, compute scores."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import date, datetime, timezone

from .models import Location, Location, SurfDay, SurfReport

MARINE_URL = (
    "https://marine-api.open-meteo.com/v1/marine"
    "?latitude={lat}&longitude={lon}"
    "&daily=wave_height_max,wave_direction_dominant,wave_period_max"
    ",swell_wave_height_max,swell_wave_direction_dominant,swell_wave_period_max"
    "&forecast_days={days}"
    "&timezone=auto"
)

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&daily=temperature_2m_max,wind_speed_10m_max,wind_direction_10m_dominant,weather_code"
    "&forecast_days={days}"
    "&timezone=auto"
)

# WMO weather codes → description
WMO_CODES: dict[int, str] = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _fetch_json(url: str) -> dict | None:
    """Fetch a URL and parse JSON."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def _wind_dir_label(deg: int | None) -> str:
    """Convert degrees to compass direction."""
    if deg is None:
        return "N/A"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(deg / 22.5) % 16
    return dirs[idx]


def _compass_to_deg(label: str) -> float | None:
    """Convert simple compass direction to approximate degrees (for score)."""
    mapping = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}
    return mapping.get(label)


def _wave_origin_angle(wave_dir: int | None, wind_dir: int | None) -> str:
    """Classify wind relative to swell direction."""
    if wave_dir is None or wind_dir is None:
        return "unknown"
    diff = abs(wave_dir - wind_dir)
    if diff > 180:
        diff = 360 - diff
    if diff <= 45:
        return "onshore"
    elif diff <= 135:
        return "cross-shore"
    else:
        return "offshore"


def _compute_score(day: SurfDay) -> tuple[float, str, str]:
    """Compute a surf-score (0-10) and conditions descriptor."""
    score = 5.0  # baseline

    notes = []
    wave_h = day.wave_height_m
    period_s = day.wave_period_s
    swell_h = day.swell_height_m

    # Wave height scoring
    if wave_h is not None:
        if wave_h < 0.3:
            score -= 2.5
            notes.append("Flat")
        elif wave_h < 0.6:
            score -= 1.0
            notes.append("Small")
        elif wave_h <= 2.0:
            score += 2.0
            notes.append("Good size")
        elif wave_h <= 3.5:
            score += 1.0
            notes.append("Big")
        else:
            score -= 1.0
            notes.append("Dangerous")

    # Swell period — longer = better quality
    sw_period = day.swell_period_s or period_s
    if sw_period is not None:
        if sw_period < 7:
            score -= 1.5
            notes.append("Short period")
        elif sw_period < 10:
            score += 0.5
            notes.append("Moderate period")
        elif sw_period < 14:
            score += 1.5
            notes.append("Long period")
        else:
            score += 2.0
            notes.append("Excellent period")

    # Wind direction relative to swell
    if day.wave_dir_deg is not None and day.wind_dir_deg is not None:
        regime = _wave_origin_angle(day.wave_dir_deg, day.wind_dir_deg)
        if regime == "offshore":
            score += 1.0
            notes.append("Offshore wind")
        elif regime == "onshore":
            score -= 1.0
            notes.append("Onshore wind")

    # Wind speed
    if day.wind_speed_kmh is not None:
        if day.wind_speed_kmh > 40:
            score -= 1.5
            notes.append("Gusty")
        elif day.wind_speed_kmh > 25:
            score -= 0.5
            notes.append("Windy")

    # Clamp
    score = max(0.0, min(10.0, round(score, 1)))

    # Label
    if score >= 7.5:
        label = "Excellent 🏄"
    elif score >= 5.5:
        label = "Good 👍"
    elif score >= 3.5:
        label = "Fair 🌊"
    else:
        label = "Poor 😞"

    condition = ", ".join(notes) if notes else "Mixed conditions"
    return score, label, condition


def fetch_report(location: Location, days: int = 5) -> SurfReport:
    """Fetch marine + weather data and return a full SurfReport."""
    report = SurfReport(location=location, generated=datetime.now(timezone.utc).isoformat())

    # Fetch data in parallel (simple sequential — two calls is fast)
    marine = _fetch_json(MARINE_URL.format(lat=location.lat, lon=location.lon, days=days))
    weather = _fetch_json(WEATHER_URL.format(lat=location.lat, lon=location.lon, days=days))

    if not marine:
        # Return empty report
        return report

    md = marine.get("daily", {})

    def _safe_list(key: str) -> list:
        return md.get(key, []) or []

    dates_raw = _safe_list("time")
    wave_heights = _safe_list("wave_height_max")
    wave_dirs = _safe_list("wave_direction_dominant")
    wave_periods = _safe_list("wave_period_max")
    swell_heights = _safe_list("swell_wave_height_max")
    swell_dirs = _safe_list("swell_wave_direction_dominant")
    swell_periods = _safe_list("swell_wave_period_max")

    # Weather daily
    wd = weather.get("daily", {}) if weather else {}
    temps = wd.get("temperature_2m_max", []) or []
    winds_speed = wd.get("wind_speed_10m_max", []) or []
    winds_dir = wd.get("wind_direction_10m_dominant", []) or []
    wmo_codes = wd.get("weather_code", []) or []

    for i, raw_date in enumerate(dates_raw):
        try:
            dt = date.fromisoformat(raw_date.replace("Z", ""))
        except (ValueError, AttributeError):
            dt = date.today()

        day = SurfDay(dt=dt)
        if i < len(wave_heights) and wave_heights[i] is not None:
            day.wave_height_m = round(float(wave_heights[i]), 2)
        if i < len(wave_dirs) and wave_dirs[i] is not None:
            day.wave_dir_deg = int(wave_dirs[i])
        if i < len(wave_periods) and wave_periods[i] is not None:
            day.wave_period_s = round(float(wave_periods[i]), 1)
        if i < len(swell_heights) and swell_heights[i] is not None:
            day.swell_height_m = round(float(swell_heights[i]), 2)
        if i < len(swell_dirs) and swell_dirs[i] is not None:
            day.swell_dir_deg = int(swell_dirs[i])
        if i < len(swell_periods) and swell_periods[i] is not None:
            day.swell_period_s = round(float(swell_periods[i]), 1)
        if i < len(temps) and temps[i] is not None:
            day.temp_max_c = round(float(temps[i]), 1)
        if i < len(winds_speed) and winds_speed[i] is not None:
            day.wind_speed_kmh = round(float(winds_speed[i]), 1)
        if i < len(winds_dir) and winds_dir[i] is not None:
            day.wind_dir_deg = int(winds_dir[i])
        if i < len(wmo_codes) and wmo_codes[i] is not None:
            day.weather_code = int(wmo_codes[i])

        day.score, day.score_label, day.conditions_note = _compute_score(day)
        report.days.append(day)

    return report