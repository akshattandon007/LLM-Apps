"""
Tests for fuel-tracker MCP server tools.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# Patch httpx before importing server so the client doesn't make real HTTP calls
from fuel_tracker.server import (
    FUELWIDE_BASE,
    FuelWideClient,
    get_country_fuel_prices,
    get_fuel_prices,
    get_nearby_stations,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a MagicMock that replaces FuelWideClient."""
    with patch("fuel_tracker.server.FuelWideClient") as mock:
        instance = mock.return_value
        # Simulate get_all_prices
        instance.get_all_prices.return_value = [
            {
                "country": "DE",
                "observations": {
                    "petrol_95": {"value": 1.74, "currency": "EUR", "unit": "litre"},
                    "diesel": {"value": 1.62, "currency": "EUR", "unit": "litre"},
                },
            },
            {
                "country": "FR",
                "observations": {
                    "petrol_95": {"value": 1.81, "currency": "EUR", "unit": "litre"},
                    "diesel": {"value": 1.68, "currency": "EUR", "unit": "litre"},
                },
            },
        ]
        # Simulate get_country_prices
        instance.get_country_prices.return_value = {
            "country": "DE",
            "observations": {
                "petrol_95": {"value": 1.74, "currency": "EUR", "unit": "litre"},
                "diesel": {"value": 1.62, "currency": "EUR", "unit": "litre"},
            },
        }
        # Simulate get_stations
        instance.get_stations.return_value = [
            {
                "brand": "Shell",
                "address": "Musterstr. 1, Berlin",
                "distance_km": 1.2,
                "prices": {"euro95": 1.72, "diesel": 1.59},
            },
            {
                "brand": "Aral",
                "address": "Hauptstr. 50, Berlin",
                "distance_km": 2.5,
                "prices": {"euro95": 1.69, "diesel": 1.55},
            },
        ]
        yield instance


# ---------------------------------------------------------------------------
# FuelWideClient unit tests
# ---------------------------------------------------------------------------


class TestFuelWideClient:
    """Test the HTTP client wrapper directly."""

    def test_get_all_prices_happy_path(self) -> None:
        """get_all_prices should parse the dict response into a list."""
        client = FuelWideClient()
        # Stub the underlying httpx call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "DE": {"observations": {"petrol_95": {"value": 1.74}}},
            "FR": {"observations": {"petrol_95": {"value": 1.81}}},
        }
        client._client = MagicMock()
        client._client.get.return_value = mock_response

        result = client.get_all_prices()
        assert len(result) == 2
        assert result[0]["country"] == "DE"
        client._client.get.assert_called_once_with("/api/fuel-prices")

    def test_get_country_prices(self) -> None:
        """get_country_prices should call the correct endpoint."""
        client = FuelWideClient()
        mock_response = MagicMock()
        mock_response.json.return_value = {"country": "GB"}
        client._client = MagicMock()
        client._client.get.return_value = mock_response

        result = client.get_country_prices("GB")
        assert result["country"] == "GB"
        client._client.get.assert_called_once_with("/api/fuel-prices/GB")


# ---------------------------------------------------------------------------
# MCP tool tests (via mock)
# ---------------------------------------------------------------------------


class TestMCPTools:
    """Test the MCP tool functions (which use a global client)."""

    def test_get_fuel_prices_returns_formatted_output(self, mock_client: MagicMock) -> None:
        """get_fuel_prices should return a markdown table of prices."""
        result = get_fuel_prices()
        assert "DE" in result
        assert "FR" in result
        assert "1.74" in result
        assert "petrol_95" in result
        assert result.startswith("# National Average")

    def test_get_fuel_prices_empty(self, mock_client: MagicMock) -> None:
        """get_fuel_prices should handle empty data."""
        instance = FuelWideClient()
        instance._client = MagicMock()
        instance._client.get.return_value.json.return_value = []
        with patch("fuel_tracker.server._get_client", return_value=instance):
            result = get_fuel_prices()
        assert "No fuel price data" in result

    def test_get_country_fuel_prices(self, mock_client: MagicMock) -> None:
        """get_country_fuel_prices should return JSON for the country."""
        result = get_country_fuel_prices("DE")
        data = json.loads(result)
        assert data["country"] == "DE"
        assert data["observations"]["petrol_95"]["value"] == 1.74

    def test_get_nearby_stations(self, mock_client: MagicMock) -> None:
        """get_nearby_stations should return formatted station list."""
        result = get_nearby_stations("DE", 52.52, 13.405, 25)
        assert "Shell" in result
        assert "Aral" in result
        assert "1.72" in result

    def test_get_nearby_stations_empty(self, mock_client: MagicMock) -> None:
        """get_nearby_stations should handle no stations found."""
        instance = FuelWideClient()
        instance._client = MagicMock()
        instance._client.get.return_value.json.return_value = []
        with patch("fuel_tracker.server._get_client", return_value=instance):
            result = get_nearby_stations("DE", 0.0, 0.0)
        assert "No stations found" in result