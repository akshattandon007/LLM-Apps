"""Trip Advisor Agent — compiles vehicle safety + weather + rest stops into report."""

from typing import Optional

from saferide.models import (
    RouteWeather,
    RestStop,
    SegmentForecast,
    TripReport,
    VehicleCheck,
    Waypoint,
)


def _overall_weather_rating(weather: RouteWeather) -> str:
    """Classify overall route weather."""
    origins = [weather.origin_forecast, weather.destination_forecast] + weather.waypoint_forecasts
    hazard_count = sum(1 for f in origins if f.hazard)
    if hazard_count >= 3:
        return "avoid"
    if hazard_count >= 1:
        return "caution"
    return "good"


def _build_weather_summary(weather: RouteWeather) -> str:
    parts = [
        f"📍 {weather.origin_name}: {weather.origin_forecast.temp_c:.0f}°C, "
        f"{weather.origin_forecast.condition}, wind {weather.origin_forecast.wind_speed_kmh:.0f} km/h"
    ]
    for wp in weather.waypoint_forecasts:
        parts.append(
            f"📍 {wp.location}: {wp.temp_c:.0f}°C, {wp.condition}, "
            f"wind {wp.wind_speed_kmh:.0f} km/h"
        )
    parts.append(
        f"📍 {weather.destination_name}: {weather.destination_forecast.temp_c:.0f}°C, "
        f"{weather.destination_forecast.condition}, wind {weather.destination_forecast.wind_speed_kmh:.0f} km/h"
    )
    return "\n".join(parts)


def _build_verdict(vehicle: VehicleCheck, weather: RouteWeather) -> str:
    issues = []
    if vehicle.status == "recall_found":
        critical = sum(1 for r in vehicle.recalls if r.safety_risk in ("critical", "high"))
        if critical > 0:
            issues.append(f"{critical} critical/high-severity recall(s) — address before driving")
    if weather.overall_rating == "avoid":
        issues.append("Severe weather along route — consider postponing trip")
    elif weather.overall_rating == "caution":
        issues.append("Weather hazards detected — drive with extra care")

    if not issues:
        return "✅ All clear — safe to drive!"
    return "⚠️  " + " | ".join(issues)


def build_report(
    vehicle: VehicleCheck,
    origin_fc: SegmentForecast,
    dest_fc: SegmentForecast,
    waypoint_fcs: Optional[list[SegmentForecast]] = None,
    rest_stops: Optional[list[RestStop]] = None,
    origin_name: str = "Origin",
    dest_name: str = "Destination",
) -> TripReport:
    """Assemble the full trip report from all agent outputs."""
    weather = RouteWeather(
        origin_name=origin_name,
        origin_forecast=origin_fc,
        destination_name=dest_name,
        destination_forecast=dest_fc,
        waypoint_forecasts=waypoint_fcs or [],
        total_hazards=sum(
            1 for f in [origin_fc, dest_fc] + (waypoint_fcs or []) if f.hazard
        ),
        source=origin_fc.source,
    )
    weather.overall_rating = _overall_weather_rating(weather)
    weather.total_hazards = sum(1 for f in [origin_fc, dest_fc] + (waypoint_fcs or []) if f.hazard)

    summary = _build_weather_summary(weather)
    verdict = _build_verdict(vehicle, weather)

    return TripReport(
        vehicle=vehicle,
        weather=weather,
        rest_stops=rest_stops or [],
        summary=summary,
        verdict=verdict,
    )