"""
BreatheSmart MCP Agent — Air Quality & Pollen Intelligence Server.

Exposes MCP tools for real-time air quality, pollen, and UV data
using the free Open-Meteo Air Quality API (zero-auth, no key required).
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("breathesmart")

# ── Constants ────────────────────────────────────────────────────────────
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
DEFAULT_DAYS = 1
MAX_FORECAST_DAYS = 7

# Pollen parameter groups
POLLEN_TYPES = {
    "alder_pollen": "Alder",
    "birch_pollen": "Birch",
    "grass_pollen": "Grass",
    "mugwort_pollen": "Mugwort",
    "olive_pollen": "Olive",
    "ragweed_pollen": "Ragweed",
}

POLLUTANT_LABELS = {
    "pm2_5": "PM2.5 (Fine Particles)",
    "pm10": "PM10 (Coarse Particles)",
    "ozone": "Ozone (O₃)",
    "nitrogen_dioxide": "Nitrogen Dioxide (NO₂)",
    "sulphur_dioxide": "Sulfur Dioxide (SO₂)",
    "carbon_monoxide": "Carbon Monoxide (CO)",
}

AQI_LEVELS = [
    (0, 50, "Good", "🟢"),
    (51, 100, "Moderate", "🟡"),
    (101, 150, "Unhealthy for Sensitive Groups", "🟠"),
    (151, 200, "Unhealthy", "🔴"),
    (201, 300, "Very Unhealthy", "🟣"),
    (301, 999, "Hazardous", "⚫"),
]

POLLEN_LEVELS = [
    (0, 20, "Low", "🟢"),
    (21, 50, "Moderate", "🟡"),
    (51, 100, "High", "🟠"),
    (101, 999, "Very High", "🔴"),
]

UV_LEVELS = [
    (0, 2, "Low", "🟢"),
    (3, 5, "Moderate", "🟡"),
    (6, 7, "High", "🟠"),
    (8, 10, "Very High", "🔴"),
    (11, 999, "Extreme", "🟣"),
]

# ── Helper Functions ─────────────────────────────────────────────────────

def _classify(value: Optional[float], levels: list[tuple[int, int, str, str]]) -> dict:
    """Classify a numeric value into a level label and emoji."""
    if value is None:
        return {"label": "N/A", "emoji": "⬜", "value": None}
    for lo, hi, label, emoji in levels:
        if lo <= value <= hi:
            return {"label": label, "emoji": emoji, "value": value}
    return {"label": "Unknown", "emoji": "❓", "value": value}


def _fetch_air_quality(
    latitude: float,
    longitude: float,
    current_params: list[str],
    hourly_params: Optional[list[str]] = None,
    forecast_days: int = 0,
) -> dict:
    """Fetch air quality data from Open-Meteo."""
    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(current_params),
        "timezone": "auto",
    }
    if hourly_params and forecast_days > 0:
        params["hourly"] = ",".join(hourly_params)
        params["forecast_days"] = min(forecast_days, MAX_FORECAST_DAYS)

    resp = requests.get(AIR_QUALITY_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _build_aqi_summary(aqi_value: Optional[float]) -> str:
    """Build human-readable AQI description."""
    level = _classify(aqi_value, AQI_LEVELS)
    if aqi_value is None:
        return "Air quality data unavailable."
    return (
        f"{level['emoji']} **US AQI: {int(aqi_value)}** — {level['label']}.\n\n"
        f"**Recommendation:**\n"
        + {
            "Good": "Great day to be active outdoors!",
            "Moderate": "Sensitive individuals should limit prolonged outdoor exertion.",
            "Unhealthy for Sensitive Groups": "People with respiratory/heart conditions should reduce outdoor activity.",
            "Unhealthy": "Everyone should reduce prolonged outdoor exertion.",
            "Very Unhealthy": "Avoid all outdoor physical activity.",
            "Hazardous": "Stay indoors. Health emergency — everyone affected.",
        }.get(level["label"], "No specific recommendations.")
    )


# ── MCP Server Setup ───────────────────────────────────────────────────

server = Server("breathesmart")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_current_air_quality",
            description="Get the current Air Quality Index (US AQI/European AQI) and pollutant levels (PM2.5, PM10, Ozone, NO₂, SO₂, CO) for a location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees (e.g., 40.7128)",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees (e.g., -74.0060)",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
        types.Tool(
            name="get_pollen_forecast",
            description="Get pollen forecast (grass, birch, alder, olive, ragweed, mugwort) for a location over the next N days.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days (1-7)",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 7,
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
        types.Tool(
            name="get_uv_index",
            description="Get the current UV Index for a location with health recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
        types.Tool(
            name="get_health_summary",
            description="Get an all-in-one health summary: AQI + sun protection + outdoor risk. Perfect for deciding if it's safe to go outside.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude in decimal degrees",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude in decimal degrees",
                    },
                    "location_name": {
                        "type": "string",
                        "description": "Optional human-friendly location name for the output",
                        "default": "Your location",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    lat = arguments["latitude"]
    lon = arguments["longitude"]

    try:
        if name == "get_current_air_quality":
            return await _handle_current_air_quality(lat, lon)
        elif name == "get_pollen_forecast":
            days = arguments.get("days", DEFAULT_DAYS)
            return await _handle_pollen_forecast(lat, lon, days)
        elif name == "get_uv_index":
            return await _handle_uv_index(lat, lon)
        elif name == "get_health_summary":
            loc_name = arguments.get("location_name", "Your location")
            return await _handle_health_summary(lat, lon, loc_name)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Could not reach air quality data service. Please try again later.\n\nDetails: {e}",
        )]
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ An unexpected error occurred: {e}",
        )]


# ── Tool Handlers ────────────────────────────────────────────────────────

async def _handle_current_air_quality(lat: float, lon: float) -> list[types.TextContent]:
    """Handle the current air quality tool."""
    data = _fetch_air_quality(
        lat, lon,
        current_params=["us_aqi", "european_aqi", "pm2_5", "pm10",
                        "ozone", "nitrogen_dioxide", "sulphur_dioxide",
                        "carbon_monoxide"],
    )
    current = data.get("current", {})

    us_aqi = current.get("us_aqi")
    eu_aqi = current.get("european_aqi")

    lines = ["## 🌬️ Current Air Quality\n"]

    # US AQI
    aqi_level = _classify(us_aqi, AQI_LEVELS)
    lines.append(f"**US AQI:** {aqi_level['emoji']} **{int(us_aqi) if us_aqi else 'N/A'}** — {aqi_level['label']}")

    # European AQI
    if eu_aqi is not None:
        lines.append(f"**European AQI:** {int(eu_aqi)}/100")

    lines.append("")

    # Pollutants
    lines.append("### Pollutants\n")
    lines.append("| Pollutant | Level | Status |")
    lines.append("|-----------|-------|--------|")

    # PM2.5 WHO guideline: 15 μg/m³ 24h mean
    pm25 = current.get("pm2_5")
    pm25_status = "🟢 Good" if pm25 is not None and pm25 < 15 else ("🟡 Elevated" if pm25 is not None else "N/A")
    lines.append(f"| PM2.5 | {pm25 if pm25 is not None else 'N/A'} μg/m³ | {pm25_status} |")

    # PM10 WHO guideline: 45 μg/m³ 24h mean
    pm10 = current.get("pm10")
    pm10_status = "🟢 Good" if pm10 is not None and pm10 < 45 else ("🟡 Elevated" if pm10 is not None else "N/A")
    lines.append(f"| PM10 | {pm10 if pm10 is not None else 'N/A'} μg/m³ | {pm10_status} |")

    ozone = current.get("ozone")
    if ozone is not None:
        ozone_status = "🟢 Normal" if ozone < 100 else ("🟡 Elevated" if ozone < 200 else "🔴 High")
        lines.append(f"| Ozone (O₃) | {ozone} μg/m³ | {ozone_status} |")

    no2 = current.get("nitrogen_dioxide")
    if no2 is not None:
        no2_status = "🟢 Good" if no2 < 40 else ("🟡 Elevated" if no2 < 200 else "🔴 High")
        lines.append(f"| NO₂ | {no2} μg/m³ | {no2_status} |")

    so2 = current.get("sulphur_dioxide")
    if so2 is not None:
        so2_status = "🟢 Good" if so2 < 20 else ("🟡 Elevated" if so2 < 100 else "🔴 High")
        lines.append(f"| SO₂ | {so2} μg/m³ | {so2_status} |")

    co = current.get("carbon_monoxide")
    if co is not None:
        co_status = "🟢 Good" if co < 4000 else ("🟡 Elevated" if co < 10000 else "🔴 High")
        lines.append(f"| CO | {co} μg/m³ | {co_status} |")

    lines.append("")

    # Health recommendation
    lines.append("### 💡 Health Recommendation")
    lines.append(_build_aqi_summary(us_aqi))

    return [types.TextContent(type="text", text="\n".join(lines))]


async def _handle_pollen_forecast(lat: float, lon: float, days: int) -> list[types.TextContent]:
    """Handle the pollen forecast tool."""
    pollen_params = list(POLLEN_TYPES.keys())

    data = _fetch_air_quality(
        lat, lon,
        current_params=pollen_params,
        hourly_params=pollen_params,
        forecast_days=days,
    )

    current = data.get("current", {})

    lines = ["## 🌿 Pollen Forecast\n"]

    # Current levels
    lines.append("### Current Pollen Levels\n")
    lines.append("| Pollen Type | Level | Status |")
    lines.append("|-------------|-------|--------|")

    has_current_pollen = False
    for param, display_name in POLLEN_TYPES.items():
        value = current.get(param)
        if value is not None:
            has_current_pollen = True
            level = _classify(value, POLLEN_LEVELS)
            lines.append(f"| {display_name} | {level['emoji']} {int(value)} grains/m³ | {level['label']} |")

    if not has_current_pollen:
        lines.append("| — | No pollen data currently available | — |")

    lines.append("")

    # Hourly forecast (show next 3 time slots)
    hourly = data.get("hourly")
    if hourly and hourly.get("time"):
        lines.append(f"### Hourly Outlook (next {min(3, days * 24)} hours)\n")

        # For each pollen type, show the trend
        for param, display_name in POLLEN_TYPES.items():
            values = hourly.get(param, [])
            if values and any(v is not None for v in values[:8]):  # Check if any non-None values
                valid_vals = [v for v in values[:8] if v is not None]
                if valid_vals:
                    avg = sum(valid_vals) / len(valid_vals)
                    level = _classify(avg, POLLEN_LEVELS)
                    lines.append(f"- **{display_name}:** {level['emoji']} ~{int(avg)} grains/m³ ({level['label']})")

    lines.append("")
    lines.append("💡 *Pollen counts vary by time of day — levels are typically highest mid-morning and early evening.*")

    return [types.TextContent(type="text", text="\n".join(lines))]


async def _handle_uv_index(lat: float, lon: float) -> list[types.TextContent]:
    """Handle the UV index tool."""
    data = _fetch_air_quality(
        lat, lon,
        current_params=["us_aqi", "uv_index", "uv_index_clear_sky"],
    )
    current = data.get("current", {})

    uv = current.get("uv_index")
    uv_clear = current.get("uv_index_clear_sky")
    us_aqi = current.get("us_aqi")

    lines = ["## ☀️ UV Index\n"]

    if uv is not None:
        level = _classify(uv, UV_LEVELS)
        lines.append(f"**Current UV Index:** {level['emoji']} **{uv}** — {level['label']}")

        sun_protection_map = {
            "Low": "No protection needed. Enjoy the day!",
            "Moderate": "Wear sunglasses and use SPF 30+ if outdoors for extended periods.",
            "High": "🏷️ SPF 30+ required. Seek shade during midday (10 AM — 4 PM).",
            "Very High": "⚠️ SPF 50+ essential. Minimize time outdoors between 10 AM — 4 PM.",
            "Extreme": "🚨 Stay indoors if possible. Extreme burn risk in minutes.",
        }

        lines.append("")
        lines.append(f"**Sun Protection Recommendation:**")
        lines.append(sun_protection_map.get(level["label"], "Use standard sun protection."))
    else:
        lines.append("UV index data currently unavailable for this location (nighttime or polar region).")

    if uv_clear is not None:
        lines.append("")
        lines.append(f"*Clear-sky UV Index estimate: {uv_clear} (what it would be without cloud cover)*")

    if us_aqi is not None:
        lines.append("")
        lines.append(f"**🌬️ US AQI:** {int(us_aqi)} — {_classify(us_aqi, AQI_LEVELS)['label']}")

    return [types.TextContent(type="text", text="\n".join(lines))]


async def _handle_health_summary(lat: float, lon: float, location_name: str) -> list[types.TextContent]:
    """Handle the all-in-one health summary tool."""
    data = _fetch_air_quality(
        lat, lon,
        current_params=["us_aqi", "european_aqi", "pm2_5", "pm10",
                        "ozone", "nitrogen_dioxide", "sulphur_dioxide",
                        "carbon_monoxide", "uv_index", "uv_index_clear_sky",
                        "grass_pollen", "birch_pollen", "alder_pollen",
                        "olive_pollen", "ragweed_pollen", "mugwort_pollen"],
    )
    current = data.get("current", {})

    us_aqi = current.get("us_aqi")
    uv = current.get("uv_index")

    lines = [f"## 🫁 BreatheSmart Health Summary — {location_name}\n"]

    # ── Air Quality ──
    aqi_level = _classify(us_aqi, AQI_LEVELS)
    lines.append(f"### Air Quality  {'🟢' if aqi_level['label'] == 'Good' else '🟡' if aqi_level['label'] == 'Moderate' else '🔴'}")
    lines.append(f"**AQI:** {aqi_level['emoji']} **{int(us_aqi) if us_aqi else 'N/A'}** — {aqi_level['label']}")

    # Key pollutants
    pm25 = current.get("pm2_5")
    pm10 = current.get("pm10")
    if pm25 is not None:
        lines.append(f"- **PM2.5:** {pm25} μg/m³ {'✅ within WHO guideline' if pm25 < 15 else '⚠️ above WHO guideline (15)'}")
    if pm10 is not None:
        lines.append(f"- **PM10:** {pm10} μg/m³ {'✅ within WHO guideline' if pm10 < 45 else '⚠️ above WHO guideline (45)'}")

    lines.append("")

    # ── Pollen ──
    lines.append("### Pollen  🌿")
    active_pollen = []
    for param, display_name in POLLEN_TYPES.items():
        value = current.get(param)
        if value is not None and value > 0:
            level = _classify(value, POLLEN_LEVELS)
            active_pollen.append(f"- **{display_name}:** {level['emoji']} {int(value)} grains/m³ ({level['label']})")

    if active_pollen:
        lines.extend(active_pollen)
    else:
        lines.append("No significant pollen levels detected. ✅")
    lines.append("")

    # ── UV ──
    lines.append("### UV Index  ☀️")
    if uv is not None:
        uv_level = _classify(uv, UV_LEVELS)
        lines.append(f"**UV Index:** {uv_level['emoji']} **{uv}** — {uv_level['label']}")
        if uv >= 3:
            lines.append("🛡️ Sun protection needed (SPF 30+, shade, sunglasses).")
        else:
            lines.append("Sun protection not needed for short exposure.")
    else:
        lines.append("UV data unavailable (nighttime). 🌙")
    lines.append("")

    # ── Go/No-Go ──
    lines.append("### 🏃 Outdoor Activity Verdict\n")

    risks = []
    if us_aqi is not None and us_aqi > 100:
        risks.append("Air quality is unhealthy")
    if uv is not None and uv > 6:
        risks.append("UV index is high or extreme")
    if active_pollen:
        # Check if any pollen is High or Very High
        for _, display_name in POLLEN_TYPES.items():
            value = current.get(list(POLLEN_TYPES.keys())[list(POLLEN_TYPES.values()).index(display_name)]) if display_name in POLLEN_TYPES.values() else None
        for param, display_name in POLLEN_TYPES.items():
            value = current.get(param)
            if value is not None:
                level = _classify(value, POLLEN_LEVELS)
                if level['label'] in ("High", "Very High"):
                    risks.append(f"High {display_name.lower()} pollen levels")

    if not risks:
        verdict = "✅ **All clear!** Great conditions for outdoor activities."
    elif len(risks) == 1:
        verdict = f"⚠️ **Moderate caution.** {risks[0]}."
    else:
        verdict = f"🔴 **Take precautions.** " + "; ".join(risks) + "."

    lines.append(verdict)

    return [types.TextContent(type="text", text="\n".join(lines))]


# ── Main Entry Point ─────────────────────────────────────────────────────

def main() -> None:
    """Run the BreatheSmart MCP server via stdio transport."""
    import mcp.server.stdio
    import anyio

    async def _run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="breathesmart",
                    server_version="1.0.0",
                ),
            )

    anyio.run(_run)


if __name__ == "__main__":
    main()
