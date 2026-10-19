"""Tests for the On This Day data layer (fully hermetic — no network)."""

import pytest

from thenpaper import api


def make_fetcher(payload_by_kind: dict):
    """Return a fake HTTP fetcher keyed on the URL's kind segment."""
    def fetcher(url: str):
        kind = url.split("/")[-3]
        items = payload_by_kind.get(kind, [])
        return 200, {kind: items}
    return fetcher


BIRTHS_PAYLOAD = {
    "births": [
        {
            "year": 1990,
            "text": "A test person is born",
            "pages": [
                {
                    "title": "Test Person",
                    "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Test_Person"}},
                }
            ],
        }
    ]
}


def test_parse_live_births(monkeypatch):
    api.set_fetcher(make_fetcher(BIRTHS_PAYLOAD))
    facts = api.fetch_day(10, 19)
    assert facts.source == "live"
    assert len(facts.births) == 1
    b = facts.births[0]
    assert b.year == 1990
    assert b.kind == "birth"
    assert b.pages[0].title == "Test Person"
    assert b.pages[0].url.startswith("https://en.wikipedia.org")


def test_all_endpoints_fail_simulates(monkeypatch):
    def failing(url: str):
        raise ConnectionError("offline")
    api.set_fetcher(failing)
    facts = api.fetch_day(10, 19)
    assert facts.source == "simulated"
    assert len(facts.events) >= 1


def test_invalid_dates_raise():
    api.set_fetcher(None)
    for month, day in [(0, 1), (13, 1), (1, 0), (1, 32), (2, 30)]:
        with pytest.raises(ValueError):
            api.fetch_day(month, day)
    with pytest.raises(ValueError):
        api.fetch_day("10", 19)


def test_urls_zero_padded(monkeypatch):
    seen = []
    def record(url: str):
        seen.append(url)
        return 200, {"births": []}
    api.set_fetcher(record)
    api.fetch_day(1, 5)
    assert any(url.endswith("/births/01/05") for url in seen)
    assert any(url.endswith("/events/01/05") for url in seen)


def test_holidays_parsed(monkeypatch):
    api.set_fetcher(
        make_fetcher({"holidays": [{"year": 0, "text": "World Pizza Day", "pages": []}]})
    )
    facts = api.fetch_day(2, 9)
    assert len(facts.holidays) == 1
    assert facts.holidays[0].text == "World Pizza Day"


def test_simulate_day_is_deterministic():
    a = api.simulate_day(12, 25)
    b = api.simulate_day(12, 25)
    assert a.to_dict() == b.to_dict()
    assert a.source == "simulated"
    assert a.events[0].year == 1969


def test_simulate_day_validates():
    with pytest.raises(ValueError):
        api.simulate_day(2, 30)