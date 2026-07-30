"""Pydantic models — the shapes that flow between services, API and UI."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Location(BaseModel):
    """A resolved point on Earth."""

    name: str = Field(..., description="Human-readable label, e.g. 'London, UK'")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class BoundingBox(BaseModel):
    """Lat/lon envelope used to query OpenSky."""

    lamin: float
    lomin: float
    lamax: float
    lomax: float


class Route(BaseModel):
    """Origin/destination for a callsign (best-effort, from adsbdb)."""

    origin_iata: str | None = None
    origin_name: str | None = None
    origin_country: str | None = None
    destination_iata: str | None = None
    destination_name: str | None = None
    destination_country: str | None = None


class Flight(BaseModel):
    """A single aircraft overhead, enriched as far as free data allows."""

    icao24: str = Field(..., description="Unique 24-bit ICAO transponder address")
    callsign: str | None = Field(None, description="e.g. 'BAW123'")
    airline: str | None = Field(None, description="Resolved airline name")
    airline_icao: str | None = Field(None, description="3-letter ICAO airline code")

    origin_country: str | None = None  # transponder registration country
    route: Route | None = None
    aircraft_type: str | None = None  # e.g. 'Boeing 777-300ER'
    registration: str | None = None  # tail number, e.g. 'G-STBA'

    # Live telemetry --------------------------------------------------------
    lat: float | None = None
    lon: float | None = None
    baro_altitude_m: float | None = Field(None, description="Barometric altitude, m")
    geo_altitude_m: float | None = Field(None, description="Geometric altitude, m")
    velocity_ms: float | None = Field(None, description="Ground speed, m/s")
    true_track_deg: float | None = Field(None, description="Heading 0=N, clockwise")
    vertical_rate_ms: float | None = Field(None, description="Climb(+)/descend(-) m/s")
    on_ground: bool = False
    distance_km: float | None = Field(
        None, description="Ground distance from the search point"
    )
    bearing_deg: float | None = Field(
        None, description="Compass direction from observer to the aircraft"
    )
    elevation_deg: float | None = Field(
        None, description="Angle above the horizon; 90 = directly overhead"
    )
    slant_range_km: float | None = Field(
        None, description="True line-of-sight distance from observer"
    )
    last_contact: int | None = Field(None, description="Unix time of last position")

    # Convenience, computed for the UI -------------------------------------
    @property
    def altitude_ft(self) -> int | None:
        alt = self.geo_altitude_m or self.baro_altitude_m
        return round(alt * 3.28084) if alt is not None else None

    @property
    def speed_kts(self) -> int | None:
        if self.velocity_ms is None:
            return None
        return round(self.velocity_ms * 1.94384)

    @property
    def is_overhead(self) -> bool:
        """True when the aircraft is high in the sky almost directly above."""
        if self.elevation_deg is not None:
            return self.elevation_deg >= 75.0
        # Fall back to ground distance if we have no altitude.
        return self.distance_km is not None and self.distance_km <= 2.0


class FlightsResponse(BaseModel):
    """Payload returned by the /flights endpoint and pushed over WebSocket."""

    location: Location
    radius_km: float
    count: int
    generated_at: int = Field(..., description="Unix timestamp of this snapshot")
    flights: list[Flight]


class ChatRequest(BaseModel):
    question: str
    flight: Flight | None = None


class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str | None = None
