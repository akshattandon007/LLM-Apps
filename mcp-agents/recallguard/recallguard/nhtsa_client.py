"""NHTSA API client for vehicle safety recall data.

All endpoints are zero-auth (public API). Rate limiting is per-IP;
this client keeps a shared httpx client with polite timeouts.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx

BASE_URL = "https://api.nhtsa.gov"

TIMEOUT = 15.0  # seconds


# ── domain types ────────────────────────────────────────────────────────────


@dataclass
class RecallRecord:
    """A single vehicle recall returned by the NHTSA API."""
    manufacturer: str
    nhtsa_campaign_number: str
    report_received_date: str
    component: str
    summary: str
    consequence: str
    remedy: str
    notes: str
    model_year: str
    make: str
    model: str
    park_it: bool
    park_outside: bool
    over_the_air_update: bool

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> "RecallRecord":
        return cls(
            manufacturer=d.get("Manufacturer", ""),
            nhtsa_campaign_number=d.get("NHTSACampaignNumber", ""),
            report_received_date=d.get("ReportReceivedDate", ""),
            component=d.get("Component", ""),
            summary=d.get("Summary", ""),
            consequence=d.get("Consequence", ""),
            remedy=d.get("Remedy", ""),
            notes=d.get("Notes", ""),
            model_year=str(d.get("ModelYear", "")),
            make=d.get("Make", ""),
            model=d.get("Model", ""),
            park_it=d.get("parkIt", False),
            park_outside=d.get("parkOutSide", False),
            over_the_air_update=d.get("overTheAirUpdate", False),
        )

    def short_summary(self) -> str:
        """One-line summary for listing."""
        return (
            f"[{self.nhtsa_campaign_number}] {self.manufacturer} – "
            f"{self.model_year} {self.make} {self.model} | "
            f"{self.component}"
        )

    def full_report(self) -> str:
        """Full formatted recall details."""
        lines = [
            f"🚗 RECALL: {self.nhtsa_campaign_number}",
            f"   Manufacturer: {self.manufacturer}",
            f"   Vehicle: {self.model_year} {self.make} {self.model}",
            f"   Component: {self.component}",
            f"   Reported: {self.report_received_date}",
            f"",
            f"   ⚠ Summary: {self.summary}",
            f"   ❗ Consequence: {self.consequence}",
            f"   ✅ Remedy: {self.remedy}",
        ]
        if self.notes:
            lines.append(f"   📝 Notes: {self.notes}")
        if self.park_it:
            lines.append("   🅿 STOP: Park your vehicle immediately — fire risk.")
        if self.park_outside:
            lines.append("   🏠 Park OUTSIDE — away from structures.")
        return "\n".join(lines)


# ── API client ──────────────────────────────────────────────────────────────


class NhtsaClient:
    """Thread-safe wrapper around the NHTSA public API."""

    def __init__(self) -> None:
        self._client = httpx.Client(timeout=TIMEOUT, follow_redirects=True)

    # ── discovery endpoints ──────────────────────────────────────────────

    def get_model_years(self) -> list[str]:
        """Return list of model years that have recall data."""
        resp = self._client.get(
            f"{BASE_URL}/products/vehicle/modelYears",
            params={"issueType": "r"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["modelYear"] for item in data.get("results", [])]

    def get_makes(self, model_year: str) -> list[str]:
        """Return list of manufacturers (makes) for a given model year."""
        resp = self._client.get(
            f"{BASE_URL}/products/vehicle/makes",
            params={"modelYear": model_year, "issueType": "r"},
        )
        resp.raise_for_status()
        data = resp.json()
        # Deduplicate makes (API sometimes returns duplicates)
        seen: set[str] = set()
        makes: list[str] = []
        for item in data.get("results", []):
            m = item["make"]
            if m not in seen:
                seen.add(m)
                makes.append(m)
        return sorted(makes)

    def get_models(self, make: str, model_year: str) -> list[str]:
        """Return list of models for a given make and year."""
        resp = self._client.get(
            f"{BASE_URL}/products/vehicle/models",
            params={
                "make": make.upper(),
                "modelYear": model_year,
                "issueType": "r",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        seen: set[str] = set()
        models: list[str] = []
        for item in data.get("results", []):
            m = item["model"]
            if m not in seen:
                seen.add(m)
                models.append(m)
        return sorted(models)

    # ── recall lookup endpoints ──────────────────────────────────────────

    def check_vehicle_recalls(
        self, make: str, model: str, model_year: str
    ) -> list[RecallRecord]:
        """Look up recalls for a specific vehicle."""
        resp = self._client.get(
            f"{BASE_URL}/recalls/recallsByVehicle",
            params={
                "make": make.upper(),
                "model": model,
                "modelYear": model_year,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return [RecallRecord.from_api(r) for r in data.get("results", [])]

    def get_recall_by_campaign(self, campaign_number: str) -> list[RecallRecord]:
        """Look up a specific recall by NHTSA campaign number (e.g. '20V682000')."""
        resp = self._client.get(
            f"{BASE_URL}/recalls/campaignNumber",
            params={"campaignNumber": campaign_number},
        )
        resp.raise_for_status()
        data = resp.json()
        return [RecallRecord.from_api(r) for r in data.get("results", [])]

    def close(self) -> None:
        self._client.close()