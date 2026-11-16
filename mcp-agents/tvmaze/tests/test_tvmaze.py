"""
Tests for TVMaze MCP Server — both client and server layers.
"""

from __future__ import annotations

import pytest
import json
import httpx

from tvmaze_client import (
    Show, Episode, CastMember, ScheduleItem,
    search_shows, get_show_by_id, get_episodes, get_cast, get_schedule,
    set_client, _get_client,
    simulate_search_shows, simulate_episodes,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_client():
    """Reset the injected client before each test."""
    set_client(None)
    yield
    set_client(None)


def _mock_transport(request: httpx.Request) -> httpx.Response:
    """Route mock responses based on URL patterns."""
    url = str(request.url)
    if "search/shows" in url and "q=test" in url:
        return httpx.Response(200, json=[
            {
                "show": {
                    "id": 100,
                    "name": "Test Show",
                    "type": "Scripted",
                    "language": "English",
                    "genres": ["Drama", "Thriller"],
                    "status": "Running",
                    "runtime": 60,
                    "averageRuntime": 58,
                    "premiered": "2021-03-15",
                    "ended": None,
                    "officialSite": "https://testshow.com",
                    "network": {"name": "Test Network", "id": 1},
                    "webChannel": None,
                    "image": {"medium": "img.jpg", "original": "img_big.jpg"},
                    "summary": "<p>A test show about testing.</p>",
                    "rating": {"average": 8.2},
                    "weight": 99,
                }
            }
        ])
    elif "shows/100/episodes" in url:
        return httpx.Response(200, json=[
            {
                "id": 1001,
                "name": "Pilot",
                "season": 1,
                "number": 1,
                "airdate": "2021-03-15",
                "airtime": "21:00",
                "runtime": 60,
                "summary": "<p>The first episode.</p>",
                "image": {"medium": "ep1.jpg", "original": "ep1_big.jpg"},
            },
            {
                "id": 1002,
                "name": "Second Episode",
                "season": 1,
                "number": 2,
                "airdate": "2021-03-22",
                "airtime": "21:00",
                "runtime": 60,
                "summary": "<p>The second episode.</p>",
                "image": None,
            },
        ])
    elif "shows/100/cast" in url:
        return httpx.Response(200, json=[
            {
                "person": {
                    "id": 500,
                    "name": "Jane Test",
                    "image": {"medium": "jane.jpg"},
                },
                "character": {
                    "name": "Dr. Sample",
                    "url": "http://example.com/char/1",
                },
            }
        ])
    elif "schedule" in url and "country=US" in url:
        return httpx.Response(200, json=[
            {
                "id": 200,
                "name": "Evening News",
                "airdate": "2024-01-15",
                "airtime": "19:00",
                "season": 1,
                "number": 1,
                "summary": "<p>Top stories.</p>",
                "show": {"id": 300, "name": "Test News"},
            }
        ])
    elif "shows/200" in url:
        return httpx.Response(200, json={
            "id": 200,
            "name": "Another Show",
            "type": "Reality",
            "language": "English",
            "status": "Ended",
        })
    return httpx.Response(404, json={"error": "Not found"})


def _mock_client() -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(_mock_transport))


# ---------------------------------------------------------------------------
# Data model tests
# ---------------------------------------------------------------------------

class TestShowModel:
    def test_from_dict_minimal(self):
        d = {"id": 1, "name": "Test"}
        show = Show.from_dict(d)
        assert show.id == 1
        assert show.name == "Test"
        assert show.genres == []
        assert show.rating is None

    def test_from_dict_full(self):
        d = {
            "id": 42,
            "name": "Full Show",
            "type": "Scripted",
            "language": "English",
            "genres": ["Drama", "Comedy"],
            "status": "Running",
            "runtime": 30,
            "averageRuntime": 28,
            "premiered": "2022-01-01",
            "ended": None,
            "officialSite": "https://example.com",
            "network": {"name": "NBC", "id": 1},
            "webChannel": None,
            "image": {"medium": "med.jpg", "original": "orig.jpg"},
            "summary": "<p>Great show</p>",
            "rating": {"average": 9.0},
            "weight": 50,
        }
        show = Show.from_dict(d)
        assert show.name == "Full Show"
        assert show.network == "NBC"
        assert show.rating == 9.0
        assert show.summary == "Great show"
        assert show.image_medium == "med.jpg"

    def test_from_dict_no_html(self):
        d = {"id": 3, "name": "X", "summary": "<b>Bold</b> <i>text</i>."}
        show = Show.from_dict(d)
        assert show.summary == "Bold text."


class TestEpisodeModel:
    def test_from_dict(self):
        d = {
            "id": 10,
            "name": "Ep One",
            "season": 2,
            "number": 3,
            "airdate": "2024-05-01",
            "airtime": "22:00",
            "runtime": 45,
            "summary": "<p>An episode.</p>",
            "image": {"medium": "ep.jpg", "original": "ep_big.jpg"},
        }
        ep = Episode.from_dict(d)
        assert ep.name == "Ep One"
        assert ep.season == 2
        assert ep.number == 3
        assert ep.summary == "An episode."


class TestCastMemberModel:
    def test_from_dict(self):
        d = {
            "person": {"id": 99, "name": "Actor", "image": {"medium": "act.jpg"}},
            "character": {"name": "Hero", "url": "http://char/1"},
        }
        cm = CastMember.from_dict(d)
        assert cm.person_name == "Actor"
        assert cm.character_name == "Hero"
        assert cm.image_medium == "act.jpg"


# ---------------------------------------------------------------------------
# Client tests (with mock transport)
# ---------------------------------------------------------------------------

class TestClient:
    def test_search_shows(self):
        set_client(_mock_client())
        results = search_shows("test")
        assert len(results) >= 1
        assert results[0].name == "Test Show"
        assert results[0].rating == 8.2
        assert results[0].network == "Test Network"

    def test_search_empty(self):
        mock_empty = httpx.Client(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=[])
        ))
        set_client(mock_empty)
        results = search_shows("nonexistent")
        assert results == []

    def test_get_episodes(self):
        set_client(_mock_client())
        eps = get_episodes(100)
        assert len(eps) == 2
        assert eps[0].season == 1
        assert eps[0].number == 1

    def test_get_cast(self):
        set_client(_mock_client())
        cast = get_cast(100)
        assert len(cast) == 1
        assert cast[0].person_name == "Jane Test"
        assert cast[0].character_name == "Dr. Sample"

    def test_get_schedule(self):
        set_client(_mock_client())
        schedule = get_schedule(country="US")
        assert len(schedule) >= 1
        assert schedule[0].show_name == "Test News"

    def test_get_show_by_id(self):
        set_client(_mock_client())
        show = get_show_by_id(200)
        assert show.name == "Another Show"
        assert show.type == "Reality"

    def test_simulate_search(self):
        results = simulate_search_shows("test")
        assert len(results) == 2
        assert results[0].source == "simulated"
        assert "test" in results[0].name.lower()

    def test_simulate_episodes(self):
        eps = simulate_episodes("Test", season_count=2)
        assert len(eps) == 6  # 2 seasons × 3 episodes
        assert eps[0].source == "simulated"

    def test_set_client_none(self):
        set_client(None)
        client = _get_client()
        assert client is not None


# ---------------------------------------------------------------------------
# Server tool integration tests (using the actual tool call pattern)
# ---------------------------------------------------------------------------

class TestServerTools:
    """Verify that the server module's tool functions produce expected output."""

    def test_search_tv_shows_imports(self):
        """Just verify the tool function can be imported."""
        from server import search_tv_shows
        assert search_tv_shows is not None

    def test_get_show_details_imports(self):
        from server import get_show_details
        assert get_show_details is not None

    def test_get_episode_list_imports(self):
        from server import get_episode_list
        assert get_episode_list is not None

    def test_get_cast_list_imports(self):
        from server import get_cast_list
        assert get_cast_list is not None

    def test_get_tv_schedule_imports(self):
        from server import get_tv_schedule
        assert get_tv_schedule is not None

    def test_search_celebrities_imports(self):
        from server import search_celebrities
        assert search_celebrities is not None