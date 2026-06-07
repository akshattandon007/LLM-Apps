"""Tests for airline resolution from callsigns."""

import pytest

from flights_over_me.services.airlines import (
    airline_icao_from_callsign,
    resolve_airline,
)


@pytest.mark.parametrize(
    "callsign,code",
    [
        ("BAW123", "BAW"),
        ("baw123", "BAW"),
        ("  DLH9LF ", "DLH"),
        ("UAL", "UAL"),
        ("N12345", None),  # private registration, not an airline code
        ("", None),
        (None, None),
    ],
)
def test_airline_icao_from_callsign(callsign, code):
    assert airline_icao_from_callsign(callsign) == code


def test_resolve_known_airline():
    code, name = resolve_airline("BAW221")
    assert code == "BAW"
    assert name == "British Airways"


def test_resolve_unknown_prefix_returns_code_only():
    code, name = resolve_airline("ZZZ999")
    assert code == "ZZZ"
    assert name is None


def test_resolve_non_airline_callsign():
    code, name = resolve_airline("N12345")
    assert code is None
    assert name is None
