"""Resolve a free-text place or a "lat,lon" pair into coordinates + label.

Two paths:
  1. Fast path — "40.71,-74.01" is parsed locally, no network at all.
  2. Geocode path — any other text is geocoded through Open-Meteo; the
     most relevant result (first in the API's ordered list) is used.
"""

from __future__ import annotations

import re


class GeoLookupError(Exception):
    """Raised when a place name cannot be geocoded to any result."""


_COORDS_RE = re.compile(
    r"^\s*(?P<lat>-?\d{1,3}(?:\.\d{1,6})?)\s*,\s*"
    r"(?P<lon>-?\d{1,3}(?:\.\d{1,6})?)\s*$"
)


def parse_coords(text: str) -> tuple[float, float] | None:
    """Parse a "lat,lon" string into (lat, lon), or None if not one."""
    m = _COORDS_RE.match(text)
    if not m:
        return None
    lat, lon = float(m["lat"]), float(m["lon"])
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None
    return lat, lon


def resolve_place(
    text: str, client
) -> tuple[float, float, str]:
    """Return (lat, lon, human_label) for a place or "lat,lon" input.

    Raises GeoLookupError when a place name has no geocoding results.
    `client` is an OpenMeteoClient (injected for testability).
    """
    coords = parse_coords(text)
    if coords is not None:
        lat, lon = coords
        return lat, lon, f"{lat:.4f}, {lon:.4f}"
    results = client.geocode(text)
    if not results:
        raise GeoLookupError(text)
    best = results[0]
    label = ", ".join(
        part for part in (best.name, best.admin1, best.country) if part
    )
    return best.latitude, best.longitude, label