"""Fixtures with mock show data for WhatToWatch tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_DIR.mkdir(exist_ok=True)

# ── Sample schedule entry (episode with nested show) ──────────────────────

SAMPLE_SCHEDULE: list[dict[str, Any]] = [
    {
        "id": 1,
        "airdate": "2026-09-12",
        "airtime": "20:00",
        "season": 1,
        "number": 1,
        "name": "Pilot",
        "show": {
            "id": 1001,
            "name": "Cosmic Frontiers",
            "url": "https://www.tvmaze.com/shows/1001",
            "genres": ["Science-Fiction", "Drama", "Adventure"],
            "status": "Running",
            "rating": {"average": 8.5},
            "network": {
                "name": "BBC One",
                "country": {"code": "GB", "name": "United Kingdom"},
            },
            "webChannel": None,
            "summary": "<p>Exploring the final frontier with cutting-edge science.</p>",
            "language": "English",
            "premiered": "2024-03-15",
            "ended": None,
            "schedule": {"time": "20:00", "days": ["Saturday"]},
        },
    },
    {
        "id": 2,
        "airdate": "2026-09-12",
        "airtime": "21:00",
        "season": 3,
        "number": 7,
        "name": "The Big Bake-Off",
        "show": {
            "id": 1002,
            "name": "The Big Bake-Off",
            "url": "https://www.tvmaze.com/shows/1002",
            "genres": ["Food", "Reality"],
            "status": "Running",
            "rating": {"average": 7.8},
            "network": {
                "name": "Food Network",
                "country": {"code": "US", "name": "United States"},
            },
            "webChannel": None,
            "summary": "<p>Amateur bakers compete in weekly challenges.</p>",
            "language": "English",
            "premiered": "2023-06-01",
            "ended": None,
            "schedule": {"time": "21:00", "days": ["Saturday"]},
        },
    },
    {
        "id": 3,
        "airdate": "2026-09-12",
        "airtime": "22:00",
        "season": 5,
        "number": 12,
        "name": "Night Watch",
        "show": {
            "id": 1003,
            "name": "Night Watch",
            "url": "https://www.tvmaze.com/shows/1003",
            "genres": ["Crime", "Thriller", "Mystery"],
            "status": "Running",
            "rating": {"average": 9.1},
            "network": {
                "name": "HBO",
                "country": {"code": "US", "name": "United States"},
            },
            "webChannel": None,
            "summary": "<p>A gritty detective drama set in New York City.</p>",
            "language": "English",
            "premiered": "2022-01-10",
            "ended": None,
            "schedule": {"time": "22:00", "days": ["Saturday"]},
        },
    },
    {
        "id": 4,
        "airdate": "2026-09-12",
        "airtime": "19:30",
        "season": 2,
        "number": 4,
        "name": "Laugh Track",
        "show": {
            "id": 1004,
            "name": "Laugh Track",
            "url": "https://www.tvmaze.com/shows/1004",
            "genres": ["Comedy"],
            "status": "Ended",
            "rating": {"average": 6.5},
            "network": {
                "name": "NBC",
                "country": {"code": "US", "name": "United States"},
            },
            "webChannel": None,
            "summary": "<p>A sitcom about a stand-up comedian.</p>",
            "language": "English",
            "premiered": "2020-09-20",
            "ended": "2024-05-15",
            "schedule": {"time": "19:30", "days": ["Saturday"]},
        },
    },
]

# ── Sample search results ─────────────────────────────────────────────────

SAMPLE_SEARCH: list[dict[str, Any]] = [
    {
        "score": 0.9,
        "show": {
            "id": 2001,
            "name": "Breaking Bad",
            "url": "https://www.tvmaze.com/shows/2001",
            "genres": ["Crime", "Drama", "Thriller"],
            "status": "Ended",
            "rating": {"average": 9.5},
            "network": {
                "name": "AMC",
                "country": {"code": "US", "name": "United States"},
            },
            "webChannel": None,
            "summary": "<p>A high school chemistry teacher turns to cooking meth.</p>",
            "language": "English",
            "premiered": "2008-01-20",
            "ended": "2013-09-29",
            "schedule": {"time": "21:00", "days": ["Sunday"]},
        },
    },
    {
        "score": 0.85,
        "show": {
            "id": 2002,
            "name": "Better Call Saul",
            "url": "https://www.tvmaze.com/shows/2002",
            "genres": ["Crime", "Drama", "Comedy"],
            "status": "Ended",
            "rating": {"average": 8.9},
            "network": {
                "name": "AMC",
                "country": {"code": "US", "name": "United States"},
            },
            "webChannel": None,
            "summary": "<p>The origin story of Saul Goodman.</p>",
            "language": "English",
            "premiered": "2015-02-08",
            "ended": "2022-08-15",
            "schedule": {"time": "21:00", "days": ["Monday"]},
        },
    },
]

# ── Sample single show (for singlesearch / recommendations) ───────────────

SAMPLE_SHOW: dict[str, Any] = {
    "id": 3001,
    "name": "The Office",
    "url": "https://www.tvmaze.com/shows/3001",
    "genres": ["Comedy"],
    "status": "Ended",
    "rating": {"average": 8.8},
    "network": {
        "name": "NBC",
        "country": {"code": "US", "name": "United States"},
    },
    "webChannel": None,
    "summary": "<p>A mockumentary about office life at Dunder Mifflin.</p>",
    "language": "English",
    "premiered": "2005-03-24",
    "ended": "2013-05-16",
    "schedule": {"time": "21:00", "days": ["Thursday"]},
}

# ── Sample shows page (for genre discovery) ───────────────────────────────

SAMPLE_SHOWS_PAGE: list[dict[str, Any]] = [
    {
        "id": 4001,
        "name": "Parks and Recreation",
        "genres": ["Comedy"],
        "status": "Ended",
        "rating": {"average": 8.6},
        "network": {
            "name": "NBC",
            "country": {"code": "US", "name": "United States"},
        },
        "webChannel": None,
        "summary": "<p>A mockumentary about local government.</p>",
        "language": "English",
        "premiered": "2009-04-09",
        "ended": "2015-02-24",
        "schedule": {"time": "21:00", "days": ["Thursday"]},
    },
    {
        "id": 4002,
        "name": "Stranger Still",
        "genres": ["Science-Fiction", "Horror", "Mystery"],
        "status": "Running",
        "rating": {"average": 8.3},
        "network": None,
        "webChannel": {"name": "Netflix"},
        "summary": "<p>Supernatural events in a small town.</p>",
        "language": "English",
        "premiered": "2016-07-15",
        "ended": None,
        "schedule": {"time": "00:00", "days": ["Friday"]},
    },
]


@pytest.fixture
def mock_schedule_data() -> list[dict[str, Any]]:
    return SAMPLE_SCHEDULE


@pytest.fixture
def mock_search_data() -> list[dict[str, Any]]:
    return SAMPLE_SEARCH


@pytest.fixture
def mock_show_data() -> dict[str, Any]:
    return SAMPLE_SHOW


@pytest.fixture
def mock_shows_page() -> list[dict[str, Any]]:
    return SAMPLE_SHOWS_PAGE