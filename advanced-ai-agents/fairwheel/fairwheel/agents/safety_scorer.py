"""Safety Scorer agent — pulls NHTSA 5-star crash ratings for a vehicle."""

from __future__ import annotations

import hashlib

from ..api import HTTPError, get_json
from ..models import SafetyReport, VehicleQuery

SAFETY_RATINGS_URL = "https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{make}/model/{model}"
VEHICLE_RATINGS_URL = "https://api.nhtsa.gov/SafetyRatings/VehicleId/{vehicle_id}"


def _simulate(query: VehicleQuery, error: str) -> SafetyReport:
    """Deterministic simulated safety data when the API is unreachable."""
    seed = int(hashlib.sha256(f"{query.year}{query.make}{query.model}".lower().encode()).hexdigest(), 16)
    rating = round(3 + (seed % 30) / 10, 1)  # 3.0 - 5.9 clipped later
    rating = min(5.0, max(3.0, rating))
    return SafetyReport(
        overall_rating=rating,
        front_rating=rating,
        side_rating=rating,
        vehicle_description=f"{query.year} {query.make.title()} {query.model.title()} (simulated)",
        source="simulated",
        error=error,
    )


def run(query: VehicleQuery) -> SafetyReport:
    try:
        resp = get_json(SAFETY_RATINGS_URL.format(year=query.year, make=query.make, model=query.model))
        results = resp.get("Results") or []
        if not results:
            return _simulate(query, "no safety ratings found for this vehicle")
        vehicle_id = results[0].get("VehicleId")
        description = results[0].get("VehicleDescription", "")

        detail = get_json(VEHICLE_RATINGS_URL.format(vehicle_id=vehicle_id), params={"format": "json"})
        detail_results = detail.get("Results") or [{}]
        row = detail_results[0]

        def _num(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        return SafetyReport(
            overall_rating=_num(row.get("OverallRating")),
            front_rating=_num(row.get("OverallFrontCrashRating")),
            side_rating=_num(row.get("OverallSideCrashRating")),
            vehicle_description=description,
            source="live",
        )
    except HTTPError as exc:
        return _simulate(query, str(exc))