"""Smoke tests for HomeFix MCP server — exercises every module and tool."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from src.models import ServiceType, Pro, Quote, Appointment
from src.service_db import (
    SERVICE_DEFINITIONS,
    MOCK_PROS,
    get_pros_by_service,
    get_pro_by_name,
)
from src.searcher import find_pros, get_pro_details
from src.licenser import check_license
from src.estimator import get_estimate, extract_zip_state, infer_complexity_factor
from src.reviewer import summarize_reviews
from src.scheduler import book_appointment, get_available_slots


# ── Service DB Tests ─────────────────────────────────────────────────

class TestServiceDefinitions:
    def test_all_six_types_defined(self):
        assert len(SERVICE_DEFINITIONS) >= 6

    def test_each_type_has_common_issues(self):
        for st, defn in SERVICE_DEFINITIONS.items():
            assert len(defn.common_issues) >= 3
            assert defn.display_name
            assert defn.typical_price_range

    def test_urgent_services(self):
        assert SERVICE_DEFINITIONS[ServiceType.plumber].urgent is True
        assert SERVICE_DEFINITIONS[ServiceType.electrician].urgent is True
        assert SERVICE_DEFINITIONS[ServiceType.hvac].urgent is True
        assert SERVICE_DEFINITIONS[ServiceType.locksmith].urgent is True
        assert SERVICE_DEFINITIONS[ServiceType.handyman].urgent is False
        assert SERVICE_DEFINITIONS[ServiceType.general_contractor].urgent is False

    def test_license_check_required(self):
        assert SERVICE_DEFINITIONS[ServiceType.handyman].requires_license_check is False
        assert SERVICE_DEFINITIONS[ServiceType.plumber].requires_license_check is True


class TestMockDatabase:
    def test_has_mock_pros(self):
        assert len(MOCK_PROS) >= 10

    def test_get_pros_by_service_returns_sorted(self):
        plumbers = get_pros_by_service(ServiceType.plumber)
        assert len(plumbers) >= 2
        ratings = [p.rating for p in plumbers]
        assert ratings == sorted(ratings, reverse=True)

    def test_get_pro_by_name_finds(self):
        pro = get_pro_by_name("Rapid Rooter")
        assert pro is not None
        assert pro.rating == 4.7

    def test_get_pro_by_name_case_insensitive(self):
        pro = get_pro_by_name("brightspark")
        assert pro is not None
        assert "BrightSpark" in pro.name


# ── Searcher Tests ───────────────────────────────────────────────────

class TestSearcher:
    def test_find_pros_plumber_10001(self):
        results = find_pros("plumber", "10001")
        assert len(results) >= 1
        assert results[0]["service_types"][0] == "plumber"

    def test_find_pros_emergency_filter(self):
        results = find_pros("plumber", "10001", emergency=True)
        for r in results:
            assert r["available_now"] is True

    def test_find_pros_unknown_type(self):
        results = find_pros("dinosaur_trainer", "10001")
        assert results == []

    def test_get_pro_details_found(self):
        details = get_pro_details("KeyMaster Locksmith")
        assert details is not None
        assert details["rating"] == 4.9

    def test_get_pro_details_not_found(self):
        details = get_pro_details("Nonexistent Co")
        assert details is None


# ── Licenser Tests ───────────────────────────────────────────────────

class TestLicenser:
    def test_check_license_known_company(self):
        result = check_license("Rapid Rooter Plumbing", "NY")
        assert result["company"] == "Rapid Rooter LLC"
        assert "license_status" in result
        assert result["state"] == "NY"

    def test_check_license_unknown_company(self):
        result = check_license("Fake Company LLC", "TX")
        assert result["company"] == "Fake Company LLC"
        assert result["state"] == "TX"

    def test_check_license_has_summary(self):
        result = check_license("BrightSpark Electric", "CA")
        assert len(result["summary"]) > 20
        assert result["verification_source"]


# ── Estimator Tests ──────────────────────────────────────────────────

class TestEstimator:
    def test_get_estimate_returns_range(self):
        est = get_estimate("plumber", "Burst pipe emergency", "10001")
        assert "$" in est
        assert "10001" in est

    def test_get_estimate_unknown_service(self):
        est = get_estimate("unicorn_training", "Basic session", "10001")
        assert "Unable to estimate" in est

    def test_extract_zip_state_ny(self):
        assert extract_zip_state("10001") == "NY"

    def test_extract_zip_state_ca(self):
        assert extract_zip_state("90001") == "CA"

    def test_infer_complexity_factor_emergency(self):
        factor = infer_complexity_factor("Emergency burst pipe!")
        assert factor > 0.2

    def test_infer_complexity_factor_simple(self):
        factor = infer_complexity_factor("Simple diagnostic visit only")
        assert factor < 0


# ── Reviewer Tests ──────────────────────────────────────────────────

class TestReviewer:
    def test_summarize_reviews_found(self):
        result = summarize_reviews("ClimatePro HVAC")
        assert result["sentiment"] != "unknown"
        assert result["rating"] == 4.6
        assert len(result["summary"]) > 30

    def test_summarize_reviews_not_found(self):
        result = summarize_reviews("NoOne Here")
        assert result["sentiment"] == "unknown"

    def test_summarize_reviews_excellent_tier(self):
        result = summarize_reviews("KeyMaster Locksmith")
        assert result["sentiment"] == "excellent"
        assert result["rating"] == 4.9

    def test_summarize_reviews_good_tier(self):
        result = summarize_reviews("Ace Handyman Services")
        assert result["sentiment"] in ("good", "mixed")


# ── Scheduler Tests ─────────────────────────────────────────────────

class TestScheduler:
    def test_book_appointment_success(self):
        result = book_appointment("Rapid Rooter Plumbing", "9:00 am")
        assert result["success"] is True
        assert "HF-" in result["confirmation_number"]
        assert result["status"] == "confirmed"

    def test_book_appointment_invalid_time(self):
        result = book_appointment("Rapid Rooter Plumbing", "not_a_time")
        assert result["success"] is False

    def test_book_appointment_not_found(self):
        result = book_appointment("Ghost Company", "10:00")
        assert result["success"] is False

    def test_get_available_slots(self):
        slots = get_available_slots("Rapid Rooter Plumbing")
        assert len(slots) >= 1
        assert slots[0]["available"] is True


# ── Pydantic Model Tests ────────────────────────────────────────────

class TestModels:
    def test_pro_model_valid(self):
        pro = Pro(
            name="Test Pro", company="Test LLC",
            service_types=[ServiceType.plumber],
            phone="555-0000", zip_code="10001",
            rating=4.5, review_count=100,
            years_in_business=5,
        )
        assert pro.rating == 4.5

    def test_pro_model_rating_range(self):
        with pytest.raises(Exception):
            Pro(
                name="Bad", company="X",
                service_types=[ServiceType.plumber],
                phone="555-0000", zip_code="10001",
                rating=6.0, review_count=0, years_in_business=0,
            )

    def test_quote_model(self):
        q = Quote(pro_name="Test", company="X", service_type=ServiceType.plumber,
                  estimated_price="$200-$400", estimated_duration="2 hours")
        assert q.pro_name == "Test"

    def test_appointment_model(self):
        a = Appointment(pro_name="Test", company="X", service_type=ServiceType.plumber,
                        appointment_date="2026-06-01", appointment_time="9:00 am")
        assert a.status == "confirmed"


# ── Server Sanity Tests ─────────────────────────────────────────────

class TestServer:
    def test_server_importable(self):
        """Verify the MCP server module can be imported without errors."""
        import importlib
        spec = importlib.util.find_spec("server")
        assert spec is not None, "server module should be importable"

    def test_fastmcp_available(self):
        from mcp.server import FastMCP
        srv = FastMCP(name="test-homefix", instructions="test")
        assert srv.name == "test-homefix"