"""Tests for place resolution: "lat,lon" fast path and geocoding."""

import pytest

from breatheasy.geo import GeoLookupError, parse_coords, resolve_place
from tests import make_client


def test_parse_coords_basic():
    assert parse_coords("40.71,-74.01") == (40.71, -74.01)


def test_parse_coords_accepts_spaces_and_signs():
    assert parse_coords(" 40.71 , -74.01 ") == (40.71, -74.01)
    assert parse_coords("-33.86,151.21") == (-33.86, 151.21)


def test_parse_coords_rejects_place_names():
    assert parse_coords("Brooklyn") is None
    assert parse_coords("New York, NY") is None


def test_parse_coords_rejects_out_of_range():
    assert parse_coords("999,-74") is None
    assert parse_coords("40,181") is None
    assert parse_coords("-91,0") is None


def test_parse_coords_rejects_garbage():
    assert parse_coords("") is None
    assert parse_coords("a,b") is None
    assert parse_coords("40.71;-74.01") is None
    assert parse_coords("40.71  -74.01") is None


def test_resolve_coords_fast_path_skips_network():
    class NoNetwork:
        def geocode(self, query):  # pragma: no cover - must never run
            raise AssertionError("geocode must not be called for coords")

    lat, lon, label = resolve_place("40.71,-74.01", NoNetwork())
    assert (lat, lon) == (40.71, -74.01)
    assert label == "40.7100, -74.0100"


def test_resolve_place_geocodes_brooklyn():
    client = make_client()
    lat, lon, label = resolve_place("Brooklyn", client)
    assert (lat, lon) == (40.6501, -73.94958)
    assert label == "Brooklyn, New York, United States"


def test_resolve_place_unknown_raises():
    client = make_client(geocode={"results": []})
    with pytest.raises(GeoLookupError):
        resolve_place("Atlantis", client)


def test_resolve_place_picks_first_result():
    geo = {
        "results": [
            {
                "name": "Springfield",
                "latitude": 39.8,
                "longitude": -89.6,
                "country": "United States",
                "admin1": "Illinois",
            },
            {
                "name": "Springfield",
                "latitude": 37.2,
                "longitude": -93.3,
                "country": "United States",
                "admin1": "Missouri",
            },
        ]
    }
    client = make_client(geocode=geo)
    lat, lon, label = resolve_place("Springfield", client)
    assert (lat, lon) == (39.8, -89.6)  # first (most relevant) wins
    assert label == "Springfield, Illinois, United States"


def test_resolve_place_label_falls_back_to_name_only():
    geo = {"results": [{"name": "Alone", "latitude": 1.0, "longitude": 2.0}]}
    client = make_client(geocode=geo)
    _, _, label = resolve_place("Alone", client)
    assert label == "Alone"