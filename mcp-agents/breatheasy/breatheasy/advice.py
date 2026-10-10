"""Plain-language air quality and pollen advice — embedded offline.

EPA AQI bands (US EPA) and indicative pollen buckets are static tables
shipped with the package, so answers never depend on a network call or an
API key.  Pollen values from Open-Meteo arrive in grains of pollen per
cubic metre (P/m³); the low/medium/high buckets below are indicative
guidance, not a clinical instrument.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AqiBand:
    name: str
    low: int
    high: int | None  # None == unbounded upper range (Hazardous 300+)
    color: str
    category: str
    advice: str
    emoji: str


#: US EPA AQI bands — https://www.airnow.gov/aqi/aqi-basics/
EPA_BANDS: tuple[AqiBand, ...] = (
    AqiBand(
        "Good", 0, 50, "#00E400", "Good",
        "Air quality is good — enjoy the outdoors.", "🌳",
    ),
    AqiBand(
        "Moderate", 51, 100, "#FFFF00", "Moderate",
        "Unusually sensitive people should consider reducing prolonged "
        "outdoor exertion.", "🙂",
    ),
    AqiBand(
        "Unhealthy for Sensitive Groups", 101, 150, "#FF7E00",
        "Unhealthy for Sensitive Groups",
        "Children, older adults, and people with heart or lung disease "
        "should reduce prolonged outdoor exertion.", "😷",
    ),
    AqiBand(
        "Unhealthy", 151, 200, "#FF0000", "Unhealthy",
        "Everyone should reduce prolonged or heavy outdoor exertion.", "🚨",
    ),
    AqiBand(
        "Very Unhealthy", 201, 300, "#8F3F97", "Very Unhealthy",
        "Health alert — avoid outdoor exertion.", "☣️",
    ),
    AqiBand(
        "Hazardous", 301, None, "#7E0023", "Hazardous",
        "Emergency conditions — stay indoors and keep windows shut.", "💀",
    ),
)


def aqi_band(value: float | int | None) -> AqiBand | None:
    """Return the EPA band for an AQI value (None when data is missing)."""
    if value is None:
        return None
    v = int(value)
    if v < 0:
        v = 0
    for band in EPA_BANDS:
        if band.high is None or v <= band.high:
            return band
    return EPA_BANDS[-1]


def aqi_category(value: float | int | None) -> str | None:
    band = aqi_band(value)
    return band.category if band else None


def aqi_advice(value: float | int | None) -> str | None:
    band = aqi_band(value)
    return band.advice if band else None


def aqi_emoji(value: float | int | None) -> str | None:
    band = aqi_band(value)
    return band.emoji if band else None


def aqi_color(value: float | int | None) -> str | None:
    band = aqi_band(value)
    return band.color if band else None


# --- Pollen -------------------------------------------------------------

#: Pollen buckets: 0 → none, <=30 low, <=75 medium, else high (P/m³).
POLLEN_BUCKET_MAX: tuple[tuple[str, float], ...] = (
    ("none", 0.0),
    ("low", 30.0),
    ("medium", 75.0),
    ("high", float("inf")),
)

POLLEN_GUIDANCE: dict[str, str] = {
    "none": "No significant pollen — enjoy the outdoors.",
    "low": "Low pollen — most people should be fine.",
    "medium": "Medium pollen — sensitive noses may want to limit time outside.",
    "high": "High pollen — allergy sufferers should consider staying indoors.",
}

POLLEN_EMOJI: dict[str, str] = {
    "none": "🟢",
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
}

#: (api variable name, display name) — order used in every pollen report.
POLLEN_TYPES: tuple[tuple[str, str], ...] = (
    ("alder_pollen", "Alder"),
    ("birch_pollen", "Birch"),
    ("grass_pollen", "Grass"),
    ("mugwort_pollen", "Mugwort"),
    ("olive_pollen", "Olive"),
    ("ragweed_pollen", "Ragweed"),
)


def pollen_bucket(value: float | int | None) -> str:
    """Map a pollen concentration (P/m³) to none/low/medium/high."""
    if value is None:
        return "none"
    v = float(value)
    if v <= 0:
        return "none"
    if v <= 30:
        return "low"
    if v <= 75:
        return "medium"
    return "high"


# --- Top-pollutant ranking ----------------------------------------------

#: Reference concentrations (µg/m³) used to rank the dominant pollutant:
#: WHO 2021 AQG short-term levels for PM2.5/PM10 and the EU target for
#: ozone.  The pollutant closest to (or most over) its reference leads.
POLLUTANT_REFERENCES: dict[str, float] = {
    "pm2_5": 15.0,
    "pm10": 45.0,
    "ozone": 100.0,
}

POLLUTANT_UNITS: dict[str, str] = {
    "pm2_5": "µg/m³",
    "pm10": "µg/m³",
    "ozone": "µg/m³",
}

POLLUTANT_DISPLAY: dict[str, str] = {
    "pm2_5": "PM2.5",
    "pm10": "PM10",
    "ozone": "Ozone",
}


def top_pollutant(current: dict) -> tuple[str, float] | None:
    """Return (api_key, value) of the pollutant dominating current air.

    None when the payload carries none of the ranked pollutants.
    """
    best: tuple[float, str, float] | None = None
    for key, ref in POLLUTANT_REFERENCES.items():
        value = current.get(key)
        if value is None:
            continue
        ratio = float(value) / ref
        if best is None or ratio > best[0]:
            best = (ratio, key, float(value))
    if best is None:
        return None
    return (best[1], best[2])