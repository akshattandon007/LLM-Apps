"""Vehicle Safety Agent — queries NHTSA for open recalls."""

import urllib.parse
from typing import Optional

import httpx

from saferide.models import Recall, VehicleCheck


_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject a mock client for testing."""
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client(timeout=15.0)


NHTSA_RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle"


def _rate_recall_severity(summary: str, component: str) -> str:
    """Heuristic severity rating based on component and summary keywords."""
    critical = {"air bags", "brake", "steering", "fuel system", "fire", "engine stall"}
    high = {"transmission", "suspension", "electrical", "wheel", "tire", "seat belt"}
    medium = {"lighting", "visibility", "instrument", "structure", "door"}

    text = (summary + " " + component).lower()
    if any(k in text for k in critical):
        return "critical"
    if any(k in text for k in high):
        return "high"
    if any(k in text for k in medium):
        return "medium"
    return "low"


def check_by_vin(vin: str) -> VehicleCheck:
    """Query NHTSA for recalls by VIN (17-character identifier)."""
    vin = vin.strip().upper()
    url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?vin={urllib.parse.quote(vin)}"

    try:
        resp = _get_client().get(url)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return VehicleCheck(
            vin=vin, make="", model="", year=0,
            status="error", message=f"NHTSA query failed: {e}", source="live"
        )

    results = data.get("results", [])
    if not results:
        return VehicleCheck(
            vin=vin, make="", model="", year=0,
            status="clear", message="No recalls found for this VIN.", source="live"
        )

    first = results[0]
    recalls = []
    for r in results:
        recall = Recall(
            nhtsa_id=r.get("nhtsaCampaignNumber", "N/A"),
            component=r.get("component", "Unknown"),
            summary=r.get("summary", "No summary provided."),
            consequence=r.get("consequence", ""),
            remedy=r.get("remedy", "Contact dealer."),
            safety_risk=_rate_recall_severity(
                r.get("summary", ""), r.get("component", "")
            ),
            report_date=r.get("reportReceivedDate", ""),
        )
        recalls.append(recall)

    return VehicleCheck(
        vin=vin,
        make=first.get("make", "Unknown"),
        model=first.get("model", "Unknown"),
        year=int(first.get("modelYear", 0)),
        recalls=recalls,
        recall_count=len(recalls),
        status="recall_found",
        message=f"Found {len(recalls)} open recall(s).",
        source="live",
    )


def check_by_ymm(make: str, model: str, year: int) -> VehicleCheck:
    """Query NHTSA for recalls by make/model/year (no VIN)."""
    params = {
        "make": make,
        "model": model,
        "modelYear": str(year),
    }
    try:
        resp = _get_client().get(NHTSA_RECALLS, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return VehicleCheck(
            vin=None, make=make, model=model, year=year,
            status="error", message=f"NHTSA query failed: {e}", source="live"
        )

    results = data.get("results", [])
    if not results:
        return VehicleCheck(
            vin=None, make=make, model=model, year=year,
            status="clear", message="No recalls found for this vehicle.", source="live"
        )

    recalls = []
    for r in results:
        recall = Recall(
            nhtsa_id=r.get("nhtsaCampaignNumber", "N/A"),
            component=r.get("component", "Unknown"),
            summary=r.get("summary", "No summary provided."),
            consequence=r.get("consequence", ""),
            remedy=r.get("remedy", "Contact dealer."),
            safety_risk=_rate_recall_severity(
                r.get("summary", ""), r.get("component", "")
            ),
            report_date=r.get("reportReceivedDate", ""),
        )
        recalls.append(recall)

    return VehicleCheck(
        vin=None,
        make=make,
        model=model,
        year=year,
        recalls=recalls,
        recall_count=len(recalls),
        status="recall_found",
        message=f"Found {len(recalls)} open recall(s).",
        source="live",
    )


def _simulate_vehicle_check(make: str, model: str, year: int) -> VehicleCheck:
    """Demo data for offline mode or when APIs are unreachable."""
    return VehicleCheck(
        vin="SIMULATED",
        make=make,
        model=model,
        year=year,
        recalls=[
            Recall(
                nhtsa_id="SIM-24V-001",
                component="Air Bags",
                summary="Front passenger airbag may not deploy due to a sensor calibration error.",
                consequence="In the event of a crash, the airbag may not deploy, increasing injury risk.",
                remedy="Dealer will recalibrate the occupant classification sensor. No cost.",
                safety_risk="critical",
                report_date="2024-06-15",
                source="simulated",
            ),
            Recall(
                nhtsa_id="SIM-24V-042",
                component="Electrical System",
                summary="Battery management system may overestimate state of charge, causing unexpected shutdown.",
                consequence="Vehicle may stall without warning while driving, increasing crash risk.",
                remedy="Dealer will update the BMS firmware. No cost.",
                safety_risk="high",
                report_date="2024-08-22",
                source="simulated",
            ),
        ],
        recall_count=2,
        status="recall_found",
        message="Found 2 open recall(s).",
        source="simulated",
    )