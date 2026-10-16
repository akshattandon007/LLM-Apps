"""FEMA disaster declaration data for US counties.

FEMA's open API provides a free, zero-auth feed of all federally-declared
disasters (floods, hurricanes, fires, earthquakes, etc.) by county.
"""

from __future__ import annotations

import httpx
from datetime import datetime, timezone

FEMA_API_URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"

# Cache per state code (in-process)
_declaration_cache: dict[str, list[dict]] = {}


def get_disasters_for_state(state_code: str) -> list[dict]:
    """Fetch all FEMA disaster declarations for a given state (2-letter code).

    Returns a list of disaster dicts, newest first.
    """
    cached = _declaration_cache.get(state_code)
    if cached:
        return cached

    params = {
        "$filter": f"state eq '{state_code}'",
        "$orderby": "declarationDate desc",
        "$top": 100,
        "$format": "json",
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(FEMA_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    disasters = data.get("DisasterDeclarationsSummaries") or []
    _declaration_cache[state_code] = disasters
    return disasters


def get_state_code(state_name: str) -> str | None:
    """Convert a state name or abbreviation to a 2-letter state code."""
    mapping = {
        "AL": "AL", "AK": "AK", "AZ": "AZ", "AR": "AR", "CA": "CA",
        "CO": "CO", "CT": "CT", "DE": "DE", "FL": "FL", "GA": "GA",
        "HI": "HI", "ID": "ID", "IL": "IL", "IN": "IN", "IA": "IA",
        "KS": "KS", "KY": "KY", "LA": "LA", "ME": "ME", "MD": "MD",
        "MA": "MA", "MI": "MI", "MN": "MN", "MS": "MS", "MO": "MO",
        "MT": "MT", "NE": "NE", "NV": "NV", "NH": "NH", "NJ": "NJ",
        "NM": "NM", "NY": "NY", "NC": "NC", "ND": "ND", "OH": "OH",
        "OK": "OK", "OR": "OR", "PA": "PA", "RI": "RI", "SC": "SC",
        "SD": "SD", "TN": "TN", "TX": "TX", "UT": "UT", "VT": "VT",
        "VA": "VA", "WA": "WA", "WV": "WV", "WI": "WI", "WY": "WY",
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
        "california": "CA", "colorado": "CO", "connecticut": "CT",
        "delaware": "DE", "florida": "FL", "georgia": "GA",
        "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN",
        "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
        "maine": "ME", "maryland": "MD", "massachusetts": "MA",
        "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
        "missouri": "MO", "montana": "MT", "nebraska": "NE",
        "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
        "new mexico": "NM", "new york": "NY", "north carolina": "NC",
        "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
        "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
        "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
        "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA",
        "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
        "wyoming": "WY",
        "district of columbia": "DC", "DC": "DC",
    }
    key = state_name.strip().lower()
    if len(state_name.strip()) == 2:
        key = state_name.strip().upper()
    return mapping.get(key)


def disaster_incident_type_label(code: str) -> str:
    """Map FEMA incident type codes to human-readable labels."""
    labels = {
        "DR": "Major Disaster (flood, hurricane, tornado, etc.)",
        "FM": "Fire Management Assistance",
        "EM": "Emergency Declaration",
        "FS": "Fire Suppression Assistance",
    }
    return labels.get(code, code)


def summarize_disasters_for_county(
    state_code: str, county_name: str, max_years: int = 5
) -> str:
    """Get formatted summary of disasters for a county in a state over recent years."""
    disasters = get_disasters_for_state(state_code)
    if not disasters:
        return "No FEMA disaster declarations found for this state in recent records."

    # Filter to this county (case-insensitive partial match on designatedArea)
    county_lower = county_name.lower()
    relevant = []
    for d in disasters:
        area = (d.get("designatedArea") or "").lower()
        if county_lower in area:
            relevant.append(d)

    if not relevant:
        return f"No FEMA disaster declarations found specifically for {county_name} County."

    # Trim to recent years
    cutoff_year = datetime.now(timezone.utc).year - max_years
    recent = [d for d in relevant if (d.get("fyDeclared") or 0) >= cutoff_year]

    if not recent:
        return (
            f"No disasters recorded in {county_name} County in the last {max_years} years. "
            f"(Older records exist; none within the recent window.)"
        )

    lines = [f"**FEMA Disaster History — {county_name} County (last {max_years} years)**:\n"]
    for d in recent[:15]:  # cap at 15 entries
        title = d.get("declarationTitle") or "Untitled"
        inc_type = d.get("incidentType") or "Unknown"
        decl_date = d.get("declarationDate", "")[:10] if d.get("declarationDate") else "Unknown"
        decl_type = disaster_incident_type_label(d.get("declarationType", ""))
        lines.append(
            f"- **{title}** ({inc_type}, {decl_type})\n"
            f"  Declared: {decl_date}  "
            f"  |  IA: {'Yes' if d.get('iaProgramDeclared') else 'No'}"
            f"  |  PA: {'Yes' if d.get('paProgramDeclared') else 'No'}"
        )
    lines.append(
        f"\n*Showing {min(len(recent), 15)} of {len(recent)} relevant declarations.*"
    )
    return "\n".join(lines)