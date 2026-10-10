"""CLI tests — argparse wiring and output content, via capsys and an
injected fixture client (no network)."""

import pytest

from breatheasy.cli import main
from breatheasy.api import OpenMeteoClient
from tests import load_fixture, make_http_client


def run_cli(argv, air_quality=None, geocode=None):
    client = OpenMeteoClient(make_http_client(air_quality=air_quality, geocode=geocode))
    return main(argv, client=client)


def test_help_lists_commands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for cmd in ("now", "forecast", "pollen", "serve"):
        assert cmd in out


def test_now_output(capsys):
    rc = run_cli(["now", "Brooklyn"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Brooklyn, New York, United States" in out
    assert "US AQI: 61" in out
    assert "Moderate" in out
    assert "Top pollutant: PM2.5 (19.9 µg/m³)" in out
    assert (
        "Unusually sensitive people should consider reducing prolonged "
        "outdoor exertion." in out
    )


def test_now_output_accepts_latlon(capsys):
    rc = run_cli(["now", "40.71,-74.01"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "40.7100, -74.0100" in out  # fast-path label, no geocoding


def test_forecast_output(capsys):
    rc = run_cli(["forecast", "Brooklyn", "--days", "3"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(3-day forecast)" in out
    assert "2026-10-10" in out
    assert "2026-10-11" in out
    assert "Worst hour today (2026-10-10): 23:00 — AQI 66" in out
    assert "Advice:" in out


def test_forecast_days_clamped_to_7(capsys):
    rc = run_cli(["forecast", "Brooklyn", "--days", "99"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(7-day forecast)" in out


def test_pollen_output(capsys):
    pollen = load_fixture("pollen_sample.json")
    rc = run_cli(["pollen", "Chicago", "--days", "1"], air_quality=pollen)
    assert rc == 0
    out = capsys.readouterr().out
    assert "(1-day peak)" in out
    assert "Grass" in out and "high" in out and "80" in out
    assert "Mugwort" in out and "120" in out
    assert "Ragweed" in out and "no data" in out


def test_pollen_no_data_region(capsys):
    # Plain air-quality sample has no pollen variables at all.
    rc = run_cli(["pollen", "Brooklyn"], air_quality=load_fixture("air_quality_sample.json"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No pollen data for this region/season" in out


def test_unknown_place_exits_1(capsys):
    rc = run_cli(["now", "Atlantis"], geocode={"results": []})
    assert rc == 1
    captured = capsys.readouterr()
    assert "Could not find place" in captured.err
    assert "Atlantis" in captured.err
    assert captured.out == ""


def test_api_failure_exits_1(capsys):
    from tests import make_http_client

    client = OpenMeteoClient(
        make_http_client(status=500, air_quality=load_fixture("air_quality_sample.json"))
    )
    rc = main(["now", "Brooklyn"], client=client)
    assert rc == 1
    captured = capsys.readouterr()
    assert "Could not fetch" in captured.err