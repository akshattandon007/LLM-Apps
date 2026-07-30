"""Tests for the geospatial helpers."""

import pytest

from flights_over_me.geo import (
    bearing_deg,
    bounding_box,
    compass_point,
    haversine_km,
    look_angle,
)


def test_haversine_zero_distance():
    assert haversine_km(51.5, -0.12, 51.5, -0.12) == pytest.approx(0.0, abs=1e-9)


def test_haversine_known_distance_london_paris():
    # London (LHR-ish) to Paris (CDG-ish) is ~340 km great-circle.
    d = haversine_km(51.47, -0.45, 49.01, 2.55)
    assert 330 < d < 360


def test_haversine_symmetry():
    a = haversine_km(40.0, -73.0, 34.0, -118.0)
    b = haversine_km(34.0, -118.0, 40.0, -73.0)
    assert a == pytest.approx(b)


def test_bounding_box_contains_point():
    box = bounding_box(51.5, -0.12, 50)
    assert box.lamin < 51.5 < box.lamax
    assert box.lomin < -0.12 < box.lomax


def test_bounding_box_radius_scales_latitude_delta():
    small = bounding_box(0.0, 0.0, 10)
    big = bounding_box(0.0, 0.0, 100)
    assert (big.lamax - big.lamin) > (small.lamax - small.lamin)


def test_bounding_box_longitude_widens_near_poles():
    # At higher latitude, the same radius spans more longitude degrees.
    equator = bounding_box(0.0, 0.0, 50)
    high = bounding_box(60.0, 0.0, 50)
    eq_width = equator.lomax - equator.lomin
    high_width = high.lomax - high.lomin
    assert high_width > eq_width


def test_bounding_box_clamps_to_valid_range():
    box = bounding_box(89.9, 179.9, 250)
    assert box.lamax <= 90.0
    assert box.lomax <= 180.0
    assert box.lamin >= -90.0


def test_bounding_box_rejects_nonpositive_radius():
    with pytest.raises(ValueError):
        bounding_box(0.0, 0.0, 0)


@pytest.mark.parametrize(
    "deg,expected",
    [(0, "N"), (90, "E"), (180, "S"), (270, "W"), (45, "NE"), (None, "—")],
)
def test_compass_point(deg, expected):
    assert compass_point(deg) == expected


def test_bearing_cardinal_directions():
    # From the equator/prime-meridian origin.
    assert bearing_deg(0, 0, 1, 0) == pytest.approx(0, abs=0.5)    # due north
    assert bearing_deg(0, 0, 0, 1) == pytest.approx(90, abs=0.5)   # due east
    assert bearing_deg(0, 0, -1, 0) == pytest.approx(180, abs=0.5) # due south
    assert bearing_deg(0, 0, 0, -1) == pytest.approx(270, abs=0.5) # due west


def test_bearing_range_is_0_to_360():
    b = bearing_deg(51.5, -0.12, 48.85, 2.35)  # London -> Paris (south-east)
    assert 0 <= b < 360
    assert 120 < b < 160  # roughly SE


def test_look_angle_straight_up():
    # Aircraft directly overhead (zero ground distance) -> 90 deg elevation.
    elev, slant = look_angle(0.0, 10000.0)
    assert elev == pytest.approx(90.0, abs=0.01)
    assert slant == pytest.approx(10.0, abs=0.01)


def test_look_angle_45_degrees():
    # Ground distance == altitude -> 45 deg.
    elev, slant = look_angle(10.0, 10000.0)  # 10 km ground, 10 km alt
    assert elev == pytest.approx(45.0, abs=0.5)
    assert slant == pytest.approx(14.142, abs=0.05)


def test_look_angle_low_on_horizon():
    elev, _ = look_angle(50.0, 1000.0)  # far and low
    assert 0 < elev < 5


def test_look_angle_handles_missing_altitude():
    assert look_angle(10.0, None) == (None, None)
