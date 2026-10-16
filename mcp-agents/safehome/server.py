"""SafeHome MCP server — property safety assessment for any US address.

Exposes MCP tools for checking natural disaster risk, active weather alerts,
and 7-day forecasts for any US residential or commercial address.

Run with stdio (local):
    python -m mcp run server.py

Run with HTTP (remote):
    uvicorn server:mcp_app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
from typing import Any

import mcp.server as mcp_server
import mcp.types as types
from mcp.server.lowlevel import Server

from src.geocoder import geocode as geocode_fn
from src.report import generate_safety_report
from src.weather import get_active_alerts, get_forecast, format_alerts, format_forecast
from src.disasters import summarize_disasters_for_county, get_state_code, get_disasters_for_state

# Create the MCP server
app = Server("safehome")

# ------------------------------------------------------------------
# Handler functions
# ------------------------------------------------------------------


def _handle_safety_report(address: str = "") -> str:
    """Generate a comprehensive property safety report."""
    if not address:
        return "Please provide a US street address (e.g. '1600 Pennsylvania Ave NW, Washington, DC')."
    try:
        return generate_safety_report(address)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error generating report: {e}"


def _handle_geocode(address: str = "") -> str:
    """Resolve a US address to coordinates."""
    if not address:
        return "Please provide a US street address."
    try:
        lat, lon, formatted = geocode_fn(address)
        return (
            f"**Address**: {formatted}\n"
            f"**Latitude**: {lat:.5f}\n"
            f"**Longitude**: {lon:.5f}\n"
            f"\n*Data from US Census Geocoder.*"
        )
    except ValueError as e:
        return str(e)


def _handle_weather_alerts(address: str = "") -> str:
    """Get active weather alerts for an address."""
    if not address:
        return "Please provide a US street address."
    try:
        lat, lon, formatted = geocode_fn(address)
        alerts = get_active_alerts(lat, lon)
        return (
            f"**Active Weather Alerts for {formatted}**\n\n"
            f"{format_alerts(alerts)}"
        )
    except ValueError as e:
        return str(e)


def _handle_forecast(address: str = "") -> str:
    """Get a 7-day weather forecast for an address."""
    if not address:
        return "Please provide a US street address."
    try:
        lat, lon, formatted = geocode_fn(address)
        forecast = get_forecast(lat, lon)
        if not forecast:
            return "Forecast unavailable for this location."
        return f"**7-Day Forecast for {formatted}**\n\n{format_forecast(forecast)}"
    except ValueError as e:
        return str(e)


def _handle_disaster_history(state: str = "", county: str = "") -> str:
    """Look up FEMA disaster declarations for a state and county."""
    if not state:
        return "Please provide a state (name or 2-letter code, e.g. 'CA' or 'California')."
    if not county:
        return "Please provide a county name (e.g. 'Los Angeles')."

    state_code = get_state_code(state)
    if not state_code:
        return f"Could not recognize state: '{state}'. Use the full name or 2-letter code."

    return summarize_disasters_for_county(state_code, county)


def _handle_state_alerts(state: str = "") -> str:
    """Get all active weather alerts for a state."""
    if not state:
        return "Please provide a state name or 2-letter code."

    state_code = get_state_code(state)
    if not state_code:
        return f"Could not recognize state: '{state}'."

    from src.weather import get_alerts_for_state as get_state_alerts
    alerts = get_state_alerts(state_code)
    return format_alerts(alerts)


# Map tool names to handler functions
_handlers: dict[str, callable] = {
    "safety_report": _handle_safety_report,
    "geocode": _handle_geocode,
    "weather_alerts": _handle_weather_alerts,
    "forecast": _handle_forecast,
    "disaster_history": _handle_disaster_history,
    "state_alerts": _handle_state_alerts,
}


def _register_tools(app: Server) -> None:
    """Register all MCP tools on the server."""

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=name,
                description=desc,
                inputSchema=INPUT_SCHEMAS.get(name, {"type": "object", "properties": {}}),
            )
            for name, desc in TOOL_DESCRIPTIONS.items()
        ]

    @app.call_tool()
    async def call_tool(
        name: str,
        arguments: dict[str, Any],
    ) -> list[types.TextContent]:
        handler = _handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = handler(**arguments)
            return [types.TextContent(type="text", text=result)]
        except Exception as exc:
            return [types.TextContent(
                type="text",
                text=f"Error: {exc}",
            )]


# Help text for each tool
TOOL_DESCRIPTIONS: dict[str, str] = {
    "safety_report": (
        "Generate a complete property safety report for any US address. "
        "Combines geocoding, FEMA disaster history, active NWS weather alerts, "
        "and a 7-day forecast. Gives you a safety overview badge, disaster "
        "history, and weather conditions in one report. "
        "Example: '1600 Pennsylvania Ave NW, Washington, DC 20500'"
    ),
    "geocode": (
        "Resolve a US street address to latitude/longitude coordinates. "
        "Uses the US Census Geocoder (free, zero-auth). "
        "Returns the normalized address and coordinates."
    ),
    "weather_alerts": (
        "Get active weather alerts (watches, warnings, advisories) for a US "
        "address. Uses the National Weather Service API. Returns event type, "
        "severity, urgency, headline, and instructions. "
        "Example: '350 5th Ave, New York, NY 10118'"
    ),
    "forecast": (
        "Get a 7-day weather forecast for any US address. Returns temperature, "
        "wind, and conditions for each day/night period."
    ),
    "disaster_history": (
        "Look up FEMA disaster declarations for a specific state and county. "
        "Returns recent disaster history including flood, hurricane, fire, "
        "earthquake, and severe storm declarations. "
        "Example: state='CA', county='Los Angeles'"
    ),
    "state_alerts": (
        "Get all active weather alerts for an entire US state. "
        "Useful for trip planning or checking statewide conditions. "
        "Example: state='Florida'"
    ),
}

# Tool input schemas
INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "safety_report": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": (
                    "Full US street address including street number, street name, "
                    "city, state, and ZIP (e.g. '1600 Pennsylvania Ave NW, Washington, DC 20500')"
                ),
            },
        },
        "required": ["address"],
    },
    "geocode": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "US street address to geocode",
            },
        },
        "required": ["address"],
    },
    "weather_alerts": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "US street address to check for weather alerts",
            },
        },
        "required": ["address"],
    },
    "forecast": {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "US street address for the forecast",
            },
        },
        "required": ["address"],
    },
    "disaster_history": {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "State name or 2-letter code (e.g. 'CA', 'Florida', 'Texas')",
            },
            "county": {
                "type": "string",
                "description": "County name (e.g. 'Los Angeles', 'Harris', 'Miami-Dade')",
            },
        },
        "required": ["state", "county"],
    },
    "state_alerts": {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "State name or 2-letter code (e.g. 'CA', 'Florida')",
            },
        },
        "required": ["state"],
    },
}

# Register tools on module load
_register_tools(app)

# Export for uvicorn / mcp CLI
mcp_app = app

# When run directly, start stdio server
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    mcp_server.run(app)