"""Unit tests for the embedded advice tables (EPA bands, pollen buckets)."""

import pytest

from breatheasy.advice import (
    EPA_BANDS,
    POLLEN_EMOJI,
    POLLEN_GUIDANCE,
    aqi_advice,
    aqi_band,
    aqi_category,
    aqi_color,
    aqi_emoji,
    pollen_bucket,
    top_pollutant,
)

# Every EPA band boundary: (aqi, expected category)
BOUNDARY_CASES = [
    (0, "Good"),
    (49, "Good"),
    (50, "Good"),
    (51, "Moderate"),
    (100, "Moderate"),
    (101, "Unhealthy for Sensitive Groups"),
    (150, "Unhealthy for Sensitive Groups"),
    (151, "Unhealthy"),
    (200, "Unhealthy"),
    (201, "Very Unhealthy"),
    (300, "Very Unhealthy"),
    (301, "Hazardous"),
    (500, "Hazardous"),
]


@pytest.mark.parametrize("aqi,expected", BOUNDARY_CASES)
def test_epa_band_boundaries(aqi, expected):
    assert aqi_category(aqi) == expected


def test_band_advice_texts_exact():
    assert (
        aqi_advice(50)
        == "Air quality is good — enjoy the outdoors."
    )
    assert (
        aqi_advice(100)
        == "Unusually sensitive people should consider reducing prolonged "
        "outdoor exertion."
    )
    assert (
        aqi_advice(101)
        == "Children, older adults, and people with heart or lung disease "
        "should reduce prolonged outdoor exertion."
    )
    assert (
        aqi_advice(151)
        == "Everyone should reduce prolonged or heavy outdoor exertion."
    )
    assert aqi_advice(201) == "Health alert — avoid outdoor exertion."
    assert (
        aqi_advice(301)
        == "Emergency conditions — stay indoors and keep windows shut."
    )


def test_every_band_has_full_fields():
    assert len(EPA_BANDS) == 6
    for band in EPA_BANDS:
        assert band.name and band.category and band.advice
        assert band.color.startswith("#")
        assert band.emoji


def test_hazardous_is_open_ended():
    assert EPA_BANDS[-1].high is None
    assert aqi_category(9999) == "Hazardous"


def test_missing_aqi_is_none():
    assert aqi_band(None) is None
    assert aqi_category(None) is None
    assert aqi_advice(None) is None


def test_negative_aqi_clamps_to_good():
    assert aqi_category(-5) == "Good"


def test_epa_colors():
    assert aqi_color(50) == "#00E400"
    assert aqi_color(100) == "#FFFF00"
    assert aqi_color(301) == "#7E0023"


def test_epa_emoji():
    assert aqi_emoji(50) == "🌳"
    assert aqi_emoji(151) == "🚨"
    assert aqi_emoji(301) == "💀"


# -- Pollen buckets --------------------------------------------------------

POLLEN_CASES = [
    (0, "none"),
    (0.5, "low"),
    (1, "low"),
    (30, "low"),
    (30.1, "medium"),
    (75, "medium"),
    (75.1, "high"),
    (500, "high"),
    (None, "none"),
]


@pytest.mark.parametrize("value,bucket", POLLEN_CASES)
def test_pollen_buckets(value, bucket):
    assert pollen_bucket(value) == bucket


def test_pollen_guidance_covers_all_buckets():
    for bucket in ("none", "low", "medium", "high"):
        assert POLLEN_GUIDANCE[bucket]
        assert POLLEN_EMOJI[bucket]


# -- Top pollutant ---------------------------------------------------------

def test_top_pollutant_picks_pm25_from_sample():
    # pm2_5 19.9/15 = 1.33 > pm10 20.2/45 = 0.45 > ozone 0/100 = 0
    current = {"pm2_5": 19.9, "pm10": 20.2, "ozone": 0.0}
    assert top_pollutant(current) == ("pm2_5", 19.9)


def test_top_pollutant_picks_ozone_when_extreme():
    current = {"pm2_5": 10.0, "pm10": 20.0, "ozone": 130.0}
    assert top_pollutant(current) == ("ozone", 130.0)


def test_top_pollutant_ignores_missing_columns():
    assert top_pollutant({"pm2_5": 999.0}) == ("pm2_5", 999.0)
    assert top_pollutant({}) is None
    assert top_pollutant({"us_aqi": 61}) is None