"""
fuel-tracker — MCP server for fuel/gas price data.

Provides tools to look up national average fuel prices per country
and station-level prices near a location, via the free FuelWide API
(no API key required).

Usage:
    python server.py              # runs stdio MCP server
    python server.py --country DE # quick CLI test for country prices
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any

import httpx

from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FUELWIDE_BASE = "https://fuelwide.com"
TIMEOUT_S = 15.0
USER_AGENT = "fuel-tracker-mcp/1.0"

# ---------------------------------------------------------------------------
# API client (stateless, thin wrapper)
# ---------------------------------------------------------------------------


@dataclass
class FuelWideClient:
    """Thread‑safe HTTP client for the FuelWide public API."""

    _client: httpx.Client = field(default_factory=lambda: httpx.Client(
        base_url=FUELWIDE_BASE,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_S,
    ))

    # ------------------------------------------------------------------
    # National averages
    # ------------------------------------------------------------------

    def get_all_prices(self) -> list[dict[str, Any]]:
        """Return national‑average fuel prices for every available country."""
        resp = self._client.get("/api/fuel-prices")
        resp.raise_for_status()
        data = resp.json()
        # The API returns an object keyed by country code; normalise to a list
        if isinstance(data, dict):
            return [{"country": k, **v} for k, v in data.items()]
        return data  # already a list

    def get_country_prices(self, country_code: str) -> dict[str, Any]:
        """Return fuel prices for a single ISO‑3166‑1 alpha‑2 country code."""
        resp = self._client.get(f"/api/fuel-prices/{country_code}")
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Station‑level
    # ------------------------------------------------------------------

    def get_stations(
        self,
        country: str,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: int = 25,
        fuel_type: str | None = None,
        sort: str | None = "price",
    ) -> list[dict[str, Any]]:
        """Return per‑station prices, optionally filtered by location."""
        params: dict[str, Any] = {}
        if lat is not None and lon is not None:
            params["near"] = f"{lat},{lon}"
            params["km"] = str(radius_km)
        if fuel_type:
            params["fuel"] = fuel_type
        if sort:
            params["sort"] = sort
        resp = self._client.get(
            f"/api/stations/{country}", params=params
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()


# ---------------------------------------------------------------------------
# MCP Server definition
# ---------------------------------------------------------------------------

server = MCPServer(
    name="fuel-tracker",
    version="1.0.0",
    description="Look up fuel/gas prices by country and nearby stations via FuelWide.",
    instructions=(
        "Tools for checking fuel prices.  Use `get_fuel_prices` for a global "
        "overview, `get_country_fuel_prices` for a specific country's averages, "
        "and `get_nearby_stations` to find cheap stations near a location."
    ),
)

_client: FuelWideClient | None = None


def _get_client() -> FuelWideClient:
    global _client
    if _client is None:
        _client = FuelWideClient()
    return _client


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool(
    name="get_fuel_prices",
    description="Get national average fuel prices (petrol 95, diesel, LPG) for ALL available countries.",
)
def get_fuel_prices() -> str:
    """Return a formatted summary of national average fuel prices."""
    client = _get_client()
    prices = client.get_all_prices()
    if not prices:
        return "No fuel price data available at this time."

    lines = ["# National Average Fuel Prices (EUR per litre)\n"]
    for entry in prices:
        country = entry.get("country", "??")
        observations = entry.get("observations", entry.get("prices", {}))
        if isinstance(observations, dict):
            fuels = []
            for fuel_name, obs in observations.items():
                if isinstance(obs, dict):
                    val = obs.get("value", "?")
                    fuels.append(f"{fuel_name}: {val}€")
                else:
                    fuels.append(f"{fuel_name}: {obs}")
            price_str = " · ".join(fuels) if fuels else "no data"
        else:
            price_str = str(observations)
        lines.append(f"- **{country.upper()}**: {price_str}")

    return "\n".join(lines)


@server.tool(
    name="get_country_fuel_prices",
    description="Get detailed fuel price data for a specific country by ISO‑3166‑1 alpha‑2 code (e.g. DE, FR, US, GB, IT, ES).",
)
def get_country_fuel_prices(country_code: str) -> str:
    """
    Return fuel prices for one country.

    Parameters
    ----------
    country_code : str
        Two‑letter ISO‑3166‑1 alpha‑2 country code (e.g. "DE", "US", "GB").
    """
    client = _get_client()
    try:
        data = client.get_country_prices(country_code.strip().upper())
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 451:
            return (
                f"**{country_code.upper()}** — 451 Unavailable For Legal Reasons. "
                "The data publisher for this market does not allow redistribution "
                "through third‑party APIs. Check FuelWide directly for details."
            )
        return f"Error fetching data for {country_code}: {exc}"

    return json.dumps(data, indent=2, default=str)


@server.tool(
    name="get_nearby_stations",
    description="Find fuel stations near a location with prices. Supports IT, ES, FR, AU (Western Australia only).",
)
def get_nearby_stations(
    country: str,
    lat: float,
    lon: float,
    radius_km: int = 25,
    fuel_type: str | None = None,
) -> str:
    """
    Return station‑level fuel prices near a geographic coordinate.

    Parameters
    ----------
    country : str
        Two‑letter ISO‑3166‑1 alpha‑2 code (IT, ES, FR, AU).
    lat : float
        Latitude in decimal degrees.
    lon : float
        Longitude in decimal degrees.
    radius_km : int
        Search radius in kilometres (default 25).
    fuel_type : str | None
        Optional fuel grade filter (e.g. "euro95", "diesel").
    """
    client = _get_client()
    try:
        stations = client.get_stations(
            country=country.strip().upper(),
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            fuel_type=fuel_type,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 451:
            return (
                f"Station data for **{country.upper()}** is not available "
                "for redistribution via API. Check FuelWide directly."
            )
        return f"Error fetching stations: {exc}"

    if not stations:
        return f"No stations found near ({lat}, {lon}) within {radius_km} km."

    lines = [f"# Fuel Stations near ({lat}, {lon}) within {radius_km} km\n"]
    for s in stations[:50]:  # cap display
        brand = s.get("brand", "Unknown")
        address = s.get("address", "")
        dist = s.get("distance_km", "")
        prices = s.get("prices", {})
        price_str = " | ".join(
            f"{k}: {v}€" for k, v in prices.items()
        ) if isinstance(prices, dict) else str(prices)
        lines.append(
            f"- **{brand}** ({address})"
            + (f" [{dist} km]" if dist else "")
            + f"\n  {price_str}"
        )

    if len(stations) > 50:
        lines.append(f"\n*…and {len(stations) - 50} more stations.*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run as stdio MCP server, or as a quick CLI demo with --country."""
    if len(sys.argv) > 1 and sys.argv[1] == "--country" and len(sys.argv) > 2:
        # CLI quick‑test mode
        result = get_country_fuel_prices(sys.argv[2])
        print(result)
        return

    # Normal MCP server mode over stdio
    server.run(transport="stdio")


if __name__ == "__main__":
    main()