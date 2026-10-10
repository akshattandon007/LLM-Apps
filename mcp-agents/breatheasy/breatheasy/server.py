"""MCP server (stdio transport) exposing breatheasy's four tools.

House style: every tool returns FORMATTED MARKDOWN TEXT (headings, emoji,
structured fields) — never raw JSON.  Unknown places and API failures are
returned as friendly error strings, never raised as exceptions.

Run with:  python -m breatheasy serve
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .advice import (
    POLLEN_EMOJI,
    POLLEN_GUIDANCE,
    POLLEN_TYPES,
    POLLUTANT_DISPLAY,
    POLLUTANT_UNITS,
    aqi_band,
    pollen_bucket,
    top_pollutant,
)
from .api import (
    OpenMeteoClient,
    daily_max_aqi,
    pollen_peak_per_type,
    today_from_payload,
    worst_hour_today,
)
from .geo import GeoLookupError, resolve_place

MAX_FORECAST_DAYS = 7

mcp = FastMCP("breatheasy")

_client: OpenMeteoClient | None = None


def get_client() -> OpenMeteoClient:
    """Shared default client (lazy; tests monkeypatch this)."""
    global _client
    if _client is None:
        _client = OpenMeteoClient()
    return _client


def _resolve_or_error(
    client: OpenMeteoClient, place: str
) -> tuple[tuple[float, float, str] | None, str | None]:
    """Resolve a place, or return a friendly markdown error string.

    Both unknown places AND backend failures (HTTP errors, timeouts, bad
    JSON from the geocoding API) become strings — tools never raise.
    """
    try:
        return resolve_place(place, client), None
    except GeoLookupError:
        return (
            None,
            f"😕 **Could not find '{place}'** — try a city name like "
            "'Brooklyn', 'City, State', or 'lat,lon' "
            "(e.g. '40.71,-74.01').",
        )
    except Exception as exc:  # noqa: BLE001 - friendly string, not a raise
        return (
            None,
            f"⚠️ Could not fetch location data for '{place}': {exc}",
        )


# -- Tool 1: current air quality ------------------------------------------

@mcp.tool(
    description=(
        "Current US AQI, European AQI, top pollutant, EPA category and "
        "plain-language advice for a place (city name or 'lat,lon')."
    )
)
async def get_air_quality(place: str) -> str:
    client = get_client()
    where, err = _resolve_or_error(client, place)
    if err is not None:
        return err
    lat, lon, label = where
    try:
        data = client.air_quality(lat, lon, days=1)
    except Exception as exc:  # noqa: BLE001 - friendly string, not a raise
        return f"⚠️ Could not fetch air quality data for {label}: {exc}"
    return format_air_quality(data, label)


def format_air_quality(data: dict, label: str) -> str:
    current = data.get("current") or {}
    us = current.get("us_aqi")
    eu = current.get("european_aqi")
    if us is None and eu is None:
        return (
            f"## 🌬️ Air quality in {label}\n\n"
            "No current air quality data is available right now."
        )
    aqi = us if us is not None else eu
    band = aqi_band(aqi)
    source = (
        "US AQI"
        if us is not None
        else "European AQI (US AQI not reported)"
    )
    lines = [
        f"## 🌬️ Air quality in {label}",
        "",
        f"**{source}:** **{aqi}** — {band.category} {band.emoji}",
    ]
    if us is not None and eu is not None:
        lines.append(f"**European AQI:** {eu}")
    tp = top_pollutant(current)
    if tp is not None:
        key, value = tp
        lines.append(
            f"**Top pollutant:** {POLLUTANT_DISPLAY.get(key, key)} "
            f"({value:g} {POLLUTANT_UNITS.get(key, '')})"
        )
    lines.append(f"**Advice:** {band.advice}")
    return "\n".join(lines)


# -- Tool 2: air forecast -------------------------------------------------

@mcp.tool(
    description=(
        "Daily max AQI trend for `days` (clamped 1-7) from hourly data, "
        "the worst hour today, and plain advice."
    )
)
async def get_air_forecast(place: str, days: int = 3) -> str:
    days = min(max(int(days), 1), MAX_FORECAST_DAYS)
    client = get_client()
    where, err = _resolve_or_error(client, place)
    if err is not None:
        return err
    lat, lon, label = where
    try:
        data = client.air_quality(lat, lon, days=days)
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Could not fetch air quality forecast for {label}: {exc}"
    return format_air_forecast(data, label, days)


def format_air_forecast(data: dict, label: str, days: int) -> str:
    hourly = data.get("hourly") or {}
    daily = daily_max_aqi(hourly)
    head = f"## 📈 Air quality forecast for {label} ({days}-day forecast)"
    if not daily:
        return head + "\n\nNo air quality forecast data is available for this location."
    today = today_from_payload(data)
    worst = worst_hour_today(hourly, today)
    overall_band = aqi_band(max(value for _, value in daily))
    lines = [head, "", "| Date | Max AQI | Category |", "|---|---|---|"]
    for date, value in daily[:days]:
        band = aqi_band(value)
        lines.append(f"| {date} | {value} | {band.category} {band.emoji} |")
    if worst is not None:
        hh, value = worst
        band = aqi_band(value)
        lines.extend(
            [
                "",
                f"**Worst hour today ({today}):** {hh} — AQI {value} "
                f"({band.category} {band.emoji})",
            ]
        )
    lines.extend(["", f"**Advice:** {overall_band.advice}"])
    return "\n".join(lines)


# -- Tool 3: pollen forecast ----------------------------------------------

@mcp.tool(
    description=(
        "Per pollen type (alder, birch, grass, mugwort, olive, ragweed): "
        "peak level in P/m³, low/medium/high label and one-line guidance. "
        "Regions/seasons without pollen data report 'no data'."
    )
)
async def get_pollen_forecast(place: str, days: int = 1) -> str:
    days = min(max(int(days), 1), MAX_FORECAST_DAYS)
    client = get_client()
    where, err = _resolve_or_error(client, place)
    if err is not None:
        return err
    lat, lon, label = where
    try:
        data = client.air_quality(lat, lon, days=days)
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Could not fetch pollen forecast for {label}: {exc}"
    return format_pollen_forecast(data, label, days)


def format_pollen_forecast(data: dict, label: str, days: int) -> str:
    peaks = pollen_peak_per_type(data.get("hourly") or {})
    head = f"## 🌼 Pollen forecast for {label} ({days}-day peak)"
    if not peaks:
        return (
            head
            + "\n\nNo pollen data is available for this region/season. "
            "Open-Meteo pollen coverage is mostly Europe; values are NULL "
            "elsewhere and outside pollen season."
        )
    lines = [
        head,
        "",
        "| Pollen | Peak (P/m³) | Level | Guidance |",
        "|---|---|---|---|",
    ]
    for key, display in POLLEN_TYPES:
        if key in peaks:
            peak = peaks[key]
            bucket = pollen_bucket(peak)
            lines.append(
                f"| {display} | {peak:g} | {bucket} "
                f"{POLLEN_EMOJI[bucket]} | {POLLEN_GUIDANCE[bucket]} |"
            )
        else:
            lines.append(
                f"| {display} | — | no data 🚫 | "
                "No pollen data for this region/season. |"
            )
    return "\n".join(lines)


# -- Tool 4: wildfire smoke alert -----------------------------------------

@mcp.tool(
    description=(
        "Check today's US AQI and PM2.5 for elevated pollution that may "
        "include wildfire smoke (honest, non-diagnostic wording)."
    )
)
async def get_wildfire_smoke_alert(place: str) -> str:
    client = get_client()
    where, err = _resolve_or_error(client, place)
    if err is not None:
        return err
    lat, lon, label = where
    try:
        data = client.air_quality(lat, lon, days=1)
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ Could not fetch air quality data for {label}: {exc}"
    return format_wildfire_alert(data, label)


def format_wildfire_alert(data: dict, label: str) -> str:
    current = data.get("current") or {}
    us = current.get("us_aqi")
    pm = current.get("pm2_5")
    lines = [f"## 🔥 Wildfire smoke check for {label}", ""]
    parts = []
    if us is not None:
        band = aqi_band(us)
        parts.append(f"US AQI **{us}** ({band.category} {band.emoji})")
    if pm is not None:
        parts.append(f"PM2.5 **{pm:g}** µg/m³")
    lines.append(" · ".join(parts) if parts else "No current air quality data.")
    elevated = (us is not None and us >= 151) or (pm is not None and pm >= 55.4)
    if elevated:
        lines.append("")
        lines.append(
            "⚠️ **Elevated pollution detected that may include wildfire "
            "smoke.** High AQI and PM2.5 can also come from other sources — "
            "check local alerts, reduce outdoor exertion, and keep windows "
            "closed."
        )
    else:
        lines.append("")
        lines.append(
            "✅ **Air looks clear** — no elevated smoke signals right now."
        )
    return "\n".join(lines)