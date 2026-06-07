"""Enrichment via adsbdb.com — free callsign/aircraft metadata.

OpenSky tells us *where* a plane is; adsbdb tells us *what it is and where it's
going*:

  * ``/callsign/{callsign}`` -> origin + destination airports.
  * ``/aircraft/{icao24}``   -> type, manufacturer, registration, owner.

These facts are stable for the life of a flight, so we cache them in-process
with a TTL to keep request volume polite and the UI snappy.
"""

from __future__ import annotations

import logging
import time

import httpx

from ..config import Settings
from ..models import Route

logger = logging.getLogger(__name__)


class _TTLCache:
    """Minimal TTL cache. Good enough; swap for Redis if you go multi-process."""

    def __init__(self, ttl_s: float) -> None:
        self._ttl = ttl_s
        self._store: dict[str, tuple[float, object]] = {}

    def get(self, key: str):
        item = self._store.get(key)
        if item is None:
            return None
        expires, value = item
        if time.time() > expires:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: object) -> None:
        self._store[key] = (time.time() + self._ttl, value)


class EnrichmentClient:
    """Best-effort metadata lookups. Never raises — missing data is fine."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._s = settings
        self._http = client
        # Routes/aircraft are stable; 1h cache is plenty and very kind to adsbdb.
        self._route_cache = _TTLCache(ttl_s=3600)
        self._aircraft_cache = _TTLCache(ttl_s=86400)

    async def _get_json(self, url: str) -> dict | None:
        try:
            resp = await self._http.get(
                url, headers={"User-Agent": self._s.user_agent}
            )
        except httpx.HTTPError as exc:
            logger.debug("adsbdb request failed: %s", exc)
            return None
        if resp.status_code != 200:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

    async def route_for_callsign(self, callsign: str | None) -> Route | None:
        if not callsign:
            return None
        cached = self._route_cache.get(callsign)
        if cached is not None:
            return cached or None  # cached "" sentinel means "looked up, nothing"

        data = await self._get_json(
            f"{self._s.adsbdb_base_url}/callsign/{callsign}"
        )
        route = None
        flightroute = (data or {}).get("response", {}).get("flightroute")
        if isinstance(flightroute, dict):
            origin = flightroute.get("origin") or {}
            dest = flightroute.get("destination") or {}
            route = Route(
                origin_iata=origin.get("iata_code"),
                origin_name=origin.get("name"),
                origin_country=origin.get("country_name"),
                destination_iata=dest.get("iata_code"),
                destination_name=dest.get("name"),
                destination_country=dest.get("country_name"),
            )
        self._route_cache.set(callsign, route or "")
        return route

    async def aircraft_for_icao24(
        self, icao24: str | None
    ) -> tuple[str | None, str | None]:
        """Return ``(aircraft_type, registration)`` for a transponder address."""
        if not icao24:
            return None, None
        cached = self._aircraft_cache.get(icao24)
        if cached is not None:
            return cached  # type: ignore[return-value]

        data = await self._get_json(
            f"{self._s.adsbdb_base_url}/aircraft/{icao24}"
        )
        aircraft = (data or {}).get("response", {}).get("aircraft")
        result: tuple[str | None, str | None] = (None, None)
        if isinstance(aircraft, dict):
            manufacturer = aircraft.get("manufacturer") or ""
            type_name = aircraft.get("type") or ""
            full_type = f"{manufacturer} {type_name}".strip() or None
            result = (full_type, aircraft.get("registration"))
        self._aircraft_cache.set(icao24, result)
        return result
