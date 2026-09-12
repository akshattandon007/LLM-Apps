"""Smoke tests for WhatToWatch — runs against mock data, not live API."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models import ScheduleEntry, Show
from src.schedule import whats_on_right_now, whats_on_tonight, daily_schedule
from src.search import search_show, search_by_genre
from src.recommendations import find_similar_shows
from src.genres import normalize_genre_input, discover_by_genre
from src.tvmaze import TVMazeClient


# ── Model tests ───────────────────────────────────────────────────────────


class TestShowModel:
    def test_from_tvmaze_show(self, mock_show_data: dict[str, Any]) -> None:
        show = Show.from_tvmaze_show(mock_show_data)
        assert show.name == "The Office"
        assert show.rating == 8.8
        assert show.network == "NBC"
        assert show.country == "US"
        assert "Comedy" in show.genres
        assert show.status == "Ended"
        assert show.summary_plain().startswith("A mockumentary")
        assert show.schedule_time == "21:00"
        assert show.schedule_days == ["Thursday"]

    def test_from_schedule_episode(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        entry = mock_schedule_data[0]
        show = Show.from_schedule_episode(entry)
        assert show.name == "Cosmic Frontiers"
        assert show.network == "BBC One"
        assert show.country == "GB"

    def test_no_rating(self) -> None:
        data = {
            "id": 999,
            "name": "Test Show",
            "genres": [],
            "status": "Running",
            "rating": None,
            "network": None,
            "webChannel": None,
            "summary": None,
            "language": None,
            "premiered": None,
            "ended": None,
            "schedule": None,
        }
        show = Show.from_tvmaze_show(data)
        assert show.rating == 0.0
        assert show.summary_plain() == "No summary available."

    def test_no_summary(self) -> None:
        data = {
            "id": 998,
            "name": "Quiet Show",
            "genres": [],
            "status": "Ended",
            "rating": {"average": 5.0},
            "network": None,
            "webChannel": None,
            "summary": None,
            "language": None,
            "premiered": None,
            "ended": None,
            "schedule": None,
        }
        show = Show.from_tvmaze_show(data)
        assert show.summary_plain() == "No summary available."


class TestScheduleEntry:
    def test_from_tvmaze(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        entry = ScheduleEntry.from_tvmaze(mock_schedule_data[0])
        assert entry.id == 1
        assert entry.airtime == "20:00"
        assert entry.airdate == "2026-09-12"
        assert entry.show.name == "Cosmic Frontiers"
        assert entry.season == 1
        assert entry.episode == 1

    def test_from_tvmaze_empty(self) -> None:
        entry = ScheduleEntry.from_tvmaze({})
        assert entry.id == 0
        assert entry.show.name == "Unknown"


# ── Genre helpers ─────────────────────────────────────────────────────────


class TestNormalizeGenre:
    def test_exact_group(self) -> None:
        assert normalize_genre_input("comedy") == ["Comedy", "Anime"]

    def test_exact_genre(self) -> None:
        assert normalize_genre_input("drama") == ["Drama", "Romance", "Medical", "Legal"]

    def test_sci_fi(self) -> None:
        result = normalize_genre_input("sci-fi")
        assert "Science-Fiction" in result or "Sci-Fi" in result

    def test_unknown(self) -> None:
        assert normalize_genre_input("quantum") == []

    def test_partial_match(self) -> None:
        result = normalize_genre_input("doc")
        assert len(result) > 0


class TestDiscoverByGenre:
    def test_discover(self, mock_shows_page: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.shows_page.return_value = mock_shows_page
        results = discover_by_genre(client, ["Comedy"], limit=5)
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert "Parks and Recreation" in names


# ── Schedule functions ────────────────────────────────────────────────────


class TestWhatsOnRightNow:
    def test_returns_string(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.schedule.return_value = mock_schedule_data

        with patch("src.schedule.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-09-12"
            mock_dt.now.return_value.hour = 20
            result = whats_on_right_now(client, country="US")
            assert isinstance(result, str)
            assert "Cosmic Frontiers" in result

    def test_genre_filter(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.schedule.return_value = mock_schedule_data

        with patch("src.schedule.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-09-12"
            mock_dt.now.return_value.hour = 20
            result = whats_on_right_now(client, country="US", genre="food")
            assert isinstance(result, str)


class TestWhatsOnTonight:
    def test_returns_string(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.schedule.return_value = mock_schedule_data

        with patch("src.schedule.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-09-12"
            result = whats_on_tonight(client, country="US")
            assert isinstance(result, str)
            assert "Cosmic Frontiers" in result or "Night Watch" in result

    def with_genre(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.schedule.return_value = mock_schedule_data

        with patch("src.schedule.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-09-12"
            result = whats_on_tonight(client, genre="food", country="US")
            assert isinstance(result, str)


class TestDailySchedule:
    def test_returns_string(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.schedule.return_value = mock_schedule_data
        result = daily_schedule(client, date="2026-09-12", country="US")
        assert isinstance(result, str)
        assert "Cosmic Frontiers" in result

    def test_default_date(self, mock_schedule_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.schedule.return_value = mock_schedule_data

        with patch("src.schedule.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = "2026-09-12"
            result = daily_schedule(client, country="US")
            assert isinstance(result, str)
            assert "Cosmic Frontiers" in result


# ── Search functions ──────────────────────────────────────────────────────


class TestSearchShow:
    def test_returns_string(self, mock_search_data: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.search_show.return_value = mock_search_data
        result = search_show(client, query="Breaking Bad")
        assert isinstance(result, str)
        assert "Breaking Bad" in result

    def test_not_found(self) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.search_show.return_value = []
        result = search_show(client, query="Xyzzy")
        assert "No shows found" in result


class TestSearchByGenre:
    def test_returns_string(self, mock_shows_page: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.shows_page.return_value = mock_shows_page
        result = search_by_genre(client, "comedy", limit=5)
        assert isinstance(result, str)

    def test_unknown_genre(self) -> None:
        client = MagicMock(spec=TVMazeClient)
        result = search_by_genre(client, "quantum")
        assert "Unknown genre" in result


# ── Recommendations ───────────────────────────────────────────────────────


class TestFindSimilarShows:
    def test_returns_string(self, mock_show_data: dict[str, Any], mock_shows_page: list[dict[str, Any]]) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.show_by_name.return_value = mock_show_data
        client.shows_page.return_value = mock_shows_page
        result = find_similar_shows(client, show_name="The Office")
        assert isinstance(result, str)
        assert "Parks and Recreation" in result or "similar" in result.lower()

    def test_show_not_found(self) -> None:
        client = MagicMock(spec=TVMazeClient)
        client.show_by_name.return_value = None
        result = find_similar_shows(client, show_name="NonExistentShow")
        assert "Could not find" in result


# ── Server bootstrap (just check imports) ─────────────────────────────────


class TestServerBootstrap:
    def test_server_imports(self) -> None:
        """server.py imports should work without errors."""
        import sys
        sys.path.insert(0, "/data/LLM-Apps/mcp-agents/what-to-watch")
        try:
            from server import app, call_tool, list_tools
            assert app is not None
        finally:
            sys.path.pop(0)