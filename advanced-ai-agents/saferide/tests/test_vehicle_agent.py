"""Tests for the Vehicle Safety Agent."""

import httpx

from saferide.agents.vehicle_agent import (
    _rate_recall_severity,
    check_by_vin,
    check_by_ymm,
    set_client,
)


def test_severity_rating():
    """Test severity heuristic classifies correctly."""
    assert _rate_recall_severity("Air bags may not deploy", "Air Bags") == "critical"
    assert _rate_recall_severity("Transmission may slip", "Transmission") == "high"
    assert _rate_recall_severity("Lighting may dim", "Lighting") == "medium"
    assert _rate_recall_severity("Floor mat may shift", "Interior") == "low"


def test_check_by_vin_api_error_fallback():
    """When NHTSA 500s, return an error VehicleCheck — not crashed."""
    def handler(request):
        return httpx.Response(500, json={"error": "Internal server error"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        result = check_by_vin("1HGCM82633A004352")

    assert result.status == "error"
    assert "NHTSA query failed" in result.message
    assert result.vin == "1HGCM82633A004352"


def test_check_by_vin_no_records():
    """When NHTSA returns empty results, report clear status."""
    def handler(request):
        return httpx.Response(200, json={"results": [], "count": 0})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        result = check_by_vin("1HGCM82633A004352")

    assert result.status == "clear"
    assert result.recall_count == 0


def test_check_by_vin_with_records():
    """When NHTSA returns recall records, parse them correctly."""
    def handler(request):
        return httpx.Response(200, json={
            "results": [
                {
                    "nhtsaCampaignNumber": "24V-001",
                    "component": "Air Bags",
                    "summary": "Front passenger airbag may not deploy",
                    "consequence": "Increased injury risk",
                    "remedy": "Replace sensor module",
                    "reportReceivedDate": "2024-06-15",
                    "make": "HONDA",
                    "model": "CIVIC",
                    "modelYear": 2019,
                }
            ]
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        result = check_by_vin("1HGCM82633A004352")

    assert result.status == "recall_found"
    assert result.recall_count == 1
    assert result.recalls[0].component == "Air Bags"
    assert result.recalls[0].safety_risk == "critical"
    assert result.vin == "1HGCM82633A004352"


def test_check_by_ymm_empty():
    """check_by_ymm with no results returns clear."""
    def handler(request):
        return httpx.Response(200, json={"results": [], "count": 0})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        set_client(client)
        result = check_by_ymm("Toyota", "Camry", 2024)

    assert result.status == "clear"
    assert result.make == "Toyota"
    assert result.model == "Camry"
    assert result.year == 2024