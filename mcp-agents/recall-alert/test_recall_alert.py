"""
Tests for recall-alert MCP server.
Uses MockTransport to simulate API responses without network calls.
"""

from __future__ import annotations

import json
import httpx
import pytest

from recall_client import (
    search_food_recall,
    search_vehicle_recall,
    RecallResult,
    set_client,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_client():
    """Reset the client before and after each test to avoid cross-test leaks."""
    set_client(None)
    yield
    set_client(None)


# ── RecallResult dataclass tests ─────────────────────────────────────────────

def test_recall_result_creation():
    """Verify the dataclass fields work as expected."""
    r = RecallResult(
        source="openFDA",
        recall_id="F-1234",
        product="Peanut Butter Crunchy 16oz",
        description="Contains undeclared peanuts",
        date="2026-11-01",
        classification="Class I",
    )
    assert r.source == "openFDA"
    assert r.recall_id == "F-1234"
    assert "Peanut" in r.product
    assert r.classification == "Class I"


def test_recall_result_defaults():
    """Verify optional fields have expected defaults."""
    r = RecallResult(
        source="NHTSA",
        recall_id="22V-123",
        product="Brake pedal assembly",
        description="Brake pedal may detach",
        date="2026-10-15",
        classification="Safety",
    )
    assert r.remedy == ""
    assert r.url == ""


# ── openFDA recall search tests ──────────────────────────────────────────────

FDA_RESPONSE = {
    "results": [
        {
            "recall_number": "F-3456-2025",
            "event_id": "98765",
            "product_description": "Crunchy Peanut Butter 16oz",
            "reason_for_recall": "Product may contain undeclared milk allergen",
            "remedial_actions": "Return to place of purchase for full refund",
            "recalling_firm": "Nutty Spreads Co.",
            "classification": "Class I",
            "report_date": "20251101",
            "product_type": "Food",
        },
    ]
}


def test_search_food_recall_returns_results():
    """Verify openFDA search returns parsed RecallResult objects."""
    def handler(req: httpx.Request) -> httpx.Response:
        assert "peanut" in str(req.url).lower()
        return httpx.Response(200, json=FDA_RESPONSE)

    set_client(httpx.Client(transport=httpx.MockTransport(handler)))

    results = search_food_recall("peanut butter")
    assert len(results) == 1
    r = results[0]
    assert r.source == "openFDA"
    assert "Peanut Butter" in r.product
    assert "Nutty Spreads Co." in r.description
    assert r.classification == "Class I"
    assert r.date == "2025-11-01"
    assert "Return" in r.remedy


def test_search_food_recall_empty():
    """Verify empty response returns empty list."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    set_client(httpx.Client(transport=httpx.MockTransport(handler)))

    results = search_food_recall("nonexistentproductxyz")
    assert len(results) == 0


def test_search_food_recall_api_error():
    """Verify API errors raise through to caller."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    set_client(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(httpx.HTTPStatusError):
        search_food_recall("anything")


# ── NHTSA recall search tests ────────────────────────────────────────────────

NHTSA_RESPONSE = {
    "results": [
        {
            "NHTSACampaignNumber": "22V-123",
            "Component": "SERVICE BRAKES, HYDRAULIC",
            "Summary": "Brake pedal may detach from pedal assembly",
            "Manufacturer": "Honda (American Honda Motor Co.)",
            "Remedy": "Dealers will inspect and repair free of charge",
        },
    ]
}


def test_search_vehicle_recall_found():
    """Verify NHTSA lookup by VIN returns parsed recalls."""
    def handler(req: httpx.Request) -> httpx.Response:
        assert "1HGCM82633A004352" in str(req.url)
        return httpx.Response(200, json=NHTSA_RESPONSE)

    set_client(httpx.Client(transport=httpx.MockTransport(handler)))

    results = search_vehicle_recall("1HGCM82633A004352")
    assert len(results) == 1
    r = results[0]
    assert r.source == "NHTSA"
    assert "Honda" in r.product
    assert "Brake pedal" in r.description
    assert r.classification == "Safety"
    assert "inspect and repair" in r.remedy


def test_search_vehicle_recall_invalid_vin():
    """Verify VIN validation rejects short/long VINs."""
    results = search_vehicle_recall("SHORT")
    assert len(results) == 0

    results = search_vehicle_recall("TOOLONGVINNUMBERHERE12345")
    assert len(results) == 0


def test_search_vehicle_recall_empty():
    """Verify empty NHTSA response returns empty list."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    set_client(httpx.Client(transport=httpx.MockTransport(handler)))

    results = search_vehicle_recall("1HGCM82633A004352")
    assert len(results) == 0


def test_search_vehicle_recall_api_error():
    """Verify NHTSA API errors propagate."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    set_client(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(httpx.HTTPStatusError):
        search_vehicle_recall("1HGCM82633A004352")
