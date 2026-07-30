"""OpenSky Network client — live aircraft state vectors.

OpenSky exposes ADS-B/Mode-S positions for free. The ``/states/all`` endpoint
accepts a lat/lon bounding box and returns every tracked aircraft inside it.

Auth is optional:
  * Anonymous   -> works, but tight rate limits and 10s time resolution.
  * OAuth2 (client credentials) -> higher limits, 5s resolution.

We cache the OAuth2 access token until shortly before it expires so we don't
hammer the token endpoint.

Docs: https://openskynetwork.github.io/opensky-api/rest.html
"""

from __future__ import annotations

import logging
import time

import httpx

from ..config import Settings
from ..geo import bearing_deg, bounding_box, haversine_km, look_angle
from ..models import BoundingBox, Flight
from .airlines import resolve_airline

logger = logging.getLogger(__name__)

# Index map for an OpenSky state vector (see module docstring link).
_IDX = {
    "icao24": 0,
    "callsign": 1,
    "origin_country": 2,
    "time_position": 3,
    "last_contact": 4,
    "longitude": 5,
    "latitude": 6,
    "baro_altitude": 7,
    "on_ground": 8,
    "velocity": 9,
    "true_track": 10,
    "vertical_rate": 11,
    "geo_altitude": 13,
}


class OpenSkyError(RuntimeError):
    """Raised when OpenSky is unreachable or returns an error."""


class OpenSkyClient:
    """Thin async wrapper around the OpenSky REST API."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._s = settings
        self._http = client
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # --- auth --------------------------------------------------------------
    async def _access_token(self) -> str | None:
        """Return a cached OAuth2 token, refreshing when needed.

        Returns ``None`` when no credentials are configured (anonymous mode).
        """
        if not (self._s.opensky_client_id and self._s.opensky_client_secret):
            return None

        if self._token and time.time() < self._token_expiry - 30:
            return self._token

        logger.info("Requesting new OpenSky OAuth2 token")
        resp = await self._http.post(
            self._s.opensky_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._s.opensky_client_id,
                "client_secret": self._s.opensky_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expiry = time.time() + float(payload.get("expires_in", 1800))
        return self._token

    # --- queries -----------------------------------------------------------
    async def states_in_box(self, box: BoundingBox) -> list[Flight]:
        """Fetch raw flights within a bounding box (no enrichment, no sort)."""
        params = {
            "lamin": box.lamin,
            "lomin": box.lomin,
            "lamax": box.lamax,
            "lomax": box.lomax,
        }
        headers = {"User-Agent": self._s.user_agent}
        token = await self._access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = await self._http.get(
                f"{self._s.opensky_base_url}/states/all",
                params=params,
                headers=headers,
            )
        except httpx.HTTPError as exc:  # network-level failure
            raise OpenSkyError(f"Could not reach OpenSky: {exc}") from exc

        if resp.status_code == 429:
            raise OpenSkyError(
                "OpenSky rate limit hit. Add OAuth2 credentials in .env for "
                "higher limits, or wait a moment."
            )
        if resp.status_code >= 400:
            raise OpenSkyError(f"OpenSky returned HTTP {resp.status_code}")

        data = resp.json()
        states = data.get("states") or []
        return [self._parse_state(s) for s in states]

    async def flights_near(
        self, lat: float, lon: float, radius_km: float
    ) -> list[Flight]:
        """Flights within ``radius_km`` of the point, nearest first.

        OpenSky only filters by a rectangle, so we trim to a true circle and
        attach each aircraft's distance from the search point.
        """
        box = bounding_box(lat, lon, radius_km)
        flights = await self.states_in_box(box)

        within: list[Flight] = []
        for f in flights:
            if f.lat is None or f.lon is None:
                continue
            d = haversine_km(lat, lon, f.lat, f.lon)
            if d <= radius_km:
                f.distance_km = round(d, 1)
                f.bearing_deg = round(bearing_deg(lat, lon, f.lat, f.lon))
                altitude = f.geo_altitude_m or f.baro_altitude_m
                elevation, slant = look_angle(d, altitude)
                if elevation is not None:
                    f.elevation_deg = round(elevation, 1)
                    f.slant_range_km = round(slant, 1)
                within.append(f)

        within.sort(key=lambda f: (f.distance_km is None, f.distance_km))
        return within

    # --- parsing -----------------------------------------------------------
    @staticmethod
    def _parse_state(state: list) -> Flight:
        def at(key: str):
            idx = _IDX[key]
            return state[idx] if idx < len(state) else None

        callsign_raw = at("callsign")
        callsign = callsign_raw.strip() if isinstance(callsign_raw, str) else None
        callsign = callsign or None
        airline_icao, airline = resolve_airline(callsign)

        return Flight(
            icao24=at("icao24"),
            callsign=callsign,
            airline=airline,
            airline_icao=airline_icao,
            origin_country=at("origin_country"),
            lat=at("latitude"),
            lon=at("longitude"),
            baro_altitude_m=at("baro_altitude"),
            geo_altitude_m=at("geo_altitude"),
            velocity_ms=at("velocity"),
            true_track_deg=at("true_track"),
            vertical_rate_ms=at("vertical_rate"),
            on_ground=bool(at("on_ground")),
            last_contact=at("last_contact"),
        )
