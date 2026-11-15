"""Utility functions for MoveMate — API helpers for free, keyless web APIs."""

import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Optional

USER_AGENT = "MoveMate/1.0 (Relocation Assistant; +https://github.com/akshattandon007/LLM-Apps)"


def _fetch_json(url: str, timeout: int = 10) -> Optional[dict]:
    """Fetch a URL and parse JSON response. Returns None on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            OSError, TimeoutError) as e:
        return None


def _fetch_text(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch a URL and return raw text. Returns None on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
        return None


# ──────────────────────────── OpenStreetMap / Nominatim ────────────────────────

def nominatim_geocode(query: str) -> Optional[dict]:
    """Geocode a location via Nominatim. Returns {lat, lon, display_name, type}."""
    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q={urllib.parse.quote(query)}&format=json&limit=1&addressdetails=1"
    )
    data = _fetch_json(url)
    if data and len(data) > 0:
        r = data[0]
        return {
            "lat": r.get("lat"),
            "lon": r.get("lon"),
            "display_name": r.get("display_name", query),
            "type": r.get("type", ""),
            "address": r.get("address", {}),
        }
    return None


def nominatim_reverse(lat: float, lon: float) -> Optional[dict]:
    """Reverse geocode coordinates."""
    url = (
        f"https://nominatim.openstreetmap.org/reverse?"
        f"lat={lat}&lon={lon}&format=json&addressdetails=1"
    )
    return _fetch_json(url)


def osm_nearby_amenities(lat: float, lon: float, radius: int = 1000) -> list[str]:
    """Find nearby amenities (parks, transit stops, supermarkets) via Overpass API."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
      node["public_transport"="stop_position"](around:{radius},{lat},{lon});
      node["leisure"="park"](around:{radius},{lat},{lon});
    );
    out body;
    """
    data = {"data": query}
    req = urllib.request.Request(
        overpass_url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            amenities = []
            seen = set()
            for element in result.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name", "")
                amenity_type = tags.get("amenity", tags.get("shop", tags.get("leisure", tags.get("public_transport", ""))))
                label = f"{name} ({amenity_type})" if name else f"Unnamed {amenity_type}"
                if label not in seen:
                    amenities.append(label)
                    seen.add(label)
            return amenities[:15]
    except Exception:
        return []


# ──────────────────────────── Open-Meteo Weather ───────────────────────────────

def openmeteo_forecast(lat: float, lon: float) -> Optional[dict]:
    """Get 7-day weather forecast for location. No API key needed."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
        f"&timezone=auto&forecast_days=7"
    )
    return _fetch_json(url)


def openmeteo_geocode(city: str) -> Optional[tuple[float, float]]:
    """Geocode a city name via Open-Meteo's free API."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
    data = _fetch_json(url)
    if data and data.get("results"):
        r = data["results"][0]
        return (r["latitude"], r["longitude"])
    return None


# ──────────────────────────── Wikipedia ───────────────────────────────────────

def wikipedia_summary(query: str, sentences: int = 3) -> Optional[str]:
    """Get a summary paragraph from Wikipedia."""
    url = (
        f"https://en.wikipedia.org/api/rest_v1/page/summary/"
        f"{urllib.parse.quote(query.replace(' ', '_'))}"
    )
    data = _fetch_json(url)
    if data and "extract" in data:
        return data["extract"]
    return None


def wikipedia_search(query: str, limit: int = 5) -> list[str]:
    """Search Wikipedia for pages matching query."""
    url = (
        f"https://en.wikipedia.org/w/api.php?"
        f"action=query&list=search&srsearch={urllib.parse.quote(query)}"
        f"&format=json&srlimit={limit}"
    )
    data = _fetch_json(url)
    if data and "query" in data and "search" in data["query"]:
        return [r["title"] for r in data["query"]["search"]]
    return []


# ──────────────────────────── FEMA Disaster API ──────────────────────────────

def fema_disasters(state: str) -> list[str]:
    """Get recent disaster declarations for a state (free, no key)."""
    url = f"https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=state eq '{state}'&$orderby=declarationDate desc&$top=5"
    data = _fetch_json(url)
    if data and data.get("DisasterDeclarationsSummaries"):
        return [
            f"{d.get('incidentType', 'Unknown')} - {d.get('declarationDate', '')[:10]}"
            for d in data["DisasterDeclarationsSummaries"]
        ]
    return []