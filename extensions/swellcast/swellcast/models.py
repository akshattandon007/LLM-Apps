"""Data models for SwellCast."""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Coordinates:
    lat: float
    lon: float


@dataclass
class Location:
    name: str
    country: str
    lat: float
    lon: float
    admin1: str = ""
    timezone: str = "UTC"


@dataclass
class SurfDay:
    """A single day of surf conditions."""
    dt: date
    wave_height_m: float | None = None
    wave_dir_deg: int | None = None
    wave_period_s: float | None = None
    swell_height_m: float | None = None
    swell_dir_deg: int | None = None
    swell_period_s: float | None = None
    wind_speed_kmh: float | None = None
    wind_dir_deg: int | None = None
    temp_max_c: float | None = None
    weather_code: int | None = None
    score: float = 0.0
    score_label: str = "N/A"
    conditions_note: str = ""


@dataclass
class SurfReport:
    """Full surf report for a location."""
    location: Location
    days: list[SurfDay] = field(default_factory=list)
    generated: str = ""