"""
recall_client.py — API clients for openFDA (food/drug/device) and NHTSA (vehicle) recalls.

Each function returns a list of recall dicts with a normalized schema.
Supports `set_client()` injection for hermetic testing.
"""

from __future__ import annotations

import httpx
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class RecallResult:
    """Normalized recall record across all sources."""
    source: str          # "openFDA" or "NHTSA"
    recall_id: str
    product: str
    description: str
    date: str            # ISO date string
    classification: str  # "Class I", "Class II", "Class III", "Safety", "Unknown"
    remedy: str = ""
    url: str = ""


# ── Injectable client ────────────────────────────────────────────────────────

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject a mock client for testing (set None to use real HTTP)."""
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client()


# ── openFDA food/drug/device recall search ───────────────────────────────────

OPENFDA_BASE = "https://api.fda.gov"


def _normalize_fda_recall(entry: dict) -> RecallResult | None:
    """Map an openFDA enforcement entry to our normalized schema."""
    try:
        # Classify by status
        classification = entry.get("classification", "").strip() or "Unknown"
        # Map codes like "Class I" to readable
        cl = classification.replace("_", " ").title()
        if cl.startswith("Class"):
            classification = cl
        else:
            classification = "Unknown"

        # Report date
        report_date = entry.get("report_date", "")
        if len(report_date) == 8:
            date_str = f"{report_date[:4]}-{report_date[4:6]}-{report_date[6:]}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        product = (
            entry.get("product_description", "")
            or entry.get("product_type", "")
            or "Unknown product"
        )

        reason = entry.get("reason_for_recall", "") or ""
        remedy = entry.get("remedial_actions", "") or ""
        recalling_firm = entry.get("recalling_firm", "") or ""

        desc_parts = [f"Firm: {recalling_firm}"] if recalling_firm else []
        if reason:
            desc_parts.append(f"Reason: {reason}")
        description = " | ".join(desc_parts) if desc_parts else "No details available."

        return RecallResult(
            source="openFDA",
            recall_id=entry.get("recall_number", f"FDA-{entry.get('event_id', '?')}"),
            product=product[:200],
            description=description[:500],
            date=date_str,
            classification=classification,
            remedy=remedy[:300] if remedy else "",
            url=f"{OPENFDA_BASE}/drug/enforcement.json?search=recall_number:{entry.get('recall_number', '')}",
        )
    except Exception:
        return None


def search_food_recall(product_name: str, limit: int = 10) -> list[RecallResult]:
    """Search openFDA food/drug enforcement for a product name."""
    url = f"{OPENFDA_BASE}/drug/enforcement.json"
    params = {
        "search": f"product_description:{product_name}",
        "limit": min(limit, 50),
    }

    client = _get_client()
    resp = client.get(url, params=params, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    results: list[RecallResult] = []
    for entry in data.get("results", []):
        r = _normalize_fda_recall(entry)
        if r:
            results.append(r)
    return results


# ── NHTSA vehicle recall lookup ─────────────────────────────────────────────

NHTSA_BASE = "https://api.nhtsa.gov"


def _normalize_nhtsa_recall(entry: dict) -> RecallResult | None:
    """Map an NHTSA recall campaign entry to our normalized schema."""
    try:
        comp = entry.get("Component", "") or ""
        summary = entry.get("Summary", "") or ""
        manufacturer = entry.get("Manufacturer", "") or ""
        nhtsa_id = entry.get("NHTSACampaignNumber", "") or ""
        remedy = entry.get("Remedy", "") or ""

        product = f"{manufacturer} — {comp}".strip()
        if not product.strip("— "):
            product = "Vehicle recall"

        desc_parts = []
        if summary:
            desc_parts.append(summary[:400])
        if manufacturer and not summary:
            desc_parts.append(f"Manufacturer: {manufacturer}")
        description = "\n".join(desc_parts) if desc_parts else "No details available."

        date_str = datetime.now().strftime("%Y-%m-%d")

        return RecallResult(
            source="NHTSA",
            recall_id=nhtsa_id or "N/A",
            product=product[:200],
            description=description[:500],
            date=date_str,
            classification="Safety",
            remedy=remedy[:300] if remedy else "",
            url=f"https://www.nhtsa.gov/recalls?nhtsaId={nhtsa_id}" if nhtsa_id else "",
        )
    except Exception:
        return None


def search_vehicle_recall(vin: str) -> list[RecallResult]:
    """Check NHTSA for vehicle recalls by VIN (17 characters)."""
    clean_vin = vin.strip().upper()
    if len(clean_vin) != 17:
        return []

    url = f"{NHTSA_BASE}/recalls/recallsByVehicle"
    params = {"vin": clean_vin}

    client = _get_client()
    resp = client.get(url, params=params, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    results: list[RecallResult] = []
    for entry in data.get("results", []):
        r = _normalize_nhtsa_recall(entry)
        if r:
            results.append(r)
    return results
