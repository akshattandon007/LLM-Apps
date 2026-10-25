"""Shared data models for SafeRide agents."""

from dataclasses import dataclass, field
from typing import Optional


# ── Vehicle Safety ─────────────────────────────────────────────────────────────

@dataclass
class Recall:
    nhtsa_id: str
    component: str
    summary: str
    consequence: str
    remedy: str
    safety_risk: str  # low / medium / high / critical
    report_date: str
    source: str = "live"


@dataclass
class VehicleCheck:
    vin: Optional[str]
    make: str
    model: str
    year: int
    recalls: list[Recall] = field(default_factory=list)
    recall_count: int = 0
    status: str = "clear"  # clear / recall_found / error
    message: str = ""
    source: str = "live"


# ── Weather / Route ────────────────────────────────────────────────────────────

@dataclass
class Waypoint:
    name: str
    lat: float
    lon: float


@dataclass
class SegmentForecast:
    location: str
    lat: float
    lon: float
    temp_c: float
    feels_like_c: float
    precip_mm: float
    wind_speed_kmh: float
    wind_gust_kmh: float
    visibility_km: float
    condition: str  # clear / rain / snow / fog / storm
    hazard: bool = False
    hazard_note: str = ""
    source: str = "live"


@dataclass
class RouteWeather:
    origin_name: str
    origin_forecast: SegmentForecast
    destination_name: str
    destination_forecast: SegmentForecast
    waypoint_forecasts: list[SegmentForecast] = field(default_factory=list)
    total_hazards: int = 0
    overall_rating: str = "good"  # good / moderate / caution / avoid
    source: str = "live"


# ── Trip Advisor ───────────────────────────────────────────────────────────────

@dataclass
class RestStop:
    name: str
    address: str
    lat: float
    lon: float
    distance_km: float
    type: str  # rest_area / gas_station / hospital


@dataclass
class TripReport:
    vehicle: VehicleCheck
    weather: RouteWeather
    rest_stops: list[RestStop] = field(default_factory=list)
    summary: str = ""
    verdict: str = ""  # "All clear — safe to drive!" / "Issues found — review details"
    source: str = "live"