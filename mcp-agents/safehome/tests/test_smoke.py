"""Smoke tests for SafeHome MCP server.

Tests core business logic modules with real API calls where needed,
and the server tool registration.
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# -------------------------------------------------------------------
# Tests for src.geocoder
# -------------------------------------------------------------------

def test_geocode_known_address():
    """Should return lat/lon for a well-known US address."""
    from src.geocoder import geocode
    lat, lon, formatted = geocode("1600 Pennsylvania Ave NW, Washington, DC")
    assert isinstance(lat, float), f"Expected float lat, got {type(lat)}"
    assert isinstance(lon, float), f"Expected float lon, got {type(lon)}"
    assert abs(lat) > 0, f"Expected non-zero latitude"
    assert "DC" in formatted or "WASHINGTON" in formatted.upper(), \
        f"Expected DC in formatted address, got: {formatted}"


def test_geocode_invalid_address():
    """Should raise ValueError for an unresolvable address."""
    from src.geocoder import geocode
    try:
        geocode("asdfghjklzxcvbnm1234567890")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # expected


# -------------------------------------------------------------------
# Tests for src.disasters
# -------------------------------------------------------------------

def test_get_state_code_abbr():
    """Should return state code from abbreviation."""
    from src.disasters import get_state_code
    assert get_state_code("CA") == "CA"
    assert get_state_code("NY") == "NY"
    assert get_state_code("TX") == "TX"


def test_get_state_code_name():
    """Should return state code from full name."""
    from src.disasters import get_state_code
    assert get_state_code("California") == "CA"
    assert get_state_code("New York") == "NY"
    assert get_state_code("texas") == "TX"


def test_disaster_incident_type_label():
    """Should return human-readable labels."""
    from src.disasters import disaster_incident_type_label
    assert "Major Disaster" in disaster_incident_type_label("DR")
    assert "Fire Management" in disaster_incident_type_label("FM")
    assert disaster_incident_type_label("ZZ") == "ZZ"  # unknown


def test_get_disasters_for_state():
    """Should return disaster declarations for a state."""
    from src.disasters import get_disasters_for_state
    disasters = get_disasters_for_state("DC")
    assert isinstance(disasters, list)
    if disasters:
        d = disasters[0]
        assert "declarationDate" in d or "declarationTitle" in d, \
            f"Unexpected disaster structure: {list(d.keys())}"


# -------------------------------------------------------------------
# Tests for src.weather
# -------------------------------------------------------------------

def test_get_active_alerts():
    """Should return alerts for a known location."""
    from src.weather import get_active_alerts
    # Washington DC coordinates
    alerts = get_active_alerts(38.8987, -77.0352)
    assert isinstance(alerts, list)


def test_severity_sort_key():
    """Should return numeric sort key for severity levels."""
    from src.weather import severity_sort_key
    assert severity_sort_key({"severity": "Extreme"}) == 0
    assert severity_sort_key({"severity": "Severe"}) == 1
    assert severity_sort_key({"severity": "Unknown"}) == 4
    assert severity_sort_key({}) == 5


def test_format_alerts_empty():
    """Should return 'no alerts' message for empty list."""
    from src.weather import format_alerts
    result = format_alerts([])
    assert "No active" in result or "Good weather" in result


def test_format_forecast():
    """Should return a formatted string or 'no forecast'."""
    from src.weather import format_forecast
    result = format_forecast({"periods": []})
    assert "No forecast" in result or "available" in result


# -------------------------------------------------------------------
# Tests for src.report
# -------------------------------------------------------------------

def test_generate_report_known_address():
    """Should generate a complete report for a known address."""
    from src.report import generate_safety_report
    report = generate_safety_report("1600 Pennsylvania Ave NW, Washington, DC")
    assert "SafeHome Report" in report
    assert "**Coordinates**" in report
    assert "Weather" in report
    assert "Forecast" in report


def test_generate_report_invalid_address():
    """Should raise ValueError for invalid address."""
    from src.report import generate_safety_report
    try:
        generate_safety_report("asdfghjklzxcvbnm1234567890")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# -------------------------------------------------------------------
# Tests for server.py (tool registration)
# -------------------------------------------------------------------

def test_tool_registration():
    """Should register all 6 tools."""
    from server import TOOL_DESCRIPTIONS, INPUT_SCHEMAS, _handlers
    assert len(TOOL_DESCRIPTIONS) == 6
    assert len(INPUT_SCHEMAS) == 6
    assert len(_handlers) == 6
    assert "safety_report" in TOOL_DESCRIPTIONS
    assert "geocode" in TOOL_DESCRIPTIONS
    assert "weather_alerts" in TOOL_DESCRIPTIONS
    assert "forecast" in TOOL_DESCRIPTIONS
    assert "disaster_history" in TOOL_DESCRIPTIONS
    assert "state_alerts" in TOOL_DESCRIPTIONS


def test_tool_handler_exists():
    """Each tool should have a callable handler."""
    from server import TOOL_DESCRIPTIONS, _handlers
    for name in TOOL_DESCRIPTIONS:
        assert name in _handlers, f"Missing handler for {name}"
        assert callable(_handlers[name]), f"Handler for {name} is not callable"


# -------------------------------------------------------------------
# Run all tests
# -------------------------------------------------------------------

def main() -> int:
    """Run all test functions and report results."""
    import traceback

    test_functions = [
        ("geocode_known_address", test_geocode_known_address),
        ("geocode_invalid_address", test_geocode_invalid_address),
        ("get_state_code_abbr", test_get_state_code_abbr),
        ("get_state_code_name", test_get_state_code_name),
        ("disaster_incident_type_label", test_disaster_incident_type_label),
        ("get_disasters_for_state", test_get_disasters_for_state),
        ("get_active_alerts", test_get_active_alerts),
        ("severity_sort_key", test_severity_sort_key),
        ("format_alerts_empty", test_format_alerts_empty),
        ("format_forecast", test_format_forecast),
        ("generate_report_known_address", test_generate_report_known_address),
        ("generate_report_invalid_address", test_generate_report_invalid_address),
        ("tool_registration", test_tool_registration),
        ("tool_handler_exists", test_tool_handler_exists),
    ]

    passed = 0
    failed = 0
    failures = []

    for name, func in test_functions:
        try:
            func()
            passed += 1
            print(f"  PASS  {name}")
        except Exception:
            failed += 1
            failures.append(name)
            print(f"  FAIL  {name}")
            traceback.print_exc()
            print()

    total = len(test_functions)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed", end="")
    if failed:
        print(f", {failed}/{total} failed:")
        for f in failures:
            print(f"  - {f}")
    else:
        print(" — All tests pass! ✅")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())