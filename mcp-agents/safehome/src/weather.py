"""National Weather Service (NWS) API client for weather alerts and forecasts.

Free, zero-auth API from weather.gov. Requires a User-Agent header identifying
the application. Returns alerts, forecasts, and points metadata for any US
lat/lon coordinate.
"""

from __future__ import annotations

import httpx

USER_AGENT = "(SafeHome MCP, your-email@example.com)"

_forecast_cache: dict[str, dict] = {}
_alerts_cache: dict[str, list] = {}

CURRENT_ALERTS_URL = "https://api.weather.gov/alerts/active"
POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def get_active_alerts(lat: float, lon: float) -> list[dict]:
    """Get active weather alerts near a lat/lon coordinate.

    Returns a list of alert features (headline, severity, urgency,
    event type, instruction, etc.).
    """
    cache_key = f"{lat:.2f},{lon:.2f}"
    cached = _alerts_cache.get(cache_key)
    if cached is not None:
        return cached

    # NWS uses a 'point' parameter for point-relative alerts
    params = {"point": f"{lat},{lon}"}
    with httpx.Client(timeout=15.0, headers=_headers()) as client:
        resp = client.get(CURRENT_ALERTS_URL, params=params)
        if resp.status_code == 404:
            _alerts_cache[cache_key] = []
            return []
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features") or []
    alerts = []
    for f in features:
        props = f.get("properties") or {}
        alerts.append({
            "headline": props.get("headline") or "Unknown",
            "event": props.get("event") or "",
            "severity": props.get("severity") or "",
            "urgency": props.get("urgency") or "",
            "instruction": props.get("instruction") or "",
            "areaDesc": props.get("areaDesc") or "",
            "expires": (props.get("expires") or "")[:19] if props.get("expires") else "",
        })

    _alerts_cache[cache_key] = alerts
    return alerts


def get_alerts_for_state(state_code: str) -> list[dict]:
    """Get all active weather alerts for a state."""
    params = {"area": state_code}
    with httpx.Client(timeout=15.0, headers=_headers()) as client:
        resp = client.get(CURRENT_ALERTS_URL, params=params)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features") or []
    alerts = []
    for f in features[:30]:  # cap at 30
        props = f.get("properties") or {}
        alerts.append({
            "headline": props.get("headline") or "Unknown",
            "event": props.get("event") or "",
            "severity": props.get("severity") or "",
            "urgency": props.get("urgency") or "",
            "areaDesc": props.get("areaDesc") or "",
            "expires": (props.get("expires") or "")[:19] if props.get("expires") else "",
        })
    return alerts


def get_forecast(lat: float, lon: float) -> dict | None:
    """Get the NWS forecast for a lat/lon coordinate.

    Returns a dict with 'periods' (list of forecast periods), or None on error.
    """
    cache_key = f"{lat:.4f},{lon:.4f}"
    cached = _forecast_cache.get(cache_key)
    if cached is not None:
        return cached

    # Step 1: get the points endpoint for the forecast URL
    # NWS rejects coordinates beyond 4 decimal places; round them.
    lat_rounded = round(lat, 4)
    lon_rounded = round(lon, 4)
    points_url = POINTS_URL.format(lat=lat_rounded, lon=lon_rounded)
    with httpx.Client(timeout=15.0, headers=_headers()) as client:
        resp = client.get(points_url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        points_data = resp.json()

    forecast_url = (points_data.get("properties") or {}).get("forecast")
    if not forecast_url:
        return None

    # Step 2: get the actual forecast
    with httpx.Client(timeout=15.0, headers=_headers()) as client:
        resp2 = client.get(forecast_url)
        resp2.raise_for_status()
        forecast_data = resp2.json()

    periods = (forecast_data.get("properties") or {}).get("periods") or []

    # Extract relevant fields
    result = {
        "location": (points_data.get("properties") or {}).get("relativeLocation", {}).get("properties", {}).get("city", ""),
        "state": (points_data.get("properties") or {}).get("relativeLocation", {}).get("properties", {}).get("state", ""),
        "forecast_zone": (points_data.get("properties") or {}).get("forecastZone", ""),
        "periods": [
            {
                "name": p.get("name", ""),
                "temperature": p.get("temperature"),
                "tempUnit": p.get("temperatureUnit", "F"),
                "shortForecast": p.get("shortForecast", ""),
                "detailedForecast": p.get("detailedForecast", ""),
                "windSpeed": p.get("windSpeed", ""),
                "windDirection": p.get("windDirection", ""),
                "isDaytime": p.get("isDaytime", True),
            }
            for p in periods[:14]  # 7 days
        ],
    }

    _forecast_cache[cache_key] = result
    return result


def severity_sort_key(alert: dict) -> int:
    """Sort key for alert severity (most severe first)."""
    levels = {"Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
    return levels.get(alert.get("severity", ""), 5)


def format_alerts(alerts: list[dict]) -> str:
    """Format a list of alerts into a readable string."""
    if not alerts:
        return "No active weather alerts for this location. Good weather conditions."

    sorted_alerts = sorted(alerts, key=severity_sort_key)

    lines = [f"**{len(sorted_alerts)} Active Weather Alert(s):**\n"]
    for a in sorted_alerts[:10]:
        lines.append(
            f"- **{a.get('event')}** — Severity: {a.get('severity')} "
            f"(Urgency: {a.get('urgency')})\n"
            f"  {a.get('headline')[:150]}"
        )
        if a.get("instruction"):
            lines.append(f"  _Instruction:_ {a.get('instruction')[:200]}")
        if a.get("expires"):
            lines.append(f"  _Expires:_ {a.get('expires')}")
        lines.append("")
    return "\n".join(lines)


def format_forecast(forecast: dict) -> str:
    """Format a forecast into a readable string."""
    periods = forecast.get("periods", [])
    if not periods:
        return "No forecast available for this location."

    location_parts = []
    if forecast.get("location"):
        location_parts.append(forecast["location"])
    if forecast.get("state"):
        location_parts.append(forecast["state"])
    loc_str = ", ".join(location_parts) if location_parts else "Unknown"

    lines = [f"**7-Day Forecast for {loc_str}:**\n"]
    for p in periods[:14]:
        temp = p.get("temperature", "?")
        unit = p.get("tempUnit", "F")
        lines.append(
            f"- **{p.get('name')}**: {temp}{unit}, {p.get('shortForecast')}  "
            f"(Wind: {p.get('windSpeed')} {p.get('windDirection')})"
        )
    return "\n".join(lines)