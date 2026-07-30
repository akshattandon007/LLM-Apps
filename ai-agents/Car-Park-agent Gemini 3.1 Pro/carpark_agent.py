"""
UK Car Park Finder Agent
========================
A Gemini 3.1 Pro-powered agentic system that finds, evaluates, and books
car parks across the UK using Google Maps + Parkopedia APIs.

Architecture:
    User Query → Gemini 3.1 Pro Agent (function-calling with thinking) → Tools:
        1. geocode_destination()        – Google Maps Geocoding
        2. search_nearby_car_parks()     – Google Maps Places (New)
        3. check_availability()          – Parkopedia Availability API
        4. get_booking_link()            – JustPark / Parkopedia deep links
    Agent synthesises results → ranked recommendations → user

Model: gemini-3.1-pro-preview-customtools
    - Google's most advanced reasoning model (Feb 2026)
    - Custom tools variant: optimised for agentic workflows with
      user-defined function declarations
    - thinking_level=MEDIUM for balanced speed/reasoning in tool-calling
    - Thought signatures handled automatically by the SDK

Requirements:
    pip install google-genai google-maps-new requests rich python-dateutil

API Keys needed (set as env vars):
    GOOGLE_MAPS_API_KEY   – Google Cloud (Maps Platform)
    GEMINI_API_KEY        – Google AI Studio / Vertex
    PARKOPEDIA_API_KEY    – Parkopedia (https://parkopedia.com/developer)
    PARKOPEDIA_API_ID     – Parkopedia application ID

Author: Akshat | 2026
"""

from __future__ import annotations

import json
import logging
import os
import sys
import math
import time
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, field, asdict
from zoneinfo import ZoneInfo

import requests
from dateutil import parser as dtparser
from google import genai
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

# ──────────────────────────────────────────────
# Config & Constants
# ──────────────────────────────────────────────

UK_TZ = ZoneInfo("Europe/London")
console = Console()
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("carpark_agent")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PARKOPEDIA_API_KEY = os.getenv("PARKOPEDIA_API_KEY", "")
PARKOPEDIA_API_ID = os.getenv("PARKOPEDIA_API_ID", "")

# Google Maps endpoints
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# Parkopedia API endpoint
PARKOPEDIA_BASE = "https://api.parkopedia.com/v3"

# JustPark search page (deep-link fallback for booking)
JUSTPARK_SEARCH = "https://www.justpark.com/search"

# Vehicle size mapping for filtering
VEHICLE_SIZES = {
    "small": {"max_height_m": 1.5, "max_length_m": 4.2, "labels": ["compact", "hatchback"]},
    "medium": {"max_height_m": 1.6, "max_length_m": 4.7, "labels": ["saloon", "sedan"]},
    "large": {"max_height_m": 1.8, "max_length_m": 5.1, "labels": ["suv", "tesla", "estate", "ev"]},
    "van": {"max_height_m": 2.5, "max_length_m": 5.9, "labels": ["van", "transit"]},
}


# ──────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────

@dataclass
class CarPark:
    """Represents a single car park result."""
    name: str
    address: str
    lat: float
    lng: float
    distance_miles: float = 0.0
    total_spaces: int = 0
    available_spaces: int | None = None
    hourly_rate_gbp: float | None = None
    has_ev_charging: bool = False
    height_restriction_m: float | None = None
    operator: str = ""
    booking_url: str = ""
    google_place_id: str = ""
    parkopedia_id: str = ""
    rating: float | None = None
    features: list[str] = field(default_factory=list)

    @property
    def suitability_score(self) -> float:
        """Weighted suitability score (0-100). Higher = better."""
        score = 50.0
        # Proximity bonus (max 25 pts – closer is better)
        if self.distance_miles <= 0.3:
            score += 25
        elif self.distance_miles <= 0.5:
            score += 20
        elif self.distance_miles <= 1.0:
            score += 10
        # Availability bonus (max 20 pts)
        if self.available_spaces is not None:
            if self.available_spaces > 50:
                score += 20
            elif self.available_spaces > 20:
                score += 15
            elif self.available_spaces > 5:
                score += 10
            elif self.available_spaces > 0:
                score += 5
        # EV charging bonus
        if self.has_ev_charging:
            score += 10
        # Size / large-vehicle friendly
        if self.total_spaces > 200:
            score += 5
        # Price bonus (max 10 pts)
        if self.hourly_rate_gbp is not None:
            if self.hourly_rate_gbp <= 2.0:
                score += 10
            elif self.hourly_rate_gbp <= 4.0:
                score += 5
        # Rating bonus
        if self.rating and self.rating >= 4.0:
            score += 5
        return min(score, 100.0)


# ──────────────────────────────────────────────
# Tool Functions (called by Gemini agent)
# ──────────────────────────────────────────────

def geocode_destination(destination: str) -> dict[str, Any]:
    """
    Geocode a UK destination string to lat/lng coordinates using
    Google Maps Geocoding API.

    Args:
        destination: Free-text location, e.g. 'Newcastle city centre'

    Returns:
        dict with keys: lat, lng, formatted_address, success
    """
    log.info(f"Geocoding: {destination}")

    # Append 'UK' to bias results to the United Kingdom
    query = f"{destination}, UK"

    try:
        resp = requests.get(
            GEOCODE_URL,
            params={
                "address": query,
                "key": GOOGLE_MAPS_API_KEY,
                "region": "uk",
                "components": "country:GB",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data["status"] != "OK" or not data.get("results"):
            return {"success": False, "error": f"Geocoding failed: {data['status']}"}

        result = data["results"][0]
        loc = result["geometry"]["location"]

        return {
            "success": True,
            "lat": loc["lat"],
            "lng": loc["lng"],
            "formatted_address": result["formatted_address"],
        }
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def calculate_route(
    origin_lat: float,
    origin_lng: float,
    destination_lat: float,
    destination_lng: float,
    departure_offset_minutes: int = 0,
    travel_mode: str = "DRIVE",
) -> dict[str, Any]:
    """
    Calculate the driving route between an origin and destination using
    the Google Maps Routes API (Compute Routes). Returns travel duration,
    distance, and estimated arrival time.

    This is critical for departure-based queries like:
      "I'm leaving Great Park in 30 mins, find parking by the time I arrive"

    The agent uses this to:
      1. Compute travel time (traffic-aware)
      2. Add departure offset (e.g. "leaving in 30 mins")
      3. Project the estimated arrival time
      4. Feed that arrival time into check_car_park_availability()

    Args:
        origin_lat:                Latitude of the starting point
        origin_lng:                Longitude of the starting point
        destination_lat:           Latitude of the destination
        destination_lng:           Longitude of the destination
        departure_offset_minutes:  Minutes until the user actually departs
                                   (e.g. 30 if "leaving in 30 mins")
        travel_mode:               DRIVE, BICYCLE, WALK, TWO_WHEELER, TRANSIT

    Returns:
        dict with keys: duration_seconds, duration_text, distance_metres,
        distance_text, departure_time, estimated_arrival_time, success
    """
    log.info(
        f"Calculating route: ({origin_lat},{origin_lng}) → "
        f"({destination_lat},{destination_lng}), "
        f"departing in {departure_offset_minutes} mins"
    )

    now = datetime.now(UK_TZ)
    departure_time = now + timedelta(minutes=departure_offset_minutes)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "routes.duration,routes.distanceMeters,"
            "routes.legs.duration,routes.legs.distanceMeters,"
            "routes.legs.startLocation,routes.legs.endLocation"
        ),
    }

    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin_lat,
                    "longitude": origin_lng,
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination_lat,
                    "longitude": destination_lng,
                }
            }
        },
        "travelMode": travel_mode,
        "routingPreference": "TRAFFIC_AWARE",
        "departureTime": departure_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "languageCode": "en-GB",
        "units": "METRIC",
    }

    try:
        resp = requests.post(ROUTES_URL, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("routes"):
            return {"success": False, "error": "No route found between the locations"}

        route = data["routes"][0]

        # Duration comes as "1234s" string
        duration_str = route.get("duration", "0s")
        duration_seconds = int(duration_str.replace("s", ""))
        distance_metres = route.get("distanceMeters", 0)

        estimated_arrival = departure_time + timedelta(seconds=duration_seconds)

        # Human-readable formatting
        hours, remainder = divmod(duration_seconds, 3600)
        minutes = remainder // 60
        if hours > 0:
            duration_text = f"{hours}h {minutes}min"
        else:
            duration_text = f"{minutes} min"

        distance_miles = round(distance_metres * 0.000621371, 1)
        distance_text = f"{distance_miles} miles ({round(distance_metres / 1000, 1)} km)"

        return {
            "success": True,
            "duration_seconds": duration_seconds,
            "duration_text": duration_text,
            "distance_metres": distance_metres,
            "distance_text": distance_text,
            "departure_time": departure_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "departure_time_human": departure_time.strftime("%I:%M %p"),
            "estimated_arrival_time": estimated_arrival.strftime("%Y-%m-%dT%H:%M:%S"),
            "estimated_arrival_time_human": estimated_arrival.strftime("%I:%M %p"),
            "travel_mode": travel_mode,
        }

    except requests.RequestException as e:
        # Fallback: estimate using straight-line distance
        log.warning(f"Routes API error: {e}, using fallback estimate")
        straight_line_miles = _haversine(
            origin_lat, origin_lng, destination_lat, destination_lng
        )
        # Rough estimate: 25 mph average city driving in UK
        estimated_minutes = int((straight_line_miles / 25) * 60) + 5  # +5 min buffer
        estimated_arrival = departure_time + timedelta(minutes=estimated_minutes)

        return {
            "success": True,
            "duration_seconds": estimated_minutes * 60,
            "duration_text": f"~{estimated_minutes} min (estimated)",
            "distance_metres": int(straight_line_miles * 1609.34),
            "distance_text": f"~{round(straight_line_miles, 1)} miles (straight-line estimate)",
            "departure_time": departure_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "departure_time_human": departure_time.strftime("%I:%M %p"),
            "estimated_arrival_time": estimated_arrival.strftime("%Y-%m-%dT%H:%M:%S"),
            "estimated_arrival_time_human": estimated_arrival.strftime("%I:%M %p"),
            "travel_mode": travel_mode,
            "is_estimate": True,
            "note": "Based on straight-line distance — actual travel may differ",
        }


def search_nearby_car_parks(
    lat: float,
    lng: float,
    radius_metres: int = 1500,
    vehicle_size: str = "large",
    require_ev_charging: bool = False,
) -> dict[str, Any]:
    """
    Search for car parks near a location using Google Maps Places API (New).

    Args:
        lat:                  Latitude of destination
        lng:                  Longitude of destination
        radius_metres:        Search radius in metres (default 1500)
        vehicle_size:         One of: small, medium, large, van
        require_ev_charging:  If True, prioritise car parks with EV chargers

    Returns:
        dict with keys: car_parks (list[dict]), count, success
    """
    log.info(f"Searching car parks near ({lat}, {lng}), radius={radius_metres}m")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.evChargeOptions,"
            "places.parkingOptions,places.currentOpeningHours,"
            "places.types"
        ),
    }

    # Google Places (New) – searchNearby request body
    body = {
        "includedTypes": ["parking"],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_metres),
            }
        },
        "maxResultCount": 10,
        "rankPreference": "DISTANCE",
        "languageCode": "en-GB",
    }

    try:
        resp = requests.post(PLACES_NEARBY_URL, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"success": False, "error": str(e), "car_parks": [], "count": 0}

    places = data.get("places", [])
    car_parks: list[dict] = []

    for p in places:
        loc = p.get("location", {})
        p_lat = loc.get("latitude", 0)
        p_lng = loc.get("longitude", 0)
        dist = _haversine(lat, lng, p_lat, p_lng)

        has_ev = bool(p.get("evChargeOptions"))

        # If EV charging is required, skip parks without it
        if require_ev_charging and not has_ev:
            continue

        features = []
        parking_opts = p.get("parkingOptions", {})
        if parking_opts.get("freeParkingLot"):
            features.append("free_parking")
        if parking_opts.get("paidParkingLot"):
            features.append("paid_parking")
        if parking_opts.get("wheelchairAccessibleParking"):
            features.append("wheelchair_accessible")
        if has_ev:
            features.append("ev_charging")

        cp = CarPark(
            name=p.get("displayName", {}).get("text", "Unknown"),
            address=p.get("formattedAddress", ""),
            lat=p_lat,
            lng=p_lng,
            distance_miles=round(dist, 2),
            has_ev_charging=has_ev,
            google_place_id=p.get("id", ""),
            rating=p.get("rating"),
            features=features,
        )
        car_parks.append(asdict(cp))

    # Sort by distance
    car_parks.sort(key=lambda x: x["distance_miles"])

    return {
        "success": True,
        "car_parks": car_parks[:10],
        "count": len(car_parks),
    }


def check_car_park_availability(
    lat: float,
    lng: float,
    arrival_datetime: str,
    duration_hours: int = 3,
) -> dict[str, Any]:
    """
    Check car park availability and pricing via Parkopedia API for
    a given location and arrival time.

    Args:
        lat:               Latitude of the area
        lng:               Longitude of the area
        arrival_datetime:  ISO-8601 datetime string, e.g. '2026-03-24T18:30:00'
        duration_hours:    Intended parking duration in hours (default 3)

    Returns:
        dict with keys: parks (list of availability info), success
    """
    log.info(f"Checking availability near ({lat},{lng}) at {arrival_datetime}")

    try:
        arrival_dt = dtparser.isoparse(arrival_datetime)
    except (ValueError, TypeError):
        arrival_dt = datetime.now(UK_TZ) + timedelta(hours=1)

    departure_dt = arrival_dt + timedelta(hours=duration_hours)

    # ── Parkopedia API v3 – Search with availability ──
    params = {
        "lat": lat,
        "lng": lng,
        "arriving": arrival_dt.strftime("%Y%m%d%H%M"),
        "leaving": departure_dt.strftime("%Y%m%d%H%M"),
        "max": 10,
        "key": PARKOPEDIA_API_KEY,
        "id": PARKOPEDIA_API_ID,
    }

    try:
        resp = requests.get(
            f"{PARKOPEDIA_BASE}/parking/search",
            params=params,
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            parks = []
            for p in data.get("result", {}).get("parkings", []):
                park_info = {
                    "parkopedia_id": p.get("id", ""),
                    "name": p.get("name", ""),
                    "address": p.get("address", ""),
                    "lat": p.get("lat", 0),
                    "lng": p.get("lng", 0),
                    "total_spaces": p.get("capacity", 0),
                    "available_spaces": p.get("availability", {}).get("free"),
                    "hourly_rate_gbp": _extract_rate(p.get("pricing")),
                    "height_restriction_m": p.get("restrictions", {}).get("maxHeight"),
                    "has_ev_charging": "ev_charging" in str(p.get("amenities", [])).lower(),
                    "operator": p.get("operator", {}).get("name", ""),
                    "booking_url": p.get("bookingUrl", ""),
                    "features": p.get("amenities", []),
                }
                parks.append(park_info)

            return {"success": True, "parks": parks, "count": len(parks)}

        else:
            log.warning(f"Parkopedia API returned {resp.status_code}, using fallback data")
            return _fallback_availability(lat, lng, arrival_dt.isoformat())

    except requests.RequestException as e:
        log.warning(f"Parkopedia API error: {e}, using fallback data")
        return _fallback_availability(lat, lng, arrival_dt.isoformat())


def get_booking_link(
    car_park_name: str,
    lat: float,
    lng: float,
    arrival_datetime: str,
    duration_hours: int = 3,
    parkopedia_id: str = "",
) -> dict[str, Any]:
    """
    Generate a booking link for a specific car park.
    Tries Parkopedia direct booking first, then falls back to
    JustPark and YourParkingSpace search links.

    Args:
        car_park_name:    Name of the car park
        lat:              Latitude
        lng:              Longitude
        arrival_datetime: ISO-8601 arrival time
        duration_hours:   Parking duration in hours
        parkopedia_id:    Parkopedia car park ID (if known)

    Returns:
        dict with booking_url, alternatives, success
    """
    log.info(f"Generating booking link for: {car_park_name}")

    try:
        arrival_dt = dtparser.isoparse(arrival_datetime)
    except (ValueError, TypeError):
        arrival_dt = datetime.now(UK_TZ) + timedelta(hours=1)

    departure_dt = arrival_dt + timedelta(hours=duration_hours)

    # ── Primary: Parkopedia deep link ──
    parkopedia_url = ""
    if parkopedia_id:
        parkopedia_url = (
            f"https://en.parkopedia.co.uk/parking/{parkopedia_id}"
            f"?arriving={arrival_dt.strftime('%Y%m%d%H%M')}"
            f"&leaving={departure_dt.strftime('%Y%m%d%H%M')}"
        )

    # ── JustPark search link ──
    justpark_url = (
        f"https://www.justpark.com/search?"
        f"q={requests.utils.quote(car_park_name)}"
        f"&lat={lat}&lng={lng}"
        f"&arriving={arrival_dt.strftime('%Y-%m-%dT%H:%M')}"
        f"&leaving={departure_dt.strftime('%Y-%m-%dT%H:%M')}"
    )

    # ── YourParkingSpace link ──
    yps_url = (
        f"https://www.yourparkingspace.co.uk/parking/search?"
        f"latitude={lat}&longitude={lng}"
        f"&start={arrival_dt.strftime('%Y-%m-%dT%H:%M')}"
        f"&end={departure_dt.strftime('%Y-%m-%dT%H:%M')}"
    )

    # ── NCP direct link (if NCP car park) ──
    ncp_url = ""
    if "ncp" in car_park_name.lower():
        slug = car_park_name.lower().replace(" ", "-").replace("ncp-", "")
        ncp_url = f"https://www.ncp.co.uk/find-a-car-park/car-parks/{slug}/"

    return {
        "success": True,
        "car_park_name": car_park_name,
        "primary_booking_url": parkopedia_url or justpark_url,
        "alternatives": {
            "justpark": justpark_url,
            "yourparkingspace": yps_url,
            "parkopedia": parkopedia_url,
            **({"ncp": ncp_url} if ncp_url else {}),
        },
    }


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _extract_rate(pricing: dict | list | None) -> float | None:
    """Extract hourly rate from Parkopedia pricing structure."""
    if not pricing:
        return None
    if isinstance(pricing, list) and pricing:
        pricing = pricing[0]
    if isinstance(pricing, dict):
        rate = pricing.get("rate") or pricing.get("hourlyRate")
        if rate is not None:
            try:
                return round(float(rate) / 100, 2)  # pence → pounds
            except (ValueError, TypeError):
                return None
    return None


def _fallback_availability(
    lat: float, lng: float, arrival_iso: str
) -> dict[str, Any]:
    """
    Fallback availability data using known NCP / council car parks
    in major UK cities. Used when Parkopedia API is unavailable.
    """
    # Known car parks in major UK centres (manually curated)
    known_parks = {
        "newcastle": [
            {
                "name": "NCP Eldon Square",
                "address": "Percy Street, Newcastle upon Tyne NE1 7JB",
                "lat": 54.9753, "lng": -1.6147,
                "total_spaces": 550, "available_spaces": 180,
                "hourly_rate_gbp": 3.80, "has_ev_charging": True,
                "operator": "NCP", "height_restriction_m": 2.1,
                "features": ["ev_charging", "cctv", "lift", "disabled_bays"],
            },
            {
                "name": "NCP Dean Street",
                "address": "Dean Street, Newcastle upon Tyne NE1 1PG",
                "lat": 54.9710, "lng": -1.6120,
                "total_spaces": 420, "available_spaces": 95,
                "hourly_rate_gbp": 4.20, "has_ev_charging": True,
                "operator": "NCP", "height_restriction_m": 2.0,
                "features": ["ev_charging", "cctv", "24_hour"],
            },
            {
                "name": "Eldon Garden Car Park",
                "address": "Eldon Garden, Newcastle upon Tyne NE1 7RA",
                "lat": 54.9760, "lng": -1.6155,
                "total_spaces": 480, "available_spaces": 145,
                "hourly_rate_gbp": 3.50, "has_ev_charging": False,
                "operator": "Eldon Garden", "height_restriction_m": 1.98,
                "features": ["cctv", "shopping_centre", "covered"],
            },
            {
                "name": "Quayside Multi-Storey",
                "address": "Broad Chare, Newcastle upon Tyne NE1 3DQ",
                "lat": 54.9690, "lng": -1.6040,
                "total_spaces": 630, "available_spaces": 280,
                "hourly_rate_gbp": 2.80, "has_ev_charging": True,
                "operator": "Newcastle City Council",
                "height_restriction_m": 2.2,
                "features": ["ev_charging", "cctv", "large_vehicle_friendly"],
            },
            {
                "name": "St James' Park Car Park",
                "address": "St James' Boulevard, Newcastle NE1 4ST",
                "lat": 54.9755, "lng": -1.6217,
                "total_spaces": 350, "available_spaces": 200,
                "hourly_rate_gbp": 3.00, "has_ev_charging": False,
                "operator": "Newcastle City Council",
                "height_restriction_m": None,
                "features": ["open_air", "large_vehicle_friendly", "match_day_restrictions"],
            },
        ],
    }

    # Find nearest city
    city_key = "newcastle"  # default
    min_dist = float("inf")
    city_coords = {
        "newcastle": (54.9783, -1.6178),
        "london": (51.5074, -0.1278),
        "manchester": (53.4808, -2.2426),
        "birmingham": (52.4862, -1.8904),
        "edinburgh": (55.9533, -3.1883),
        "leeds": (53.8008, -1.5491),
    }
    for city, (clat, clng) in city_coords.items():
        d = _haversine(lat, lng, clat, clng)
        if d < min_dist:
            min_dist = d
            city_key = city

    parks = known_parks.get(city_key, known_parks["newcastle"])

    # Enrich with distance from target
    for p in parks:
        p["distance_miles"] = round(_haversine(lat, lng, p["lat"], p["lng"]), 2)

    parks.sort(key=lambda x: x["distance_miles"])

    return {
        "success": True,
        "parks": parks,
        "count": len(parks),
        "source": "fallback_curated_data",
    }


# ──────────────────────────────────────────────
# Gemini Agent Setup
# ──────────────────────────────────────────────

# Define tools for Gemini function calling
TOOL_DECLARATIONS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="geocode_destination",
            description=(
                "Geocode any UK location to lat/lng — works for both origins "
                "and destinations. Call this for EACH location the user mentions. "
                "E.g. if user says 'leaving from Great Park to city centre', "
                "geocode BOTH 'Great Park Newcastle' AND 'Newcastle city centre'."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "destination": types.Schema(
                        type="STRING",
                        description="The location, e.g. 'Great Park Newcastle', 'Newcastle city centre', 'Manchester Arndale'"
                    ),
                },
                required=["destination"],
            ),
        ),
        types.FunctionDeclaration(
            name="calculate_route",
            description=(
                "Calculate driving route between two locations using Google Maps "
                "Routes API with real-time traffic. Returns travel duration, distance, "
                "and estimated arrival time. MUST be called when the user mentions "
                "a starting point / origin / 'leaving from' / 'departing from' — "
                "use the result's estimated_arrival_time as the arrival_datetime "
                "for check_car_park_availability."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "origin_lat": types.Schema(type="NUMBER", description="Origin latitude"),
                    "origin_lng": types.Schema(type="NUMBER", description="Origin longitude"),
                    "destination_lat": types.Schema(type="NUMBER", description="Destination latitude"),
                    "destination_lng": types.Schema(type="NUMBER", description="Destination longitude"),
                    "departure_offset_minutes": types.Schema(
                        type="INTEGER",
                        description=(
                            "Minutes from now until the user actually departs. "
                            "E.g. 30 if 'leaving in 30 mins', 0 if 'leaving now'."
                        )
                    ),
                    "travel_mode": types.Schema(
                        type="STRING",
                        description="DRIVE, BICYCLE, WALK, TWO_WHEELER, or TRANSIT (default DRIVE)"
                    ),
                },
                required=["origin_lat", "origin_lng", "destination_lat", "destination_lng"],
            ),
        ),
        types.FunctionDeclaration(
            name="search_nearby_car_parks",
            description=(
                "Search for car parks near the geocoded destination using Google Maps. "
                "Call after geocoding to find available parking locations."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "lat": types.Schema(type="NUMBER", description="Latitude"),
                    "lng": types.Schema(type="NUMBER", description="Longitude"),
                    "radius_metres": types.Schema(
                        type="INTEGER",
                        description="Search radius in metres (default 1500)"
                    ),
                    "vehicle_size": types.Schema(
                        type="STRING",
                        description="Vehicle size: small, medium, large, van"
                    ),
                    "require_ev_charging": types.Schema(
                        type="BOOLEAN",
                        description="Whether EV charging is required"
                    ),
                },
                required=["lat", "lng"],
            ),
        ),
        types.FunctionDeclaration(
            name="check_car_park_availability",
            description=(
                "Check real-time availability and pricing of car parks near a location "
                "for a specific arrival time via the Parkopedia API."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "lat": types.Schema(type="NUMBER", description="Latitude"),
                    "lng": types.Schema(type="NUMBER", description="Longitude"),
                    "arrival_datetime": types.Schema(
                        type="STRING",
                        description="ISO-8601 arrival datetime, e.g. '2026-03-24T18:30:00'"
                    ),
                    "duration_hours": types.Schema(
                        type="INTEGER",
                        description="Intended parking duration in hours"
                    ),
                },
                required=["lat", "lng", "arrival_datetime"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_booking_link",
            description=(
                "Generate booking links for a specific car park across multiple UK "
                "booking platforms (JustPark, YourParkingSpace, NCP, Parkopedia)."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "car_park_name": types.Schema(type="STRING", description="Name of the car park"),
                    "lat": types.Schema(type="NUMBER", description="Latitude"),
                    "lng": types.Schema(type="NUMBER", description="Longitude"),
                    "arrival_datetime": types.Schema(
                        type="STRING",
                        description="ISO-8601 arrival datetime"
                    ),
                    "duration_hours": types.Schema(
                        type="INTEGER",
                        description="Parking duration in hours"
                    ),
                    "parkopedia_id": types.Schema(
                        type="STRING",
                        description="Parkopedia ID if known"
                    ),
                },
                required=["car_park_name", "lat", "lng", "arrival_datetime"],
            ),
        ),
    ]
)

SYSTEM_PROMPT = """\
You are ParkMate AI — a smart UK car parking assistant. Your job is to help \
drivers find the best car park for their needs. You are friendly, concise, and \
knowledgeable about UK parking.

## Workflow — TWO MODES

### MODE A: Departure-based query
Triggered when the user mentions a starting point, e.g.:
  "I'm leaving from Great Park in 30 mins, find parking by the time I reach city centre"
  "Departing from Heathrow in 1 hour, need parking near Paddington"

Steps:
1. Parse the request to extract: ORIGIN, DESTINATION, departure offset (minutes \
   from now), vehicle type, size, EV needs, preferences.
2. Call `geocode_destination` for the ORIGIN location.
3. Call `geocode_destination` for the DESTINATION location.
4. Call `calculate_route` with both sets of coordinates + departure_offset_minutes. \
   This uses Google Maps Routes API with TRAFFIC_AWARE routing to compute real \
   travel time and estimated arrival.
5. Use the `estimated_arrival_time` from the route result as the arrival_datetime \
   for all subsequent car park queries.
6. Call `search_nearby_car_parks` near the DESTINATION.
7. Call `check_car_park_availability` with the projected arrival time.
8. Merge and rank results. Select the TOP 3.
9. For each of the top 3, call `get_booking_link`.
10. Present results. ALWAYS include: the route summary (distance, travel time, \
    departure time, estimated arrival), then the 3 car park recommendations.

### MODE B: Arrival-based / simple query
Triggered when the user gives a destination + arrival time (or no time):
  "Find parking near Newcastle city centre by 6:30pm"
  "Car park in Manchester with EV charging"

Steps:
1. Parse: destination, arrival time, vehicle type, size, EV needs, preferences.
2. Call `geocode_destination` for the destination.
3. Call `search_nearby_car_parks` with appropriate filters.
4. Call `check_car_park_availability` with the arrival time.
5. Merge and rank. Select TOP 3.
6. For each, call `get_booking_link`.
7. Present the 3 recommendations.

## Presentation Format
For each car park, present:
  - Car park name & address
  - Distance from destination
  - Available spaces (if known) / total capacity
  - Hourly rate (£)
  - EV charging availability
  - Height restrictions (⚠️ if <2.0m for large vehicles / Tesla / SUV)
  - Relevant features (24h, CCTV, covered, etc.)
  - Direct booking link

For departure-based queries, ALWAYS begin with a route summary:
  "🚗 Route: [origin] → [destination]
   📏 Distance: X miles | ⏱️ Travel time: Y min (traffic-aware)
   🕐 Departing: HH:MM | 🏁 Arriving: HH:MM
   Car parks showing availability for your HH:MM arrival:"

## Rules
- Always search within 1500m of the destination unless specified otherwise.
- For Tesla / large EVs, flag height restrictions below 2.0m as a warning.
- If EV charging is mentioned or vehicle is electric, set require_ev_charging=True.
- Default parking duration is 3 hours if not specified.
- All prices in GBP (£).
- If NO arrival time AND NO departure info is given, assume arriving 1 hour from now.
- "Leaving in X mins" → set departure_offset_minutes=X in calculate_route.
- "Leaving now" → set departure_offset_minutes=0.
- Be proactive — suggest pre-booking for peak hours (8-9am, 5-7pm, weekends).
- If the origin seems ambiguous (e.g. "Great Park"), add the city context \
  (e.g. "Great Park Newcastle") to improve geocoding accuracy.
"""

# Map function names → actual Python callables
TOOL_DISPATCH = {
    "geocode_destination": geocode_destination,
    "calculate_route": calculate_route,
    "search_nearby_car_parks": search_nearby_car_parks,
    "check_car_park_availability": check_car_park_availability,
    "get_booking_link": get_booking_link,
}


def run_agent(user_query: str) -> str:
    """
    Execute the Gemini agent loop with function calling.
    Handles multi-turn tool calls until the agent produces a final text response.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Model priority — tries each in order until one works.
    # Gemini 3.1 Pro is paid-only (zero free-tier quota).
    # Gemini 3 Flash is free-tier friendly and still excellent at tool-calling.
    # Gemini 2.5 Flash is the safe fallback available on all tiers.
    MODEL_PRIORITY = [
        "gemini-3.1-pro-preview-customtools",  # Best: paid tier only
        "gemini-3-flash-preview",               # Great: free tier, fast
        "gemini-2.5-flash",                     # Safe fallback: always available
    ]

    # Try each model until one doesn't throw a quota error
    model_id = MODEL_PRIORITY[0]
    for candidate_model in MODEL_PRIORITY:
        try:
            test_response = client.models.generate_content(
                model=candidate_model,
                contents=[types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="ping")],
                )],
                config=types.GenerateContentConfig(
                    max_output_tokens=5,
                ),
            )
            model_id = candidate_model
            console.print(f"  [dim]🤖 Using model:[/dim] [bold]{model_id}[/bold]")
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                log.warning(f"Model {candidate_model} quota exceeded, trying next...")
                continue
            else:
                model_id = candidate_model  # Non-quota error, try it anyway
                break

    # Build initial message history
    messages = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_query)],
        )
    ]

    # Gemini 3 series config notes:
    #   - thinking_level replaces thinking_budget (LOW / MEDIUM / HIGH)
    #   - MEDIUM balances cost, speed, and reasoning depth — ideal for
    #     structured tool-calling where we need reliable parameter extraction
    #   - Gemini 2.5 series uses thinking_budget instead (or omit for default)
    #   - Thought signatures are handled automatically by the SDK
    is_gemini3 = "gemini-3" in model_id
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOL_DECLARATIONS],
        **({"thinking_config": types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.MEDIUM,
        )} if is_gemini3 else {}),
    )

    max_iterations = 12  # Safety limit for agent loop
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        log.info(f"Agent iteration {iteration}")

        # Retry with backoff for transient rate limits mid-conversation
        response = None
        for retry in range(3):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=messages,
                    config=config,
                )
                break
            except Exception as e:
                if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) and retry < 2:
                    wait = (retry + 1) * 15  # 15s, 30s
                    console.print(f"  [yellow]⏳ Rate limited, retrying in {wait}s...[/yellow]")
                    time.sleep(wait)
                else:
                    raise

        if response is None:
            return "⚠️ Rate limited after retries. Wait a minute and try again."

        # Check if the model wants to call functions
        candidate = response.candidates[0]
        has_function_call = False
        function_results_parts = []

        for part in candidate.content.parts:
            if part.function_call:
                has_function_call = True
                fn_name = part.function_call.name
                fn_args = dict(part.function_call.args) if part.function_call.args else {}

                console.print(
                    f"  [dim]🔧 Calling tool:[/dim] [bold cyan]{fn_name}[/bold cyan]"
                    f"[dim]({json.dumps(fn_args, default=str)[:120]}...)[/dim]"
                )

                # Dispatch to actual function
                if fn_name in TOOL_DISPATCH:
                    result = TOOL_DISPATCH[fn_name](**fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                function_results_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response=result,
                    )
                )

        if has_function_call:
            # Add the assistant's function call message
            messages.append(candidate.content)
            # Add the function results
            messages.append(
                types.Content(
                    role="user",
                    parts=function_results_parts,
                )
            )
        else:
            # No more function calls — extract final text response
            final_text = ""
            for part in candidate.content.parts:
                if part.text:
                    final_text += part.text
            return final_text

    return "⚠️ Agent reached maximum iterations. Please try a simpler query."


# ──────────────────────────────────────────────
# CLI Interface
# ──────────────────────────────────────────────

def display_welcome():
    """Show a welcome banner."""
    console.print(
        Panel(
            "[bold green]🅿️  ParkMate AI — UK Car Park Finder Agent[/bold green]\n\n"
            "[dim]Powered by Google Gemini 3.1 Pro + Google Maps + Parkopedia[/dim]\n"
            "[dim]Find, compare, and book car parks across the UK[/dim]\n\n"
            "[yellow]Example queries:[/yellow]\n"
            '  • "Find a big car park for my Tesla near Newcastle city centre by 6:30pm"\n'
            '  • "I need parking with EV charging in Manchester Arndale for 3 hours"\n'
            '  • "Cheap parking near London Bridge arriving at 9am tomorrow"\n\n'
            '[dim]Type "quit" or "exit" to stop.[/dim]',
            border_style="green",
        )
    )


def validate_api_keys() -> bool:
    """Check that required API keys are set."""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not GOOGLE_MAPS_API_KEY:
        missing.append("GOOGLE_MAPS_API_KEY")

    if missing:
        console.print(
            Panel(
                "[bold red]Missing API Keys[/bold red]\n\n"
                + "\n".join(f"  • {k} — not set" for k in missing)
                + "\n\n[dim]Set these as environment variables before running.[/dim]\n"
                "[dim]PARKOPEDIA_API_KEY is optional (fallback data used if missing).[/dim]",
                border_style="red",
            )
        )
        return False
    return True


def main():
    """Main entry point — interactive CLI loop."""
    display_welcome()

    if not validate_api_keys():
        sys.exit(1)

    while True:
        console.print()
        user_input = console.input("[bold green]🚗 You:[/bold green] ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]👋 Goodbye! Drive safe.[/dim]")
            break

        console.print()
        with console.status("[bold cyan]ParkMate is thinking...[/bold cyan]", spinner="dots"):
            try:
                response = run_agent(user_input)
            except Exception as e:
                log.error(f"Agent error: {e}", exc_info=True)
                response = f"Sorry, something went wrong: {e}"

        console.print(Panel(Markdown(response), title="🅿️ ParkMate AI", border_style="cyan"))


if __name__ == "__main__":
    main()
