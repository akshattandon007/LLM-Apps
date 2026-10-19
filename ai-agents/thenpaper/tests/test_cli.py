"""Tests for the CLI entry point (offline mode, no network, no LLM)."""

import json

import pytest

from thenpaper.cli import _parse_date, main


def test_parse_date_basic():
    assert _parse_date("12/25") == (12, 25, None)
    assert _parse_date("1/5") == (1, 5, None)
    assert _parse_date("1990/10/19") == (10, 19, 1990)


def test_parse_date_today():
    import datetime
    today = datetime.date.today()
    month, day, year = _parse_date("today")
    assert (month, day) == (today.month, today.day)
    assert year is None


def test_parse_date_invalid():
    with pytest.raises(ValueError):
        _parse_date("13/40")
    with pytest.raises(ValueError):
        _parse_date("banana")
    with pytest.raises(ValueError):
        _parse_date("2/30")


def test_main_offline_json(capsys):
    code = main(["--offline", "--json", "10/19"])
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data["month"] == 10
    assert data["day"] == 19
    assert data["source"] == "simulated"
    assert data["headline"]
    assert data["theme"] == "morning"


def test_main_offline_ascii(capsys):
    code = main(["--offline", "--no-llm", "12/25"])
    out = capsys.readouterr().out
    assert code == 0
    assert "THE" in out
    assert "THEN" in out
    assert "SOURCE" in out
    assert "1969" in out  # simulated lead story


def test_main_offline_theme(capsys):
    code = main(["--offline", "--theme", "late", "7/4"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Late Edition" in out


def test_main_bad_date(capsys):
    code = main(["13/40"])
    err = capsys.readouterr().err
    assert code == 2
    assert "bad date" in err