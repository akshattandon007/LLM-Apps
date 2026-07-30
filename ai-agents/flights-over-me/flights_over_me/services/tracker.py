"""Tracker — orchestrates a full 'what's overhead' snapshot.

Pipeline:
  1. (optional) geocode the user's location query
  2. ask OpenSky for everything in the radius, nearest-first
  3. enrich the nearest N flights with routes + aircraft type, concurrently

We only enrich the closest handful per refresh: those are the planes a user
actually cares about, and it keeps adsbdb traffic modest.
"""

from __future__ import annotations

import asyncio
import logging
import time

from ..config import Settings
from ..models import Flight, FlightsResponse, Location
from .enrichment import EnrichmentClient
from .opensky import OpenSkyClient

logger = logging.getLogger(__name__)


class Tracker:
    def __init__(
        self,
        settings: Settings,
        opensky: OpenSkyClient,
        enrichment: EnrichmentClient,
    ) -> None:
        self._s = settings
        self._opensky = opensky
        self._enrich = enrichment

    async def _enrich_flight(self, flight: Flight) -> None:
        """Attach route + aircraft data to a single flight, in place."""
        route_task = self._enrich.route_for_callsign(flight.callsign)
        aircraft_task = self._enrich.aircraft_for_icao24(flight.icao24)
        route, (aircraft_type, registration) = await asyncio.gather(
            route_task, aircraft_task
        )
        flight.route = route
        flight.aircraft_type = aircraft_type
        flight.registration = registration

    async def snapshot(
        self,
        location: Location,
        radius_km: float,
        enrich_top: int = 25,
    ) -> FlightsResponse:
        radius_km = min(radius_km, self._s.max_radius_km)
        flights = await self._opensky.flights_near(
            location.lat, location.lon, radius_km
        )

        # Enrich the nearest flights concurrently; leave the rest as raw telemetry.
        to_enrich = flights[:enrich_top]
        if to_enrich:
            await asyncio.gather(*(self._enrich_flight(f) for f in to_enrich))

        return FlightsResponse(
            location=location,
            radius_km=radius_km,
            count=len(flights),
            generated_at=int(time.time()),
            flights=flights,
        )
