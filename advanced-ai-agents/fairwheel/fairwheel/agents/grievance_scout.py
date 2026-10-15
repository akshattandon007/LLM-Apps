"""Grievance Scout agent — clusters NHTSA complaints by component theme."""

from __future__ import annotations

import hashlib
from collections import Counter

from ..api import HTTPError, get_json
from ..models import ComplaintCluster, ComplaintReport, VehicleQuery

COMPLAINTS_URL = "https://api.nhtsa.gov/complaints/complaintsByVehicle"
MAX_COMPLAINTS = 400  # cap for the clustering pass


def _simulate(query: VehicleQuery, error: str) -> ComplaintReport:
    seed = int(hashlib.sha256(f"{query.make}{query.model}".lower().encode()).hexdigest(), 16)
    total = 12 + (seed % 90)
    from ..models import ComplaintCluster

    clusters = [
        ComplaintCluster(component="ENGINE", count=total // 3, sample="Rough idle and hesitation at low speeds (simulated)."),
        ComplaintCluster(component="ELECTRICAL SYSTEM", count=total // 4, sample="Infotainment screen freezes and resets (simulated)."),
        ComplaintCluster(component="TRANSMISSION", count=total // 5, sample="Harsh shifting between 2nd and 3rd gear (simulated)."),
        ComplaintCluster(component="AIR BAGS", count=max(1, total // 12), sample="Air bag warning light intermittent (simulated)."),
    ]
    return ComplaintReport(
        total_complaints=total,
        clusters=[c for c in clusters if c.count > 0],
        source="simulated",
        error=error,
    )


def run(query: VehicleQuery) -> ComplaintReport:
    try:
        resp = get_json(
            COMPLAINTS_URL,
            params={
                "make": query.make,
                "model": query.model,
                "modelYear": query.year,
            },
        )
        raw = resp.get("results") or []
        counts: Counter = Counter()
        samples: dict[str, str] = {}
        for item in raw[:MAX_COMPLAINTS]:
            components = [p.strip().upper() for p in (item.get("components") or "").split(",") if p.strip()]
            for comp in components:
                counts[comp] += 1
                if comp not in samples and item.get("summary"):
                    samples[comp] = item["summary"][:220]
        clusters = [
            ComplaintCluster(component=comp, count=cnt, sample=samples.get(comp, ""))
            for comp, cnt in counts.most_common(6)
        ]
        return ComplaintReport(
            total_complaints=len(raw),
            clusters=clusters,
            source="live",
        )
    except HTTPError as exc:
        return _simulate(query, str(exc))