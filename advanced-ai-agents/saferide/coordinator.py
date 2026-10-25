"""Coordinator — orchestrates all three agents for a complete trip safety report."""

from typing import Optional

from saferide.agents import vehicle_agent as vehicle
from saferide.agents import weather_agent as weather
from saferide.agents import trip_advisor as advisor
from saferide.models import TripReport, VehicleCheck


def run_full_check(
    make: str,
    model: str,
    year: int,
    origin: str,
    destination: str,
    waypoints: Optional[list[str]] = None,
    vin: Optional[str] = None,
) -> TripReport:
    """Run the full multi-agent pipeline: vehicle → weather → compile."""
    # Agent 1: Vehicle Safety Scout
    if vin:
        v_check = vehicle.check_by_vin(vin)
    else:
        v_check = vehicle.check_by_ymm(make, model, year)

    # Agent 2: Route Weather Scanner
    origin_fc, dest_fc, waypoint_fcs = weather.get_route_forecast(origin, destination, waypoints)

    # Map names for report
    origin_name = origin
    dest_name = destination

    # Agent 3: Trip Advisor — compile
    report = advisor.build_report(
        vehicle=v_check,
        origin_fc=origin_fc,
        dest_fc=dest_fc,
        waypoint_fcs=waypoint_fcs,
        origin_name=origin_name,
        dest_name=dest_name,
    )

    return report