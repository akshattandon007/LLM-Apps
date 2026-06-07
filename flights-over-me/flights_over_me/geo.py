"""Geospatial helpers — pure functions, fully unit-tested.

We convert a (lat, lon, radius) query into the lat/lon bounding box that
OpenSky expects, and measure great-circle distance so we can sort flights by
how close they are to directly overhead.
"""

from __future__ import annotations

import math

from .models import BoundingBox

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in kilometres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lon: float, radius_km: float) -> BoundingBox:
    """Smallest lat/lon box containing the circle of the given radius.

    Latitude degrees are ~constant length; longitude degrees shrink towards
    the poles by ``cos(latitude)``. We clamp to valid ranges and guard the
    cosine near the poles to avoid blowing up the longitude delta.
    """
    if radius_km <= 0:
        raise ValueError("radius_km must be positive")

    lat_delta = math.degrees(radius_km / EARTH_RADIUS_KM)
    cos_lat = max(math.cos(math.radians(lat)), 1e-6)
    lon_delta = math.degrees(radius_km / (EARTH_RADIUS_KM * cos_lat))

    return BoundingBox(
        lamin=max(lat - lat_delta, -90.0),
        lamax=min(lat + lat_delta, 90.0),
        lomin=max(lon - lon_delta, -180.0),
        lomax=min(lon + lon_delta, 180.0),
    )


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing (azimuth) from point 1 to point 2.

    Returns degrees in ``[0, 360)`` where 0 = due north, 90 = east. This is the
    compass direction an observer at point 1 must face to look toward point 2 —
    i.e. *which way to look in the sky* for the aircraft.
    """
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def look_angle(
    ground_km: float, altitude_m: float | None
) -> tuple[float | None, float | None]:
    """Convert ground distance + altitude into a look angle and slant range.

    Returns ``(elevation_deg, slant_range_km)``:
      * ``elevation_deg`` — angle above the horizon. 0 = on the horizon,
        90 = straight up ("directly overhead").
      * ``slant_range_km`` — true line-of-sight distance to the aircraft.

    The observer is assumed to be at sea level; over the short ranges this app
    cares about (≤ a few hundred km) the flat-earth approximation for the
    elevation angle is well within "where do I point my eyes" tolerance.
    """
    if altitude_m is None:
        return None, None
    horizontal_m = ground_km * 1000.0
    if horizontal_m == 0 and altitude_m == 0:
        return 0.0, 0.0
    elevation = math.degrees(math.atan2(altitude_m, horizontal_m))
    slant_km = math.sqrt(horizontal_m**2 + altitude_m**2) / 1000.0
    return elevation, slant_km


def compass_point(bearing_deg: float | None) -> str:
    """Turn a heading in degrees into a friendly 16-point compass label."""
    if bearing_deg is None:
        return "—"
    points = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    idx = int((bearing_deg % 360) / 22.5 + 0.5) % 16
    return points[idx]
