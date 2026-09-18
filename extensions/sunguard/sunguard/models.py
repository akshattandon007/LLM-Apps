"""Pydantic models for SunGuard MCP server responses."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


class SkinType(str, Enum):
    I = "I"  # Always burns, never tans
    II = "II"  # Burns easily, tans minimally
    III = "III"  # Burns moderately, tans gradually
    IV = "IV"  # Burns minimally, tans well
    V = "V"  # Burns rarely, tans profusely
    VI = "VI"  # Never burns


class SunSafetyResult(BaseModel):
    """Combined UV + heat + AQI verdict for today."""
    location: str
    uv_index: float = Field(..., description="Max UV index for today")
    uv_risk: RiskLevel
    temperature: float = Field(..., description="Max temperature in °C")
    heat_index: Optional[float] = Field(None, description="Heat index in °C (None if irrelevant)")
    heat_risk: Optional[RiskLevel] = None
    aqi: Optional[int] = Field(None, description="European AQI value (0-500)")
    aqi_risk: Optional[RiskLevel] = None
    overall_risk: RiskLevel
    recommendation: str
    source: str = "live"  # "live" or "simulated"


class HourlyUVResult(BaseModel):
    """Hourly UV index forecast."""
    location: str
    date: str
    hours: list[dict] = Field(..., description="List of {hour, uv_index} dicts")
    peak_uv: float
    peak_hour: str
    source: str = "live"


class BurnTimeResult(BaseModel):
    """How long until sunburn for a given skin type and UV index."""
    skin_type: SkinType
    uv_index: float
    burn_time_minutes: int
    description: str
    recommendation: str


class HeatSafetyResult(BaseModel):
    """Heat index + heat advisory check."""
    location: str
    temperature: float
    heat_index: float
    heat_index_risk: RiskLevel
    advisories: list[str] = Field(default_factory=list)
    recommendation: str
    source: str = "live"


class AirQualityResult(BaseModel):
    """AQI with activity recommendations."""
    location: str
    aqi: int
    aqi_level: str
    risk: RiskLevel
    sources: list[str] = Field(default_factory=list)
    recommendation: str
    source: str = "live"


class OutdoorPlanResult(BaseModel):
    """Safety assessment for a specific activity and time."""
    location: str
    activity: str
    time: str
    uv_index: float
    temperature: float
    heat_index: Optional[float] = None
    aqi: Optional[int] = None
    is_safe: bool
    concerns: list[str] = Field(default_factory=list)
    recommendation: str
    source: str = "live"