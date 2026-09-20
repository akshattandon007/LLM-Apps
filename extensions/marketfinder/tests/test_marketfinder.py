"""Tests for MarketFinder — mocked API calls and simulated fallback."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import ANY

import httpx
import pytest

from marketfinder.api import (
    filter_by_program,
    get_market_details,
    search_by_zip,
    search_csa,
    set_client,
)
from marketfinder.models import (
    CSALocation,
    CSASearchResult,
    Market,
    MarketDetails,
    MarketSearchResult,
    Program,
)


@pytest.fixture(autouse=True)
def reset_client() -> None:
    """Reset the module-level client before and after each test."""
    set_client(None)
    yield
    set_client(None)


# ── helpers ───────────────────────────────────────────────────────────


def _mock_data() -> list[dict[str, Any]]:
    return [
        {
            "id": "test-001",
            "marketname": "Test Market 1",
            "address": "123 Main St",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "x": "-122.68",
            "y": "45.51",
            "distance": "0.3 mi",
            "acceptssnap": "Y",
            "acceptswic": "Y",
            "acceptswiccash": "N",
            "acceptssfmnp": "N",
            "organic": "Y",
            "products": "Vegetables, fruit",
            "season1date": "June–Oct",
            "season1time": "Sat 8am–2pm",
            "website": "https://test1.org",
            "contact": "Jane Doe",
            "email": "jane@test1.org",
            "phone": "503-555-1000",
        },
        {
            "id": "test-002",
            "marketname": "Test Market 2",
            "address": "456 Oak Ave",
            "city": "Beaverton",
            "state": "OR",
            "zip": "97005",
            "x": "-122.80",
            "y": "45.48",
            "distance": "5.0 mi",
            "acceptssnap": "N",
            "acceptswic": "N",
            "acceptswiccash": "N",
            "acceptssfmnp": "N",
            "organic": "N",
            "products": "Crafts",
            "website": "",
        },
    ]


def _mock_csa_data() -> list[dict[str, Any]]:
    return [
        {
            "id": "csa-test-001",
            "operationname": "Test CSA Farm",
            "address": "789 Country Rd",
            "city": "Portland",
            "state": "OR",
            "zip": "97202",
            "y": "45.50",
            "x": "-122.64",
            "distance": "3.2 mi",
            "website": "https://testcsa.org",
            "contact": "Farmer John",
            "phone": "503-555-2000",
        }
    ]


def _build_response(data: list[dict[str, Any]]) -> httpx.Response:
    return httpx.Response(200, json={"data": data})


# ── search_by_zip ─────────────────────────────────────────────────────


class TestSearchByZip:
    def test_returns_markets_from_api(self) -> None:
        """Happy path — real API response parsed into Market models."""
        client = httpx.Client(transport=httpx.MockTransport(lambda _: _build_response(_mock_data())))
        set_client(client)

        result = search_by_zip("97201", radius_miles=10)

        assert isinstance(result, MarketSearchResult)
        assert result.count == 2
        assert result.zip == "97201"
        assert result.radius_miles == 10

        m1 = result.markets[0]
        assert m1.market_name == "Test Market 1"
        assert m1.accepts_snap is True
        assert m1.accepts_wic is True
        assert m1.latitude == 45.51
        assert m1.longitude == -122.68
        assert m1.website == "https://test1.org"

        m2 = result.markets[1]
        assert m2.market_name == "Test Market 2"
        assert m2.accepts_snap is False
        assert m2.organic is False

    def test_fallback_to_simulated_on_api_failure(self) -> None:
        """When api fails (timeout/5xx), simulated Portland data is returned."""
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(503))
        )
        set_client(client)

        result = search_by_zip("99999", radius_miles=10)

        assert result.count == 5  # 5 simulated markets
        assert result.markets[0].market_name == "Portland Farmers Market — PSU"
        assert result.markets[0].accepts_snap is True

    def test_empty_response(self) -> None:
        """API returns no data — empty result, not simulated."""
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: _build_response([]))
        )
        set_client(client)

        result = search_by_zip("00000", radius_miles=10)

        assert result.count == 0
        assert result.markets == []


# ── filter_by_program ─────────────────────────────────────────────────


class TestFilterByProgram:
    def test_filters_by_snap(self) -> None:
        client = httpx.Client(transport=httpx.MockTransport(lambda _: _build_response(_mock_data())))
        set_client(client)

        result = filter_by_program("97201", Program.SNAP.value)

        assert result.count == 1
        assert result.markets[0].market_name == "Test Market 1"

    def test_all_returns_all(self) -> None:
        client = httpx.Client(transport=httpx.MockTransport(lambda _: _build_response(_mock_data())))
        set_client(client)

        result = filter_by_program("97201", Program.all.value)

        assert result.count == 2

    def test_fallback_works_through_search(self) -> None:
        """filter_by_program delegates to search_by_zip, which falls back to simulated."""
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(503))
        )
        set_client(client)

        result = filter_by_program("97201", Program.SNAP.value)

        assert result.count == 5  # all simulated accept SNAP


# ── get_market_details ────────────────────────────────────────────────


class TestGetMarketDetails:
    def test_returns_details_from_api(self) -> None:
        client = httpx.Client(transport=httpx.MockTransport(lambda _: _build_response(_mock_data())))
        set_client(client)

        details = get_market_details("test-001")

        assert isinstance(details, MarketDetails)
        assert details.market_name == "Test Market 1"
        assert details.schedule == "June–Oct Sat 8am–2pm"
        assert "123 Main St" in (details.directions or "")
        assert details.contact_email == "jane@test1.org"

    def test_fallback_to_simulated_on_failure(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(500))
        )
        set_client(client)

        details = get_market_details("unknown-id")

        assert isinstance(details, MarketDetails)
        assert details.market_name == "Portland Farmers Market — PSU"

    def test_market_not_found_in_api_falls_back(self) -> None:
        """API returns empty data array -> simulated fallback."""
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: _build_response([]))
        )
        set_client(client)

        details = get_market_details("nonexistent")

        assert details.market_name == "Portland Farmers Market — PSU"


# ── search_csa ────────────────────────────────────────────────────────


class TestSearchCSA:
    def test_returns_csa_from_api(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: _build_response(_mock_csa_data()))
        )
        set_client(client)

        result = search_csa("97202")

        assert isinstance(result, CSASearchResult)
        assert result.count == 1
        assert result.csa_locations[0].operation_name == "Test CSA Farm"
        assert result.csa_locations[0].latitude == 45.50

    def test_fallback_to_simulated_on_failure(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(502))
        )
        set_client(client)

        result = search_csa("97202")

        assert result.count == 3  # 3 simulated CSAs
        assert result.csa_locations[0].operation_name == "Groundwork Farm CSA"


# ── Program enum ──────────────────────────────────────────────────────


class TestProgramEnum:
    def test_values_are_correct(self) -> None:
        assert Program.SNAP.value == "SNAP"
        assert Program.WIC.value == "WIC"
        assert Program.WICcash.value == "WICcash"
        assert Program.SFMNP.value == "SFMNP"
        assert Program.all.value == "all"