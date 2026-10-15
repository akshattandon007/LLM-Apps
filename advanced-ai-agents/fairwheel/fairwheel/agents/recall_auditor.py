"""Recall Auditor agent — lists open NHTSA recall campaigns for a vehicle."""

from __future__ import annotations

import hashlib

from ..api import HTTPError, get_json
from ..models import RecallItem, RecallReport, VehicleQuery

RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle"


def _simulate(query: VehicleQuery, error: str) -> RecallReport:
    seed = int(hashlib.sha256(f"{query.make}{query.model}".lower().encode()).hexdigest(), 16)
    if seed % 3 == 0:  # simulate a recall-free vehicle ~1/3 of the time
        return RecallReport(recalls=[], source="simulated", error=error)
    return RecallReport(
        recalls=[
            RecallItem(
                campaign_number=f"SIM{query.year}{seed % 10000:04d}",
                component="AIR BAGS:SENSOR",
                summary="Front passenger seat weight sensor may crack and short circuit (simulated).",
                consequence="Air bag may not deploy as intended, increasing injury risk (simulated).",
                remedy="Dealers will replace the sensor free of charge (simulated).",
            ),
            RecallItem(
                campaign_number=f"SIM{query.year}{seed % 7000 + 1000:04d}",
                component="SEAT BELTS:REAR:RETRACTOR",
                summary="Second-row seat belt retractor may deactivate improperly (simulated).",
                consequence="Unsecured child restraint in a crash (simulated).",
                remedy="Dealers will replace the retractor free of charge (simulated).",
            ),
        ],
        source="simulated",
        error=error,
    )


def run(query: VehicleQuery) -> RecallReport:
    try:
        resp = get_json(
            RECALLS_URL,
            params={
                "make": query.make,
                "model": query.model,
                "modelYear": query.year,
            },
        )
        raw = resp.get("results") or []
        recalls = [
            RecallItem(
                campaign_number=str(item.get("NHTSACampaignNumber", "Unknown")),
                component=str(item.get("Component", "Unknown")),
                summary=str(item.get("Summary", "")),
                consequence=str(item.get("Consequence", "")),
                remedy=str(item.get("Remedy", "")),
            )
            for item in raw
        ]
        return RecallReport(recalls=recalls, source="live")
    except HTTPError as exc:
        return _simulate(query, str(exc))