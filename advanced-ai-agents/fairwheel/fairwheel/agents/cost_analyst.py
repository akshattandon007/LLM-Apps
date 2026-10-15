"""Cost Analyst agent — real MPG from fueleconomy.gov + deterministic fuel math."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET

from ..api import HTTPError, get_text
from ..models import CostReport, VehicleQuery

MENU_URL = "https://www.fueleconomy.gov/ws/rest/vehicle/menu/options"
VEHICLE_URL = "https://www.fueleconomy.gov/ws/rest/vehicle/{vehicle_id}"


def _simulate(query: VehicleQuery, error: str) -> CostReport:
    seed = int(hashlib.sha256(f"{query.year}{query.make}{query.model}".lower().encode()).hexdigest(), 16)
    combined_mpg = round(18 + (seed % 20) + (seed % 5) / 2, 1)  # 18-37.5 mpg band
    report = CostReport(
        combined_mpg=combined_mpg,
        city_mpg=round(combined_mpg * 0.85, 1),
        highway_mpg=round(combined_mpg * 1.2, 1),
        source="simulated",
        error=error,
    )
    report.compute_fuel_costs(query.annual_miles, query.fuel_price)
    return report


def _parse_mpg(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    def field(name: str):
        node = root.find(name)
        if node is None or node.text is None:
            return None
        try:
            val = float(node.text)
            return val if val >= 0 else None
        except ValueError:
            return None
    return {"city": field("city08"), "highway": field("highway08"), "combined": field("comb08")}


def run(query: VehicleQuery) -> CostReport:
    try:
        menu_xml = get_text(MENU_URL, params={"year": query.year, "make": query.make, "model": query.model})
        menu_root = ET.fromstring(menu_xml)
        vehicle_id = None
        for item in menu_root.iter("menuItem"):
            value = item.findtext("value", "").strip()
            if value:
                vehicle_id = value
                break
        if not vehicle_id:
            return _simulate(query, "no fueleconomy.gov config found for this vehicle")

        detail_xml = get_text(VEHICLE_URL.format(vehicle_id=vehicle_id))
        mpg = _parse_mpg(detail_xml)
        report = CostReport(
            combined_mpg=mpg["combined"],
            city_mpg=mpg["city"],
            highway_mpg=mpg["highway"],
            source="live",
        )
        report.compute_fuel_costs(query.annual_miles, query.fuel_price)
        return report
    except (HTTPError, ET.ParseError) as exc:
        return _simulate(query, str(exc))