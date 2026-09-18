"""SunGuard — UV / sun / heat / air quality MCP server.

Run with:  mcp run sunguard/server.py
Or:        python -m sunguard.server
"""

from __future__ import annotations

import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from sunguard.models import (
    AirQualityResult,
    BurnTimeResult,
    HeatSafetyResult,
    HourlyUVResult,
    OutdoorPlanResult,
    RiskLevel,
    SunSafetyResult,
)
from sunguard.weather import (
    calculate_burn_time,
    calculate_heat_index,
    geocode,
    get_air_quality,
    get_heat_advisories,
    get_uv_forecast,
    aqi_risk_level,
    heat_index_risk,
    overall_risk,
    uv_risk_level,
    NWSAlert,
)

mcp = FastMCP(
    "SunGuard",
    instructions=(
        "Sun safety, UV index, heat index, and air quality checks for everyday people. "
        "Ask about outdoor safety, burn time, or best hours for the beach."
    ),
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _resolve_location(zip_or_city: str) -> tuple[str, float, float]:
    """Resolve a location string to (name, lat, lon)."""
    geo = geocode(zip_or_city)
    return geo.name, geo.latitude, geo.longitude


def _build_recommendation(risk: RiskLevel, domain: str = "sun") -> str:
    """Generate a human-readable recommendation based on risk level."""
    if risk == RiskLevel.LOW:
        if domain == "sun":
            return "Low UV — minimal sun protection needed. Enjoy your day!"
        elif domain == "heat":
            return "No heat concerns. Stay hydrated."
        elif domain == "aqi":
            return "Air quality is good. Enjoy outdoor activities."
    elif risk == RiskLevel.MODERATE:
        if domain == "sun":
            return "Moderate UV — wear sunscreen SPF 15+, hat, and sunglasses."
        elif domain == "heat":
            return "Moderate heat — drink water and take breaks in shade."
        elif domain == "aqi":
            return "Air quality is moderate. Sensitive groups should limit prolonged exertion."
    elif risk == RiskLevel.HIGH:
        if domain == "sun":
            return "High UV — seek shade 10am-4pm, wear SPF 30+, hat, and protective clothing."
        elif domain == "heat":
            return "High heat index — limit outdoor activity, stay hydrated."
        elif domain == "aqi":
            return "Unhealthy for sensitive groups. Limit prolonged outdoor exertion."
    elif risk == RiskLevel.VERY_HIGH:
        if domain == "sun":
            return "Very high UV — avoid midday sun, SPF 50+, protective clothing, sunglasses."
        elif domain == "heat":
            return "Very high heat — avoid strenuous activity, stay in A/C if possible."
        elif domain == "aqi":
            return "Unhealthy air quality. Everyone should limit outdoor exertion."
    elif risk == RiskLevel.EXTREME:
        return "EXTREME — avoid outdoor activity. Stay indoors, keep hydrated."
    return "Check conditions before heading out."


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def sun_safety(zip_or_city: str) -> SunSafetyResult:
    """Combined UV + heat + AQI verdict for today. Provides a summary with risk level and recommendation."""
    name, lat, lon = _resolve_location(zip_or_city)

    uv = get_uv_forecast(lat, lon)
    aq = get_air_quality(lat, lon)
    heat_adv = get_heat_advisories(lat, lon)

    uv_r = uv_risk_level(uv.max_uv)
    aqi_r = aqi_risk_level(aq.aqi)
    hi = calculate_heat_index(uv.max_temp)
    heat_r = heat_index_risk(hi)

    combined = overall_risk(uv_r, heat_r, aqi_r)

    # Build recommendation
    parts = []
    if combined in ("very_high", "extreme"):
        parts.append(_build_recommendation(RiskLevel(combined)))
    else:
        parts.append(_build_recommendation(RiskLevel(uv_r), "sun"))
        if heat_r in ("high", "very_high", "extreme"):
            parts.append(_build_recommendation(RiskLevel(heat_r), "heat"))
        if aqi_r in ("high",):
            parts.append(_build_recommendation(RiskLevel(aqi_r), "aqi"))

    source = "live" if uv.source == "live" else "simulated"

    return SunSafetyResult(
        location=name,
        uv_index=uv.max_uv,
        uv_risk=RiskLevel(uv_r),
        temperature=uv.max_temp,
        heat_index=hi if uv.max_temp >= 27 else None,
        heat_risk=RiskLevel(heat_r) if heat_r != "low" else None,
        aqi=aq.aqi,
        aqi_risk=RiskLevel(aqi_r) if aqi_r != "low" else None,
        overall_risk=RiskLevel(combined),
        recommendation=" ".join(parts),
        source=source,
    )


@mcp.tool()
def hourly_uv(lat: float, lon: float, date: str) -> HourlyUVResult:
    """UV index hour-by-hour for a specific date. Returns list of hourly UV values."""
    uv = get_uv_forecast(lat, lon)
    if not uv.hourly_uv:
        return HourlyUVResult(
            location=f"{lat},{lon}",
            date=date,
            hours=[],
            peak_uv=0,
            peak_hour="",
            source="simulated",
        )

    peak_hour_entry = max(uv.hourly_uv, key=lambda h: h["uv_index"])
    source = "live" if uv.source == "live" else "simulated"

    return HourlyUVResult(
        location=f"{lat},{lon}",
        date=date,
        hours=uv.hourly_uv,
        peak_uv=peak_hour_entry["uv_index"],
        peak_hour=f"{peak_hour_entry['hour']}:00",
        source=source,
    )


@mcp.tool()
def skin_burn_time(skin_type: str, uv_index: float) -> BurnTimeResult:
    """How long until sunburn. skin_type is Fitzpatrick scale (I-VI)."""
    burn_minutes, desc = calculate_burn_time(skin_type, uv_index)

    if burn_minutes <= 15:
        rec = "Extremely high burn risk — seek shade immediately or stay indoors."
    elif burn_minutes <= 30:
        rec = "High burn risk — apply SPF 50+ and wear protective clothing."
    elif burn_minutes <= 60:
        rec = "Moderate burn risk — SPF 30+ recommended, reapply every 2 hours."
    else:
        rec = "Low burn risk — basic sun protection still recommended."

    return BurnTimeResult(
        skin_type=skin_type.upper(),
        uv_index=uv_index,
        burn_time_minutes=burn_minutes,
        description=desc,
        recommendation=rec,
    )


@mcp.tool()
def heat_safety(zip_or_city: str) -> HeatSafetyResult:
    """Heat index + heat advisory check for today."""
    name, lat, lon = _resolve_location(zip_or_city)

    uv = get_uv_forecast(lat, lon)
    hi = calculate_heat_index(uv.max_temp)
    heat_r = heat_index_risk(hi)

    advisories = get_heat_advisories(lat, lon)
    adv_texts = [a.headline for a in advisories]

    source = "live" if uv.source == "live" else "simulated"

    return HeatSafetyResult(
        location=name,
        temperature=uv.max_temp,
        heat_index=hi,
        heat_index_risk=RiskLevel(heat_r),
        advisories=adv_texts,
        recommendation=_build_recommendation(RiskLevel(heat_r), "heat"),
        source=source,
    )


@mcp.tool()
def air_quality_check(zip_or_city: str) -> AirQualityResult:
    """AQI with activity recommendations for sensitive groups."""
    name, lat, lon = _resolve_location(zip_or_city)

    aq = get_air_quality(lat, lon)
    aqi_r = aqi_risk_level(aq.aqi)

    source = "live" if aq.source == "live" else "simulated"

    if aq.aqi <= 50:
        level = "Good"
    elif aq.aqi <= 100:
        level = "Moderate"
    elif aq.aqi <= 150:
        level = "Unhealthy for Sensitive Groups"
    elif aq.aqi <= 200:
        level = "Unhealthy"
    else:
        level = "Very Unhealthy"

    return AirQualityResult(
        location=name,
        aqi=aq.aqi,
        aqi_level=level,
        risk=RiskLevel(aqi_r),
        recommendation=_build_recommendation(RiskLevel(aqi_r), "aqi"),
        source=source,
    )


@mcp.tool()
def outdoor_plan(zip_or_city: str, activity: str, time: str) -> OutdoorPlanResult:
    """'Is it safe to take the kids to the beach at 2pm?' Returns safety assessment."""
    name, lat, lon = _resolve_location(zip_or_city)

    uv = get_uv_forecast(lat, lon)
    aq = get_air_quality(lat, lon)
    hi = calculate_heat_index(uv.max_temp)

    # Parse requested hour from time string
    try:
        hour = int(time.split(":")[0])
    except (ValueError, IndexError):
        hour = 12

    # Get UV at the requested hour
    uv_at_time = 0
    for h in uv.hourly_uv:
        if h["hour"] == hour:
            uv_at_time = h["uv_index"]
            break

    concerns = []
    uv_r = uv_risk_level(uv_at_time)
    heat_r = heat_index_risk(hi)
    aqi_r = aqi_risk_level(aq.aqi)

    if uv_r in ("high", "very_high", "extreme"):
        concerns.append(f"UV index {uv_at_time} ({uv_r}) at {time}")
    if heat_r in ("high", "very_high", "extreme"):
        concerns.append(f"Heat index {hi}°C ({heat_r})")
    if aqi_r == "high":
        concerns.append(f"AQI {aq.aqi} (unhealthy)")

    is_safe = len(concerns) == 0

    if is_safe:
        rec = f"Yes, {activity} at {time} looks safe. Enjoy!"
    else:
        rec = f"Caution: {'; '.join(concerns)}. {'Consider rescheduling or taking precautions.' if not is_safe else ''}"

    source = "live" if uv.source == "live" else "simulated"

    return OutdoorPlanResult(
        location=name,
        activity=activity,
        time=time,
        uv_index=uv_at_time,
        temperature=uv.max_temp,
        heat_index=hi if uv.max_temp >= 27 else None,
        aqi=aq.aqi,
        is_safe=is_safe,
        concerns=concerns,
        recommendation=rec,
        source=source,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()