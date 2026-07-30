"""Geocoding via OpenStreetMap Nominatim.

Accepts either raw coordinates (``"51.5,-0.12"``) or a free-text place name
(``"Edinburgh"``). Coordinates skip the network entirely.

Nominatim's usage policy: max 1 req/s and a real User-Agent. We send one
request per *search*, not per refresh, so we stay well within bounds.
"""

from __future__ import annotations

import logging
import re

import httpx

from ..config import Settings
from ..models import Location

logger = logging.getLogger(__name__)

_COORD_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*$"
)


class GeocodeError(RuntimeError):
    pass


class Geocoder:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._s = settings
        self._http = client

    @staticmethod
    def _parse_coords(text: str) -> Location | None:
        match = _COORD_RE.match(text)
        if not match:
            return None
        lat, lon = float(match.group(1)), float(match.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return Location(name=f"{lat:.4f}, {lon:.4f}", lat=lat, lon=lon)

    async def resolve(self, query: str) -> Location:
        """Resolve a query to a single best-match Location."""
        query = (query or "").strip()
        if not query:
            raise GeocodeError("Empty location query")

        coords = self._parse_coords(query)
        if coords:
            return coords

        try:
            resp = await self._http.get(
                f"{self._s.nominatim_base_url}/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": self._s.user_agent},
            )
            resp.raise_for_status()
            results = resp.json()
        except httpx.HTTPError as exc:
            raise GeocodeError(f"Geocoding service unavailable: {exc}") from exc

        if not results:
            raise GeocodeError(f"Could not find a location for '{query}'")

        top = results[0]
        return Location(
            name=top.get("display_name", query),
            lat=float(top["lat"]),
            lon=float(top["lon"]),
        )
