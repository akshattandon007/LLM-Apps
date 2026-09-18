"""Weather API client for SunGuard.

Uses Open-Meteo APIs (free, zero-auth). All calls use a module-level
httpx client injected via set_client() for testability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

# Module-level client — swap via set_client() for testing
_client: httpx.Client = httpx.Client(timeout=15.0)

# API endpoints
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AQ = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
NWS_ALERTS = "https://api.weather.gov/alerts/active"


# ---------------------------------------------------------------------------
# Client injection for testability
# ---------------------------------------------------------------------------

def set_client(client: httpx.Client) -> None:
    """Swap the module-level httpx client (used by tests)."""
    global _client
    _client = client


def get_client() -> httpx.Client:
    """Return the current module-level httpx client."""
    return _client


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class GeocodeResult:
    name: str
    latitude: float
    longitude: float
    country: str
    admin1: Optional[str] = None  # state / province


@dataclass
class UVForecast:
    max_uv: float
    hourly_uv: list[dict]  # [{hour: int, uv_index: float}, ...]
    max_temp: float
    source: str = "live"  # "live" or "simulated"


@dataclass
class AirQualityData:
    aqi: int
    hourly_values: list[dict]
    source: str = "live"  # "live" or "simulated"


@dataclass
class NWSAlert:
    headline: str
    severity: str
    description: str


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

def geocode(zip_or_city: str) -> GeocodeResult:
    """Resolve a city name or ZIP code to coordinates.

    ZIP codes that are purely numeric are prefixed with the US country
    hint (many are US, but Open-Meteo handles it). Falls back to a
    simulated Portland, OR default if the API fails.
    """
    try:
        params = {"name": zip_or_city, "count": 5, "language": "en", "format": "json"}
        resp = get_client().get(OPEN_METEO_GEOCODE, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            raise ValueError(f"No geocode results for '{zip_or_city}'")
        r = results[0]
        return GeocodeResult(
            name=r.get("name", zip_or_city),
            latitude=r["latitude"],
            longitude=r["longitude"],
            country=r.get("country", ""),
            admin1=r.get("admin1"),
        )
    except Exception:
        return _simulate_geocode(zip_or_city)


def _simulate_geocode(zip_or_city: str) -> GeocodeResult:
    """Simulated geocode — returns Portland, OR coords as fallback."""
    return GeocodeResult(
        name=zip_or_city,
        latitude=45.5152,
        longitude=-122.6784,
        country="US",
        admin1="Oregon",
    )


# ---------------------------------------------------------------------------
# UV / weather forecast
# ---------------------------------------------------------------------------

def get_uv_forecast(lat: float, lon: float) -> UVForecast:
    """Fetch UV index and temperature forecast.

    Returns hourly UV indices and daily max UV / temp. Falls back to
    simulated data on failure.
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "uv_index",
            "daily": "uv_index_max,temperature_2m_max",
            "timezone": "auto",
            "forecast_days": 1,
        }
        resp = get_client().get(OPEN_METEO_FORECAST, params=params)
        resp.raise_for_status()
        data = resp.json()

        # Hourly UV
        hourly_times = data.get("hourly", {}).get("time", [])
        hourly_uv = data.get("hourly", {}).get("uv_index", [])
        hours = []
        for t, uv in zip(hourly_times, hourly_uv):
            # Extract hour from ISO time
            hour_str = t.split("T")[1][:2] if "T" in t else t
            try:
                hour = int(hour_str.lstrip("0") or "0")
            except ValueError:
                hour = 0
            hours.append({"hour": hour, "uv_index": uv})

        daily = data.get("daily", {})
        max_uv = daily.get("uv_index_max", [0])[0] if daily.get("uv_index_max") else 0
        max_temp = daily.get("temperature_2m_max", [20])[0] if daily.get("temperature_2m_max") else 20

        return UVForecast(max_uv=float(max_uv), hourly_uv=hours, max_temp=float(max_temp), source="live")
    except Exception:
        return _simulate_uv_forecast()


def _simulate_uv_forecast() -> UVForecast:
    """Simulated UV forecast for Portland, OR in summer (~6-7 UV)."""
    hours = [{"hour": h, "uv_index": round(0.5 + (6.5 * max(0, 1 - abs(h - 13) / 6)), 1)} for h in range(24)]
    return UVForecast(max_uv=6.5, hourly_uv=hours, max_temp=30.0, source="simulated")


# ---------------------------------------------------------------------------
# Air Quality
# ---------------------------------------------------------------------------

def get_air_quality(lat: float, lon: float) -> AirQualityData:
    """Fetch European AQI. Falls back to simulated data."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "european_aqi",
            "timezone": "auto",
            "forecast_days": 1,
        }
        resp = get_client().get(OPEN_METEO_AQ, params=params)
        resp.raise_for_status()
        data = resp.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        values = hourly.get("european_aqi", [])
        if not values:
            raise ValueError("No AQI data returned")
        # Daily AQI = max of hourly values (most conservative)
        daily_aqi = max(float(v) for v in values)
        hourly_list = [
            {"hour": int(t.split("T")[1][:2].lstrip("0") or "0"), "aqi": int(v)}
            for t, v in zip(times, values)
        ]
        return AirQualityData(aqi=int(daily_aqi), hourly_values=hourly_list, source="live")
    except Exception:
        return _simulate_air_quality()


def _simulate_air_quality() -> AirQualityData:
    """Simulated moderate AQI (~50)."""
    return AirQualityData(aqi=50, hourly_values=[], source="simulated")


# ---------------------------------------------------------------------------
# Heat index calculation
# ---------------------------------------------------------------------------

def calculate_heat_index(temp_c: float, humidity: float = 50.0) -> float:
    """Calculate heat index (apparent temperature) in °C.

    Uses the Rothfusz regression when temp >= 27°C, otherwise returns temp.
    Humidity default 50% (assumed moderate).
    """
    if temp_c < 27:
        return temp_c

    # Convert to Fahrenheit for the NOAA formula
    t_f = temp_c * 9.0 / 5.0 + 32.0
    rh = humidity

    hi_f = (
        -42.379
        + 2.04901523 * t_f
        + 10.14333127 * rh
        - 0.22475541 * t_f * rh
        - 6.83783e-3 * t_f * t_f
        - 5.481717e-2 * rh * rh
        + 1.22874e-3 * t_f * t_f * rh
        + 8.5282e-4 * t_f * rh * rh
        - 1.99e-6 * t_f * t_f * rh * rh
    )

    # Adjustments for low humidity / low temp (NOAA corrections)
    if rh < 13 and 80 < t_f < 112:
        adj = ((13.0 - rh) / 4.0) * ((17.0 - abs(t_f - 95.0)) / 17.0) ** 0.5
        hi_f -= adj
    if rh > 85 and 80 < t_f < 87:
        adj = ((rh - 85.0) / 10.0) * ((87.0 - t_f) / 5.0)
        hi_f += adj

    return round((hi_f - 32.0) * 5.0 / 9.0, 1)


def heat_index_risk(hi: float) -> str:
    """Categorize heat index risk level."""
    if hi >= 41:
        return "extreme"
    elif hi >= 33:
        return "very_high"
    elif hi >= 27:
        return "high"
    elif hi >= 24:
        return "moderate"
    return "low"


# ---------------------------------------------------------------------------
# NWS Heat Alerts (US only)
# ---------------------------------------------------------------------------

def get_heat_advisories(lat: float, lon: float) -> list[NWSAlert]:
    """Fetch active weather alerts for a (lat, lon) point.

    Returns only heat-related alerts. Gracefully fails if NWS is unreachable.
    """
    try:
        resp = get_client().get(f"{NWS_ALERTS}?point={lat},{lon}")
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features", [])
        alerts = []
        for f in features:
            props = f.get("properties", {})
            headline = (props.get("headline") or props.get("event", "")).upper()
            if any(kw in headline for kw in ("HEAT", "EXCESSIVE HEAT", "HEAT ADVISORY")):
                alerts.append(NWSAlert(
                    headline=props.get("headline", ""),
                    severity=props.get("severity", "Unknown"),
                    description=props.get("description", ""),
                ))
        return alerts
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Fitzpatrick burn-time mapping
# ---------------------------------------------------------------------------

FITZPATRICK_BURN_MAP = {
    "I": {"min_minutes": 10, "max_minutes": 20, "desc": "Always burns, never tans"},
    "II": {"min_minutes": 20, "max_minutes": 30, "desc": "Burns easily, tans minimally"},
    "III": {"min_minutes": 30, "max_minutes": 40, "desc": "Burns moderately, tans gradually"},
    "IV": {"min_minutes": 40, "max_minutes": 60, "desc": "Burns minimally, tans well"},
    "V": {"min_minutes": 60, "max_minutes": 90, "desc": "Burns rarely, tans profusely"},
    "VI": {"min_minutes": 90, "max_minutes": 120, "desc": "Never burns"},
}


def calculate_burn_time(skin_type: str, uv_index: float) -> tuple[int, str]:
    """Calculate burn time in minutes given Fitzpatrick skin type and UV index.

    Base time is the midpoint of the skin type range, then scaled by UV factor.
    UV 3 (moderate) is the baseline; higher UV = faster burn.
    """
    st = skin_type.upper()
    info = FITZPATRICK_BURN_MAP.get(st, FITZPATRICK_BURN_MAP["III"])
    base = (info["min_minutes"] + info["max_minutes"]) // 2

    if uv_index <= 0:
        return base, info["desc"]

    # Scale: UV 3 = baseline (factor 1.0). UV 11+ = factor ~0.27
    uv_factor = min(max(3.0 / uv_index, 0.25), 3.0)
    burn_time = max(int(base * uv_factor), info["min_minutes"] // 2)
    return burn_time, info["desc"]


# ---------------------------------------------------------------------------
# Risk-level helpers
# ---------------------------------------------------------------------------

def uv_risk_level(uv: float) -> str:
    if uv >= 11:
        return "extreme"
    elif uv >= 8:
        return "very_high"
    elif uv >= 6:
        return "high"
    elif uv >= 3:
        return "moderate"
    return "low"


def aqi_risk_level(aqi: int) -> str:
    if aqi >= 101:
        return "high"
    elif aqi >= 51:
        return "moderate"
    return "low"


def overall_risk(uv: str, heat: str, aqi: str) -> str:
    """Combine risks — pick the highest."""
    order = ["low", "moderate", "high", "very_high", "extreme"]
    max_idx = max(order.index(uv), order.index(heat if heat else "low"), order.index(aqi if aqi else "low"))
    return order[max_idx]