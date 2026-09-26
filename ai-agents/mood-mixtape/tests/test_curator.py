"""Tests for the LLM curator module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from mood_mixtape.curator import analyze_mood, curate_mixtape
from mood_mixtape.models import Track


def _build_completion(content: dict) -> MagicMock:
    """Build a mock completion with the given dict as JSON content."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(content)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


def _mock_openai(return_values: list[dict]) -> MagicMock:
    """Create a mock OpenAI client that returns different JSON on successive calls.

    Args:
        return_values: List of dicts to return in order for each .create() call.
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        _build_completion(rv) for rv in return_values
    ]
    return mock_client


class TestAnalyzeMood:
    """Tests for analyze_mood()."""

    def test_returns_parsed_mood_data(self):
        """Should return the parsed JSON from the LLM."""
        expected = {
            "mood": "melancholic nostalgia",
            "description": "A bittersweet longing for the past with a touch of sadness",
            "search_keywords": ["nostalgic", "melancholic", "acoustic", "slow tempo", "reflective"],
            "genres": ["indie folk", "singer-songwriter", "ambient"],
        }
        client = _mock_openai([expected])
        result = analyze_mood("Feeling nostalgic about growing up", client=client)
        assert result == expected

    def test_handles_empty_mood(self):
        """Should return something for an empty or minimal input."""
        expected = {
            "mood": "neutral",
            "description": "A balanced, contemplative state",
            "search_keywords": ["neutral", "calm", "instrumental"],
            "genres": ["ambient", "classical"],
        }
        client = _mock_openai([expected])
        result = analyze_mood("", client=client)
        assert result == expected


class TestCurateMixtape:
    """Tests for curate_mixtape()."""

    def test_returns_curated_mixtape(self):
        """Should return a Mixtape with songs selected from the track list."""
        tracks = [
            Track(title="Happy Song", artist="Happy Artist", release="Happy Album"),
            Track(title="Joyful Tune", artist="Joy Singer", release="Joy Album"),
            Track(title="Sunny Day", artist="Sun Artist"),
            Track(title="Good Vibes", artist="Vibe Master", release="Vibes"),
            Track(title="Wonderful Life", artist="Life Band"),
            Track(title="Beautiful Morning", artist="Morning Glory"),
            Track(title="Dancing Queen", artist="Abba", release="Arrival"),
            Track(title="Don't Stop Believin'", artist="Journey", release="Escape"),
            Track(title="Here Comes the Sun", artist="Beatles", release="Abbey Road"),
            Track(title="Happy", artist="Pharrell", release="G I R L"),
        ]

        mixtape_response = {
            "playlist_name": "Sunshine State of Mind",
            "cover_art_description": "A bright yellow sun rising over green hills with musical notes floating in the air",
            "vibe_description": "Pure joy and optimism \u2014 the perfect soundtrack for a perfect day",
            "songs": [
                {"index": 1, "title": "Happy Song", "artist": "Happy Artist", "why_it_fits": "Instant mood booster"},
                {"index": 2, "title": "Here Comes the Sun", "artist": "Beatles", "why_it_fits": "Optimism anthem"},
                {"index": 3, "title": "Happy", "artist": "Pharrell", "why_it_fits": "Smile when this plays"},
                {"index": 4, "title": "Don't Stop Believin'", "artist": "Journey", "why_it_fits": "Uplifting classic"},
                {"index": 5, "title": "Sunny Day", "artist": "Sun Artist", "why_it_fits": "Light feel-good track"},
                {"index": 6, "title": "Dancing Queen", "artist": "Abba", "why_it_fits": "Joyful energy"},
                {"index": 7, "title": "Good Vibes", "artist": "Vibe Master", "why_it_fits": "Carefree mood"},
                {"index": 8, "title": "Beautiful Morning", "artist": "Morning Glory", "why_it_fits": "Fresh start energy"},
            ],
        }
        mood_response = {
            "mood": "happy optimism",
            "description": "A bright, cheerful state of mind",
            "search_keywords": ["happy", "upbeat", "positive"],
            "genres": ["pop", "dance"],
        }

        client = _mock_openai([mixtape_response, mood_response])
        mixtape = curate_mixtape("Feeling incredibly happy and optimistic", tracks, client=client)

        assert mixtape.playlist_name == "Sunshine State of Mind"
        assert len(mixtape.songs) == 8
        assert mixtape.songs[0].title == "Happy Song"
        assert mixtape.songs[0].why_it_fits != ""
        assert mixtape.mood == "happy optimism"

    def test_empty_track_list_returns_no_songs(self):
        """Should handle empty track list gracefully."""
        client = _mock_openai([
            {
                "playlist_name": "Empty Playlist",
                "cover_art_description": "Minimalist design with silence",
                "vibe_description": "Quiet contemplation",
                "songs": [],
            },
            {
                "mood": "quiet reflective",
                "description": "A calm, contemplative state",
                "search_keywords": ["calm", "quiet", "reflective"],
                "genres": ["ambient", "classical"],
            },
        ])

        mixtape = curate_mixtape("Quiet and reflective", [], client=client)
        assert mixtape.playlist_name == "Empty Playlist"
        assert mixtape.songs == []

    def test_each_song_has_why_it_fits(self):
        """Every selected song should have a reason it fits the mood."""
        tracks = [
            Track(title="Song A", artist="Artist A"),
            Track(title="Song B", artist="Artist B"),
            Track(title="Song C", artist="Artist C"),
        ]

        client = _mock_openai([
            {
                "playlist_name": "Test Playlist",
                "cover_art_description": "Abstract shapes",
                "vibe_description": "Test vibe",
                "songs": [
                    {"index": 1, "title": "Song A", "artist": "Artist A", "why_it_fits": "Fits the mood perfectly"},
                    {"index": 2, "title": "Song B", "artist": "Artist B", "why_it_fits": "Great energy match"},
                ],
            },
            {
                "mood": "energetic",
                "description": "High energy state",
                "search_keywords": ["energetic", "upbeat", "fast"],
                "genres": ["rock", "electronic"],
            },
        ])

        mixtape = curate_mixtape("Energetic", tracks, client=client)

        for song in mixtape.songs:
            assert song.why_it_fits, f"Song '{song.title}' is missing 'why it fits' explanation"