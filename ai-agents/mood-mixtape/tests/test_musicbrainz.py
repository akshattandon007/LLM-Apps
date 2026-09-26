"""Tests for the MusicBrainz API client."""

from __future__ import annotations

import json
from unittest.mock import Mock

import httpx
import pytest

from mood_mixtape.musicbrainz import (
    search_by_mood_keywords,
    search_recordings,
    set_client,
)


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the HTTP client before and after each test."""
    set_client(None)
    yield
    set_client(None)


def _mock_response(status_code: int, json_data: dict) -> httpx.Response:
    """Create a mock httpx.Response."""
    return httpx.Response(status_code=status_code, json=json_data)


class TestSearchRecordings:
    """Tests for search_recordings()."""

    def test_returns_tracks_from_response(self):
        """Should parse recording results into Track objects."""
        mock_data = {
            "recordings": [
                {
                    "id": "abc-123",
                    "title": "Happy Song",
                    "artist-credit": [{"name": "Happy Artist"}],
                    "releases": [{"title": "Happy Album"}],
                },
                {
                    "id": "def-456",
                    "title": "Joyful Tune",
                    "artist-credit": [{"name": "Joy Singer"}],
                    "releases": [],
                },
            ]
        }
        mock_client = httpx.Client(transport=httpx.MockTransport(lambda r: _mock_response(200, mock_data)))
        set_client(mock_client)

        tracks = search_recordings("happy", limit=10)

        assert len(tracks) == 2
        assert tracks[0].title == "Happy Song"
        assert tracks[0].artist == "Happy Artist"
        assert tracks[0].release == "Happy Album"
        assert tracks[0].recording_id == "abc-123"

        assert tracks[1].title == "Joyful Tune"
        assert tracks[1].artist == "Joy Singer"
        assert tracks[1].release is None

    def test_empty_response_returns_empty_list(self):
        """Should return empty list when no recordings found."""
        mock_client = httpx.Client(transport=httpx.MockTransport(lambda r: _mock_response(200, {"recordings": []})))
        set_client(mock_client)

        tracks = search_recordings("xyznonexistent", limit=10)
        assert tracks == []

    def test_handles_missing_artist_credit(self):
        """Should handle recordings with partial data gracefully."""
        mock_data = {
            "recordings": [
                {
                    "id": "xyz",
                    "title": "Solo Track",
                    "artist-credit": [],
                    "releases": [],
                }
            ]
        }
        mock_client = httpx.Client(transport=httpx.MockTransport(lambda r: _mock_response(200, mock_data)))
        set_client(mock_client)

        tracks = search_recordings("solo", limit=10)
        assert len(tracks) == 1
        assert tracks[0].title == "Solo Track"
        assert tracks[0].artist == "Unknown Artist"

    def test_raises_on_http_error(self):
        """Should raise on non-200 responses."""
        def handler(r):
            return _mock_response(503, {"error": "Service Unavailable"})

        mock_client = httpx.Client(transport=httpx.MockTransport(handler))
        set_client(mock_client)

        with pytest.raises(httpx.HTTPStatusError):
            search_recordings("happy", limit=10)


class TestSearchByMoodKeywords:
    """Tests for search_by_mood_keywords()."""

    def test_searches_multiple_keywords_and_deduplicates(self):
        """Should search each keyword and remove duplicate tracks."""
        call_count = 0

        def handler(r):
            nonlocal call_count
            call_count += 1
            title = f"Track {call_count}"
            return _mock_response(200, {
                "recordings": [
                    {
                        "id": f"id-{call_count}",
                        "title": title,
                        "artist-credit": [{"name": f"Artist {call_count}"}],
                        "releases": [],
                    }
                ]
            })

        mock_client = httpx.Client(transport=httpx.MockTransport(handler))
        set_client(mock_client)

        tracks = search_by_mood_keywords(["happy", "sad"], limit=4)

        assert len(tracks) <= 4
        assert call_count >= 2  # At least one call per keyword

    def test_handles_keyword_with_no_results(self):
        """Should not crash when a keyword returns nothing."""
        def handler(r):
            return _mock_response(200, {"recordings": []})

        mock_client = httpx.Client(transport=httpx.MockTransport(handler))
        set_client(mock_client)

        tracks = search_by_mood_keywords(["veryobscureemotionxyz"], limit=10)
        assert tracks == []