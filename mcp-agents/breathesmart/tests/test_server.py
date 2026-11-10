"""
Tests for BreatheSmart MCP Agent.
"""

import json
import sys
import os

# Add parent to path so we can import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
from server import (
    _classify,
    _build_aqi_summary,
    _fetch_air_quality,
    AQI_LEVELS,
    POLLEN_LEVELS,
    UV_LEVELS,
)


class TestClassify:
    def test_good_aqi(self):
        result = _classify(35, AQI_LEVELS)
        assert result["label"] == "Good"
        assert result["emoji"] == "🟢"
        assert result["value"] == 35

    def test_moderate_aqi(self):
        result = _classify(75, AQI_LEVELS)
        assert result["label"] == "Moderate"
        assert result["emoji"] == "🟡"

    def test_unhealthy_aqi(self):
        result = _classify(175, AQI_LEVELS)
        assert result["label"] == "Unhealthy"
        assert result["emoji"] == "🔴"

    def test_hazardous_aqi(self):
        result = _classify(350, AQI_LEVELS)
        assert result["label"] == "Hazardous"
        assert result["emoji"] == "⚫"

    def test_none_value(self):
        result = _classify(None, AQI_LEVELS)
        assert result["label"] == "N/A"
        assert result["emoji"] == "⬜"
        assert result["value"] is None

    def test_zero_value(self):
        result = _classify(0, AQI_LEVELS)
        assert result["label"] == "Good"
        assert result["emoji"] == "🟢"

    def test_boundary_moderate(self):
        result = _classify(50, AQI_LEVELS)
        assert result["label"] == "Good"

    def test_boundary_moderate(self):
        result = _classify(51, AQI_LEVELS)
        assert result["label"] == "Moderate"

    def test_pollen_low(self):
        result = _classify(10, POLLEN_LEVELS)
        assert result["label"] == "Low"

    def test_pollen_high(self):
        result = _classify(75, POLLEN_LEVELS)
        assert result["label"] == "High"

    def test_uv_extreme(self):
        result = _classify(12, UV_LEVELS)
        assert result["label"] == "Extreme"
        assert result["emoji"] == "🟣"


class TestBuildAQISummary:
    def test_good_air(self):
        summary = _build_aqi_summary(25)
        assert "Good" in summary
        assert "Great day to be active outdoors" in summary

    def test_unhealthy_air(self):
        summary = _build_aqi_summary(175)
        assert "Unhealthy" in summary
        assert "reduce prolonged outdoor exertion" in summary

    def test_none_aqi(self):
        summary = _build_aqi_summary(None)
        assert "unavailable" in summary


class TestFetchAirQuality:
    @patch("server.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "current": {"us_aqi": 42, "pm2_5": 8.5},
        }
        mock_get.return_value = mock_response

        result = _fetch_air_quality(40.7128, -74.0060, ["us_aqi", "pm2_5"])
        assert result["current"]["us_aqi"] == 42
        mock_get.assert_called_once()

    @patch("server.requests.get")
    def test_fetch_with_forecast(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "current": {"us_aqi": 42},
            "hourly": {"time": ["2026-11-10T00:00"], "us_aqi": [42]},
        }
        mock_get.return_value = mock_response

        result = _fetch_air_quality(
            40.7128, -74.0060,
            ["us_aqi"],
            hourly_params=["us_aqi"],
            forecast_days=1,
        )
        assert "hourly" in result
        mock_get.assert_called_once()


class TestMCPToolDefinitions:
    def test_tool_list_has_four_tools(self):
        """Test that the server exports exactly 4 tools."""
        import server as sv
        import asyncio

        tools = asyncio.run(sv.list_tools())
        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "get_current_air_quality" in tool_names
        assert "get_pollen_forecast" in tool_names
        assert "get_uv_index" in tool_names
        assert "get_health_summary" in tool_names

    def test_tool_schemas_have_required_params(self):
        """Verify all tool schemas define latitude and longitude as required."""
        import server as sv
        import asyncio

        tools = asyncio.run(sv.list_tools())
        for tool in tools:
            props = tool.inputSchema.get("properties", {})
            required = tool.inputSchema.get("required", [])
            assert "latitude" in required, f"{tool.name} missing latitude"
            assert "longitude" in required, f"{tool.name} missing longitude"
            assert "type" in props.get("latitude", {}), f"{tool.name} latitude missing type"


class TestErrorHandling:
    @patch("server.requests.get")
    def test_api_timeout(self, mock_get):
        """Test graceful handling of API timeout."""
        import server as sv
        import asyncio
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Timeout")

        result = asyncio.run(sv.call_tool("get_current_air_quality", {
            "latitude": 40.7128, "longitude": -74.0060
        }))
        assert "Could not reach" in result[0].text or "unexpected error" in result[0].text

    def test_unknown_tool(self):
        """Test that unknown tool names are handled gracefully."""
        import server as sv
        import asyncio

        result = asyncio.run(sv.call_tool("nonexistent_tool", {"latitude": 40.0, "longitude": -74.0}))
        # The MCP decorator catches exceptions and returns error content
        assert isinstance(result, list)
        assert len(result) > 0

    def test_missing_arguments(self):
        """Test that missing latitude raises KeyError."""
        import server as sv
        import asyncio

        with pytest.raises(KeyError):
            asyncio.run(sv.call_tool("get_current_air_quality", {}))
