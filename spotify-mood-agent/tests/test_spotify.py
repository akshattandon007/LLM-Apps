"""
Tests for Spotify client data mapping.
Tests use mocked spotipy responses — no real API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.spotify.client import SpotifyClient
from src.spotify.models import AudioFeatures, Track
from tests.fixtures.mock_spotify import (
    MOCK_ARTISTS,
    MOCK_AUDIO_FEATURES,
    MOCK_RECENTLY_PLAYED,
)


class TestSpotifyClientMapping:
    """Test that raw Spotify API dicts are correctly mapped to our models."""

    def setup_method(self):
        self.mock_sp = MagicMock()
        self.client = SpotifyClient(self.mock_sp)

    def test_map_track_item(self):
        raw = MOCK_RECENTLY_PLAYED["items"][0]["track"]
        track = self.client._map_track_item(raw)
        assert track.id == "track_001"
        assert track.name == "Holocene"
        assert track.primary_artist == "Bon Iver"
        assert track.album_release_year == 2011
        assert track.explicit is False

    def test_fetch_audio_features_maps_correctly(self):
        self.mock_sp.audio_features.return_value = MOCK_AUDIO_FEATURES
        features = self.client._fetch_audio_features(["track_001"])
        assert "track_001" in features
        af = features["track_001"]
        assert isinstance(af, AudioFeatures)
        assert af.valence == pytest.approx(0.261)
        assert af.energy == pytest.approx(0.299)
        assert af.acousticness == pytest.approx(0.889)

    def test_audio_features_mood_score(self):
        self.mock_sp.audio_features.return_value = MOCK_AUDIO_FEATURES[:1]
        features = self.client._fetch_audio_features(["track_001"])
        af = features["track_001"]
        # mood_score = valence*0.6 + energy*0.4
        expected = 0.261 * 0.6 + 0.299 * 0.4
        assert af.mood_score == pytest.approx(expected, rel=0.01)

    def test_fetch_artist_genres(self):
        self.mock_sp.artists.return_value = MOCK_ARTISTS
        genres = self.client._fetch_artist_genres(["artist_bon_iver"])
        assert "artist_bon_iver" in genres
        assert "indie folk" in genres["artist_bon_iver"]["genres"]
        assert genres["artist_bon_iver"]["popularity"] == 73

    def test_get_recently_played_integration(self):
        """Integration test for the full recently_played pipeline."""
        self.mock_sp.current_user_recently_played.return_value = {
            **MOCK_RECENTLY_PLAYED,
            "cursors": {},  # Empty cursors → stop pagination
        }
        self.mock_sp.audio_features.return_value = MOCK_AUDIO_FEATURES
        self.mock_sp.artists.return_value = MOCK_ARTISTS

        session = self.client.get_recently_played(limit=5)
        assert session.track_count == 5
        assert len(session.tracks_with_features) == 5

        # Check first track
        first = session.tracks[0]
        assert first.name == "Holocene"
        assert first.audio_features is not None
        assert first.audio_features.valence == pytest.approx(0.261)
        assert "indie folk" in first.all_genres

    def test_empty_session(self):
        self.mock_sp.current_user_recently_played.return_value = {
            "items": [],
            "cursors": None,
        }
        session = self.client.get_recently_played()
        assert session.track_count == 0


class TestAudioFeaturesModel:
    """Test AudioFeatures model properties."""

    def make_af(self, valence=0.5, energy=0.5, mode=1) -> AudioFeatures:
        return AudioFeatures(
            track_id="t1",
            danceability=0.5,
            energy=energy,
            key=0,
            loudness=-10,
            mode=mode,
            speechiness=0.05,
            acousticness=0.3,
            instrumentalness=0.0,
            liveness=0.1,
            valence=valence,
            tempo=120,
            duration_ms=200_000,
            time_signature=4,
        )

    def test_is_major(self):
        assert self.make_af(mode=1).is_major is True
        assert self.make_af(mode=0).is_major is False

    def test_duration_minutes(self):
        af = self.make_af()
        assert af.duration_minutes == pytest.approx(200_000 / 60_000)

    def test_mood_score_range(self):
        af = self.make_af(valence=1.0, energy=1.0)
        assert 0 <= af.mood_score <= 1
        af_low = self.make_af(valence=0.0, energy=0.0)
        assert af_low.mood_score == 0.0
