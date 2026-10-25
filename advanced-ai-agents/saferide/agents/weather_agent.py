"""Weather Agent — forecasts for trip origin, destination, and waypoints."""

import urllib.parse
from dataclasses import dataclass
from typing import Optional

import httpx

from saferide.models import SegmentForecast, Waypoint


_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client(timeout=15.0)


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def geocode(location: str) -> Optional[Waypoint]:
    """Resolve a location name to coordinates via Open-Meteo Geocoding."""
    url = f"{GEOCODING_URL}?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
    try:
        resp = _get_client().get(url)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            r = results[0]
            return Waypoint(name=r.get("name", location), lat=r["latitude"], lon=r["longitude"])
    except Exception:
        pass
    return None


def get_forecast(lat: float, lon: float, name: str = "") -> SegmentForecast:
    """Fetch current weather forecast for coordinates."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,wind_gusts_10m,visibility",
        "timezone": "auto",
        "forecast_days": 1,
    }
    try:
        resp = _get_client().get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
    except Exception:
        return _simulate_forecast(lat, lon, name)

    temp = current.get("temperature_2m", 20.0)
    feels_like = current.get("apparent_temperature", temp)
    precip = current.get("precipitation", 0.0)
    wind = current.get("wind_speed_10m", 10.0)
    gust = current.get("wind_gusts_10m", 0.0)
    vis = current.get("visibility", 10000.0) / 1000.0  # m → km

    condition = _classify_condition(precip, wind, vis, temp)
    hazard, note = _assess_hazard(precip, wind, gust, vis, condition)

    return SegmentForecast(
        location=name or f"{lat:.3f},{lon:.3f}",
        lat=lat, lon=lon,
        temp_c=temp,
        feels_like_c=feels_like,
        precip_mm=precip,
        wind_speed_kmh=wind,
        wind_gust_kmh=gust,
        visibility_km=vis,
        condition=condition,
        hazard=hazard,
        hazard_note=note,
        source="live",
    )


def _classify_condition(precip: float, wind: float, vis: float, temp: float) -> str:
    if precip > 20:
        return "storm"
    if vis < 1.0:
        return "fog"
    if precip > 5:
        return "rain"
    if temp < -5:
        return "snow"
    if wind > 60:
        return "storm"
    if wind > 30:
        return "windy"
    return "clear"


def _assess_hazard(precip: float, wind: float, gust: float, vis: float, cond: str) -> tuple[bool, str]:
    notes = []
    if precip > 20:
        notes.append("Heavy precipitation — reduced visibility and hydroplaning risk.")
    if gust > 70:
        notes.append("Dangerous wind gusts — high-profile vehicles should use caution.")
    elif gust > 50:
        notes.append("Strong wind gusts — reduce speed and keep both hands on wheel.")
    if vis < 0.5:
        notes.append("Near-zero visibility — consider postponing travel.")
    elif vis < 1.5:
        notes.append("Low visibility — fog lights recommended.")
    if cond == "storm":
        notes.append("Storm conditions detected — delay travel if possible.")
    return bool(notes), " | ".join(notes) if notes else ""


def get_route_forecast(
    origin: str, destination: str, waypoints: Optional[list[str]] = None
) -> tuple[SegmentForecast, SegmentForecast, list[SegmentForecast]]:
    """Get forecasts for origin, destination, and all waypoints."""
    origin_wp = geocode(origin)
    dest_wp = geocode(destination)
    if not origin_wp:
        origin_wp = Waypoint(name=origin, lat=40.7128, lon=-74.0060)  # NYC fallback
    if not dest_wp:
        dest_wp = Waypoint(name=destination, lat=34.0522, lon=-118.2437)  # LA fallback

    origin_fc = get_forecast(origin_wp.lat, origin_wp.lon, origin_wp.name)
    dest_fc = get_forecast(dest_wp.lat, dest_wp.lon, dest_wp.name)

    waypoint_fcs: list[SegmentForecast] = []
    if waypoints:
        for wp_name in waypoints:
            wp = geocode(wp_name)
            if wp:
                waypoint_fcs.append(get_forecast(wp.lat, wp.lon, wp.name))

    return origin_fc, dest_fc, waypoint_fcs


def _simulate_forecast(lat: float, lon: float, name: str) -> SegmentForecast:
    """Return simulated weather when the API is unreachable."""
    return SegmentForecast(
        location=name or f"{lat:.3f},{lon:.3f}",
        lat=lat, lon=lon,
        temp_c=22.0,
        feels_like_c=20.0,
        precip_mm=0.0,
        wind_speed_kmh=15.0,
        wind_gust_kmh=25.0,
        visibility_km=16.0,
        condition="clear",
        hazard=False,
        hazard_note="",
        source="simulated",
    )