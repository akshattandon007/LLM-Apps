"""USDA Local Food Portal API client with simulated-data fallback."""

from __future__ import annotations

from typing import Optional

import httpx

from .models import (
    CSALocation,
    CSASearchResult,
    Market,
    MarketDetails,
    MarketSearchResult,
    Program,
)

BASE_URL = "https://www.usdalocalfoodportal.com/api"

# Module-level client — swapped via set_client() for testability.
_client: Optional[httpx.Client] = None


def get_client() -> httpx.Client:
    """Return the current module-level httpx client (create if None)."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=30.0)
    return _client


def set_client(client: Optional[httpx.Client]) -> None:
    """Inject a test client (or reset to None for real calls)."""
    global _client
    _client = client


# ── public query helpers ──────────────────────────────────────────────


def search_by_zip(zip_code: str, radius_miles: int = 10) -> MarketSearchResult:
    """Search farmers markets / food hubs by ZIP + radius."""
    try:
        client = get_client()
        resp = client.get(
            f"{BASE_URL}/farmersmarket",
            params={"zip": zip_code, "radius": radius_miles},
        )
        resp.raise_for_status()
        data = resp.json()
        markets = [_parse_market(item) for item in data.get("data", [])]
        return MarketSearchResult(
            count=len(markets), zip=zip_code, radius_miles=radius_miles, markets=markets
        )
    except Exception:
        return _simulate_markets(zip_code, radius_miles)


def get_market_details(market_id: str) -> MarketDetails:
    """Fetch full details for a single market by its USDA id."""
    try:
        client = get_client()
        resp = client.get(f"{BASE_URL}/farmersmarket", params={"id": market_id})
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", [])
        if items:
            return _parse_market_details(items[0])
        raise ValueError(f"Market {market_id} not found")
    except Exception:
        return _simulate_market_details(market_id)


def search_csa(zip_code: str, radius_miles: int = 10) -> CSASearchResult:
    """Search CSA pickup locations by ZIP + radius."""
    try:
        client = get_client()
        resp = client.get(
            f"{BASE_URL}/csa",
            params={"zip": zip_code, "radius": radius_miles},
        )
        resp.raise_for_status()
        data = resp.json()
        locations = [_parse_csa(item) for item in data.get("data", [])]
        return CSASearchResult(count=len(locations), zip=zip_code, csa_locations=locations)
    except Exception:
        return _simulate_csa(zip_code, radius_miles)


def filter_by_program(zip_code: str, program: str) -> MarketSearchResult:
    """Search markets and filter by food-assistance program."""
    result = search_by_zip(zip_code)
    if program == Program.all.value:
        return result

    filtered = [m for m in result.markets if _matches_program(m, program)]
    return MarketSearchResult(
        count=len(filtered),
        zip=zip_code,
        radius_miles=result.radius_miles,
        markets=filtered,
    )


# ── internal helpers ──────────────────────────────────────────────────


def _matches_program(market: Market, program: str) -> bool:
    mapping = {
        Program.SNAP.value: "accepts_snap",
        Program.WIC.value: "accepts_wic",
        Program.WICcash.value: "accepts_wic_cash",
        Program.SFMNP.value: "accepts_sfmnp",
    }
    attr = mapping.get(program)
    return bool(getattr(market, attr, False)) if attr else False


def _parse_market(item: dict) -> Market:
    return Market(
        id=item.get("id", ""),
        market_name=item.get("marketname", ""),
        address=item.get("address"),
        city=item.get("city"),
        state=item.get("state"),
        zip_code=item.get("zip"),
        latitude=_parse_float(item.get("y")),
        longitude=_parse_float(item.get("x")),
        distance=item.get("distance"),
        accepts_snap=item.get("acceptssnap", "").upper() == "Y",
        accepts_wic=item.get("acceptswic", "").upper() == "Y",
        accepts_wic_cash=item.get("acceptswiccash", "").upper() == "Y",
        accepts_sfmnp=item.get("acceptssfmnp", "").upper() == "Y",
        organic=item.get("organic", "").upper() == "Y",
        products=item.get("products"),
        season_dates=item.get("season1date"),
        season_hours=item.get("season1time"),
        website=item.get("website"),
        facebook=item.get("facebook"),
        twitter=item.get("twitter"),
        youtube=item.get("youtube"),
        contact_name=item.get("contact"),
        contact_email=item.get("email"),
        contact_phone=item.get("phone"),
    )


def _parse_market_details(item: dict) -> MarketDetails:
    base = _parse_market(item)
    return MarketDetails(
        **base.model_dump(),
        schedule=f"{item.get('season1date', '')} {item.get('season1time', '')}".strip(),
        directions=f"{base.address}, {base.city}, {base.state} {base.zip_code}",
        market_link=item.get("market_link", ""),
    )


def _parse_csa(item: dict) -> CSALocation:
    return CSALocation(
        id=item.get("id", ""),
        operation_name=item.get("operationname", ""),
        address=item.get("address"),
        city=item.get("city"),
        state=item.get("state"),
        zip_code=item.get("zip"),
        distance=item.get("distance"),
        latitude=_parse_float(item.get("y")),
        longitude=_parse_float(item.get("x")),
        website=item.get("website"),
        contact_name=item.get("contact"),
        contact_phone=item.get("phone"),
        contact_email=item.get("email"),
    )


def _parse_float(val: object) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ── simulated data (Portland, OR scene) ───────────────────────────────


SIMULATED_MARKETS = [
    {
        "id": "sim-pdx-001",
        "marketname": "Portland Farmers Market — PSU",
        "address": "SW Park Ave & Montgomery St",
        "city": "Portland",
        "state": "OR",
        "zip": "97201",
        "x": -122.6819,
        "y": 45.5122,
        "distance": "0.5 mi",
        "acceptssnap": "Y",
        "acceptswic": "Y",
        "acceptswiccash": "Y",
        "acceptssfmnp": "N",
        "organic": "Y",
        "products": "Vegetables, fruits, meat, eggs, bread, honey, flowers",
        "season1date": "March – December",
        "season1time": "Saturdays 8am–2pm",
        "website": "https://www.portlandfarmersmarket.org",
    },
    {
        "id": "sim-pdx-002",
        "marketname": "King Farmers Market",
        "address": "NE 1st Ave & Fremont St",
        "city": "Portland",
        "state": "OR",
        "zip": "97212",
        "x": -122.6635,
        "y": 45.5405,
        "distance": "1.2 mi",
        "acceptssnap": "Y",
        "acceptswic": "N",
        "acceptswiccash": "N",
        "acceptssfmnp": "Y",
        "organic": "Y",
        "products": "Vegetables, fruits, herbs, prepared food, crafts",
        "season1date": "May – October",
        "season1time": "Sundays 10am–2pm",
        "website": "https://kingfarmersmarket.org",
    },
    {
        "id": "sim-pdx-003",
        "marketname": "People's Food Co-op Farm Stand",
        "address": "3029 SE 21st Ave",
        "city": "Portland",
        "state": "OR",
        "zip": "97202",
        "x": -122.6436,
        "y": 45.4992,
        "distance": "2.0 mi",
        "acceptssnap": "Y",
        "acceptswic": "N",
        "acceptswiccash": "N",
        "acceptssfmnp": "N",
        "organic": "Y",
        "products": "Vegetables, fruits, bulk dry goods, dairy",
        "season1date": "Year-round",
        "season1time": "Daily 8am–9pm",
        "website": "https://peoples.coop",
    },
    {
        "id": "sim-pdx-004",
        "marketname": "Hillsdale Farmers Market",
        "address": "SW Sunset Blvd & Capitol Hwy",
        "city": "Portland",
        "state": "OR",
        "zip": "97239",
        "x": -122.7005,
        "y": 45.4598,
        "distance": "3.5 mi",
        "acceptssnap": "Y",
        "acceptswic": "Y",
        "acceptswiccash": "N",
        "acceptssfmnp": "N",
        "organic": "Y",
        "products": "Vegetables, fruit, meat, eggs, cheese, bread, pastries",
        "season1date": "February – November",
        "season1time": "Sundays 9am–1:30pm",
        "website": "https://hillsdalefarmersmarket.com",
    },
    {
        "id": "sim-pdx-005",
        "marketname": "Beaverton Farmers Market",
        "address": "SW 3rd St & Hall Blvd",
        "city": "Beaverton",
        "state": "OR",
        "zip": "97005",
        "x": -122.8079,
        "y": 45.4853,
        "distance": "5.8 mi",
        "acceptssnap": "Y",
        "acceptswic": "Y",
        "acceptswiccash": "Y",
        "acceptssfmnp": "Y",
        "organic": "Y",
        "products": "Vegetables, fruit, meat, eggs, seafood, baked goods, flowers",
        "season1date": "March – November",
        "season1time": "Saturdays 8am–1:30pm",
        "website": "https://beavertonfarmersmarket.com",
    },
]

SIMULATED_CSA = [
    {
        "id": "sim-csa-001",
        "operationname": "Groundwork Farm CSA",
        "address": "12015 SE 82nd Ave",
        "city": "Portland",
        "state": "OR",
        "zip": "97266",
        "distance": "4.2 mi",
        "y": 45.4823,
        "x": -122.5809,
        "website": "https://groundworkfarm.com",
        "contact": "Sara Smith",
        "phone": "503-555-0101",
        "email": "csa@groundworkfarm.com",
    },
    {
        "id": "sim-csa-002",
        "operationname": "Deep Roots Farm CSA Pickup",
        "address": "2901 SE Oak St",
        "city": "Portland",
        "state": "OR",
        "zip": "97214",
        "distance": "1.8 mi",
        "y": 45.5199,
        "x": -122.6365,
        "website": "https://deeprootsfarmpdx.com",
        "contact": "Jake Torres",
        "phone": "503-555-0102",
    },
    {
        "id": "sim-csa-003",
        "operationname": "Full Circle Farm CSA",
        "address": "16200 SW Pacific Hwy",
        "city": "Tigard",
        "state": "OR",
        "zip": "97224",
        "distance": "7.5 mi",
        "y": 45.4047,
        "x": -122.7872,
        "website": "https://fullcirclefarm.com",
        "contact": "Mia Chen",
        "phone": "503-555-0103",
        "email": "info@fullcirclefarm.com",
    },
]


def _simulate_markets(zip_code: str, radius_miles: int) -> MarketSearchResult:
    """Return Portland-area mock data when the real API is unreachable."""
    markets = [_parse_market(m) for m in SIMULATED_MARKETS]
    return MarketSearchResult(
        count=len(markets), zip=zip_code, radius_miles=radius_miles, markets=markets
    )


def _simulate_market_details(market_id: str) -> MarketDetails:
    """Return mock details for any sim-* market id, or the first one."""
    matches = [m for m in SIMULATED_MARKETS if m["id"] == market_id]
    if matches:
        return _parse_market_details(matches[0])
    return _parse_market_details(SIMULATED_MARKETS[0])


def _simulate_csa(zip_code: str, radius_miles: int) -> CSASearchResult:
    """Return Portland-area mock CSA data."""
    locations = [_parse_csa(c) for c in SIMULATED_CSA]
    return CSASearchResult(count=len(locations), zip=zip_code, csa_locations=locations)