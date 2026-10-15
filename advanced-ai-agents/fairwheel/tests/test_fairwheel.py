"""Tests for FairWheel — hermetic via MockTransport, no network needed."""

import httpx
import pytest

from fairwheel import api
from fairwheel.agents import (
    cost_analyst,
    deal_reviewer,
    grievance_scout,
    recall_auditor,
    safety_scorer,
)
from fairwheel.models import (
    ComplaintCluster,
    ComplaintReport,
    CostReport,
    DealVerdict,
    RecallItem,
    RecallReport,
    SafetyReport,
    VehicleQuery,
)
from fairwheel.orchestrator import run_pipeline
from fairwheel.report import render_markdown


def make_client(routes: dict) -> httpx.Client:
    """Build a mock httpx client returning canned responses by URL prefix."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        for prefix, payload in routes.items():
            if url.startswith(prefix):
                if isinstance(payload, Exception):
                    return httpx.Response(500, text="boom")
                return httpx.Response(200, json=payload)
        return httpx.Response(404, text="no route")

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def reset_client():
    api.set_client(None)
    yield
    api.set_client(None)


SAMPLE_VEHICLE = VehicleQuery(year=2021, make="Honda", model="Accord", budget=25000, annual_miles=12000)


def test_safety_scorer_live():
    client = make_client(
        {
            "https://api.nhtsa.gov/SafetyRatings/modelyear": {
                "Count": 1,
                "Results": [{"VehicleDescription": "2021 Honda ACCORD 4 DR FWD", "VehicleId": 15895}],
            },
            "https://api.nhtsa.gov/SafetyRatings/VehicleId/15895": {
                "Count": 1,
                "Results": [{"OverallRating": "5", "OverallFrontCrashRating": "5", "OverallSideCrashRating": "5"}],
            },
        }
    )
    api.set_client(client)
    report = safety_scorer.run(SAMPLE_VEHICLE)
    assert report.source == "live"
    assert report.overall_rating == 5.0
    assert report.front_rating == 5.0
    assert report.vehicle_description == "2021 Honda ACCORD 4 DR FWD"


def test_safety_scorer_fallback_on_error():
    client = make_client({"https://api.nhtsa.gov/SafetyRatings/modelyear": Exception("down")})
    api.set_client(client)
    report = safety_scorer.run(SAMPLE_VEHICLE)
    assert report.source == "simulated"
    assert report.overall_rating is not None
    assert 3.0 <= report.overall_rating <= 5.0


def test_grievance_scout_live_clusters():
    client = make_client(
        {
            "https://api.nhtsa.gov/complaints/complaintsByVehicle": {
                "count": 3,
                "results": [
                    {"components": "ENGINE,ELECTRICAL SYSTEM", "summary": "Engine stalls at speed."},
                    {"components": "ENGINE", "summary": "Check engine light."},
                    {"components": "AIR BAGS", "summary": "Airbag light on."},
                ],
            }
        }
    )
    api.set_client(client)
    report = grievance_scout.run(SAMPLE_VEHICLE)
    assert report.source == "live"
    assert report.total_complaints == 3
    components = [c.component for c in report.clusters]
    assert "ENGINE" in components
    engine = next(c for c in report.clusters if c.component == "ENGINE")
    assert engine.count == 2
    assert "stalls" in engine.sample.lower()


def test_recall_auditor_live():
    client = make_client(
        {
            "https://api.nhtsa.gov/recalls/recallsByVehicle": {
                "Count": 2,
                "results": [
                    {
                        "NHTSACampaignNumber": "21V900000",
                        "Component": "SEAT BELTS:REAR",
                        "Summary": "Retractor may deactivate.",
                        "Consequence": "Injury risk.",
                        "Remedy": "Dealer replaces free.",
                    }
                ],
            }
        }
    )
    api.set_client(client)
    report = recall_auditor.run(SAMPLE_VEHICLE)
    assert report.source == "live"
    assert report.count == 1
    assert report.recalls[0].campaign_number == "21V900000"


def test_cost_analyst_live_xml():
    menu_xml = """<?xml version="1.0" encoding="UTF-8"?><menuItems><menuItem><text>Auto, 4 cyl, 1.5 L</text><value>43361</value></menuItem></menuItems>"""
    vehicle_xml = """<?xml version="1.0" encoding="UTF-8"?><vehicle><city08>30</city08><highway08>38</highway08><comb08>33</comb08></vehicle>"""

    def handler(request: httpx.Request) -> httpx.Response:
        if "menu/options" in str(request.url):
            return httpx.Response(200, text=menu_xml)
        if "/ws/rest/vehicle/43361" in str(request.url):
            return httpx.Response(200, text=vehicle_xml)
        return httpx.Response(404)

    api.set_client(httpx.Client(transport=httpx.MockTransport(handler)))
    report = cost_analyst.run(SAMPLE_VEHICLE)
    assert report.source == "live"
    assert report.combined_mpg == 33.0
    # 12000 mi/yr / 33 mpg * $3.50 = $1272.73/yr => $6363.64/5yr
    assert report.five_year_fuel_cost == pytest.approx(6363.64, abs=0.1)


def test_cost_analyst_fallback_on_bad_xml():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<not-xml")

    api.set_client(httpx.Client(transport=httpx.MockTransport(handler)))
    report = cost_analyst.run(SAMPLE_VEHICLE)
    assert report.source == "simulated"
    assert report.five_year_fuel_cost is not None


def test_deal_reviewer_worth_it():
    safety = SafetyReport(overall_rating=5.0, front_rating=5.0, side_rating=5.0)
    complaints = ComplaintReport(total_complaints=2, clusters=[ComplaintCluster("INFOTAINMENT", 2)])
    recalls = RecallReport(recalls=[])
    cost = CostReport(combined_mpg=40.0, annual_fuel_cost=1050.0, five_year_fuel_cost=5250.0)
    verdict = deal_reviewer.run(SAMPLE_VEHICLE, safety, complaints, recalls, cost)
    assert verdict.verdict == "WORTH IT"
    assert verdict.score >= 80
    assert verdict.talking_points


def test_deal_reviewer_hard_gate_avoid():
    safety = SafetyReport(overall_rating=2.0, front_rating=2.0, side_rating=2.0)
    complaints = ComplaintReport(total_complaints=0, clusters=[])
    recalls = RecallReport(recalls=[])
    cost = CostReport(combined_mpg=30.0, annual_fuel_cost=1400.0, five_year_fuel_cost=7000.0)
    verdict = deal_reviewer.run(SAMPLE_VEHICLE, safety, complaints, recalls, cost)
    assert verdict.verdict == "AVOID"
    assert any("below 3 stars" in r for r in verdict.reasons)


def test_deal_reviewer_recall_leverage():
    safety = SafetyReport(overall_rating=4.0)
    complaints = ComplaintReport(total_complaints=200, clusters=[ComplaintCluster("ENGINE", 120)])
    recalls = RecallReport(recalls=[RecallItem("24V064000", "AIR BAGS:SENSOR", "Sensor cracks.", "Airbag fails.", "Replace free.")])
    cost = CostReport(combined_mpg=25.0, annual_fuel_cost=1680.0, five_year_fuel_cost=8400.0)
    verdict = deal_reviewer.run(SAMPLE_VEHICLE, safety, complaints, recalls, cost)
    assert any("24V064000" in p for p in verdict.talking_points)
    assert verdict.verdict in {"WAIT", "AVOID"}


def test_pipeline_demo_produces_full_report():
    report = run_pipeline(SAMPLE_VEHICLE, demo=True)
    assert report.safety.source == "simulated"
    assert report.recalls.source == "simulated"
    assert report.complaints.source == "simulated"
    assert report.cost.source == "simulated"
    assert report.verdict.verdict in {"WORTH IT", "WAIT", "AVOID"}
    md = render_markdown(report)
    assert "FairWheel" in md
    assert "Negotiation talking points" in md
    assert "Simulated data" in md


def test_pipeline_live_with_mock_routes():
    client = make_client(
        {
            "https://api.nhtsa.gov/SafetyRatings/modelyear": {
                "Results": [{"VehicleDescription": "2021 Honda ACCORD 4 DR FWD", "VehicleId": 15895}],
            },
            "https://api.nhtsa.gov/SafetyRatings/VehicleId/15895": {
                "Results": [{"OverallRating": "5", "OverallFrontCrashRating": "5", "OverallSideCrashRating": "5"}],
            },
            "https://api.nhtsa.gov/complaints/complaintsByVehicle": {
                "count": 1,
                "results": [{"components": "ENGINE", "summary": "Stall."}],
            },
            "https://api.nhtsa.gov/recalls/recallsByVehicle": {
                "Count": 1,
                "results": [{"NHTSACampaignNumber": "21V111", "Component": "STEERING", "Summary": "Loss of assist.", "Consequence": "Crash risk.", "Remedy": "Free fix."}],
            },
        }
    )

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "menu/options" in url:
            return httpx.Response(200, text='<?xml version="1.0"?><menuItems><menuItem><text>Auto</text><value>43361</value></menuItem></menuItems>')
        if "vehicle/43361" in url:
            return httpx.Response(200, text='<?xml version="1.0"?><vehicle><city08>30</city08><highway08>38</highway08><comb08>33</comb08></vehicle>')
        # fall back to JSON routes
        for prefix, payload in {
            "https://api.nhtsa.gov/SafetyRatings/modelyear": {"Results": [{"VehicleDescription": "2021 Honda ACCORD 4 DR FWD", "VehicleId": 15895}]},
            "https://api.nhtsa.gov/SafetyRatings/VehicleId/15895": {"Results": [{"OverallRating": "5", "OverallFrontCrashRating": "5", "OverallSideCrashRating": "5"}]},
            "https://api.nhtsa.gov/complaints/complaintsByVehicle": {"count": 1, "results": [{"components": "ENGINE", "summary": "Stall."}]},
            "https://api.nhtsa.gov/recalls/recallsByVehicle": {"Count": 1, "results": [{"NHTSACampaignNumber": "21V111", "Component": "STEERING", "Summary": "Loss of assist.", "Consequence": "Crash risk.", "Remedy": "Free fix."}]},
        }.items():
            if url.startswith(prefix):
                return httpx.Response(200, json=payload)
        return httpx.Response(404, text="no route")

    api.set_client(httpx.Client(transport=httpx.MockTransport(handler)))
    report = run_pipeline(SAMPLE_VEHICLE)
    assert report.safety.source == "live"
    assert report.complaints.source == "live"
    assert report.recalls.source == "live"
    assert report.cost.source == "live"
    assert report.verdict.verdict in {"WORTH IT", "WAIT", "AVOID"}


def test_cli_demo_writes_output(tmp_path):
    from fairwheel.cli import main

    out = tmp_path / "report.md"
    rc = main(["--year", "2021", "--make", "Honda", "--model", "Accord", "--demo", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Verdict" in content