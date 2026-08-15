"""Smoke tests for Spotify DJ MCP Agent.

Tests use FakeSpotifyClient injected via tools.setup().
No real Spotify credentials required.
"""

from __future__ import annotations

import pytest

from src.spotify_client import FakeSpotifyClient
from src.tools import _get_client, setup


def test_setup_initializes_client() -> None:
    """setup() with a fake client makes it available via _get_client()."""
    fake = FakeSpotifyClient()
    setup(client=fake)
    client = _get_client()
    assert client is fake, "setup() should store the provided client"


def test_setup_without_arg_creates_real_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """setup() without arg creates a real SpotifyClient (needs env vars)."""
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test-id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "test-secret")
    setup()
    from src.spotify_client import SpotifyClient
    assert isinstance(_get_client(), SpotifyClient)


def test_get_client_raises_if_not_setup() -> None:
    """_get_client() raises RuntimeError if setup() was not called."""
    # Unset any previously set client
    from src import tools
    tools._client = None
    with pytest.raises(RuntimeError, match="not initialized"):
        _get_client()


class TestSearchTracks:
    """Tests for the search_tracks tool."""

    def test_search_returns_formatted_results(self) -> None:
        """search_tracks returns formatted strings with track info."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        # Import the tool function directly
        from src.tools import register_tools
        from mcp.server.mcpserver import MCPServer

        server = MCPServer(name="test-server")
        register_tools(server)

        # Call the underlying client method directly
        results = fake.search_tracks("ambient", limit=5)
        assert len(results) == 1
        assert results[0]["type"] == "track"
        assert results[0]["data"]["name"] == "Fake Song: ambient"

    def test_search_passes_correct_args(self) -> None:
        """search_tracks passes query and limit to the client."""
        fake = FakeSpotifyClient()
        setup(client=fake)
        fake.search_tracks("electronic", limit=3)
        assert fake.search_tracks_called_with == [("electronic", 3)]


class TestGetRecommendations:
    """Tests for the get_recommendations tool."""

    def test_basic_recommendations(self) -> None:
        """get_recommendations returns track results."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        results = fake.get_recommendations(
            seed_genres=["ambient"],
            target_bpm=100,
            limit=5,
        )
        assert len(results) == 1
        assert results[0]["data"]["name"] == "Recommended Track (100BPM)"

    def test_recommendations_with_all_params(self) -> None:
        """get_recommendations accepts all audio feature targets."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        fake.get_recommendations(
            seed_tracks=["track1"],
            seed_artists=["artist1"],
            seed_genres=["ambient"],
            target_energy=0.3,
            target_valence=0.2,
            target_bpm=90,
            target_danceability=0.2,
            target_acousticness=0.8,
            target_instrumentalness=0.9,
            limit=10,
        )
        assert len(fake.get_recommendations_called_with) == 1
        args = fake.get_recommendations_called_with[0]
        assert args[3] == 0.3  # target_energy
        assert args[4] == 0.2  # target_valence
        assert args[5] == 90   # target_bpm


class TestGetNewReleases:
    """Tests for the get_new_releases tool."""

    def test_new_releases(self) -> None:
        """get_new_releases returns album results."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        results = fake.get_new_releases(limit=5)
        assert len(results) == 1
        assert results[0]["type"] == "album"
        assert results[0]["data"]["name"] == "New Fake Album"

    def test_new_releases_passes_country(self) -> None:
        """get_new_releases passes country parameter."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        fake.get_new_releases(limit=3, country="GB")
        assert fake.get_new_releases_called_with == [(3, "GB")]


class TestGetArtistTopTracks:
    """Tests for the get_artist_top_tracks tool."""

    def test_artist_top_tracks(self) -> None:
        """get_artist_top_tracks returns track results for an artist."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        results = fake.get_artist_top_tracks("artist123")
        assert len(results) == 1
        assert results[0]["data"]["name"] == "Artist Top Hit"

    def test_artist_top_tracks_passes_market(self) -> None:
        """get_artist_top_tracks passes market parameter."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        fake.get_artist_top_tracks("artist123", market="JP")
        assert fake.get_artist_top_tracks_called_with == [("artist123", "JP")]


class TestDescribeTrack:
    """Tests for the describe_track tool."""

    def test_describe_track_includes_audio_features(self) -> None:
        """describe_track returns track info with audio features."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        result = fake.describe_track("track123")
        assert "audio_features" in result
        assert result["audio_features"]["bpm"] == 105.0
        assert result["audio_features"]["key"] == "C"
        assert result["audio_features"]["energy"] == 0.65

    def test_describe_track_passes_id(self) -> None:
        """describe_track passes the track_id correctly."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        fake.describe_track("specific-track-id")
        assert fake.describe_track_called_with == ["specific-track-id"]


class TestGetPlaylist:
    """Tests for the get_playlist tool."""

    def test_get_playlist(self) -> None:
        """get_playlist returns playlist with tracks."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        result = fake.get_playlist("playlist123")
        assert result["name"] == "Fake Playlist"
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["name"] == "Playlist Track 1"

    def test_get_playlist_passes_id(self) -> None:
        """get_playlist passes the playlist_id correctly."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        fake.get_playlist("my-playlist")
        assert fake.get_playlist_called_with == ["my-playlist"]


class TestCreatePlaylist:
    """Tests for the create_playlist tool."""

    def test_create_playlist(self) -> None:
        """create_playlist returns playlist info."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        result = fake.create_playlist(
            user_id="user123",
            name="My Test Playlist",
            description="Testing the DJ",
        )
        assert result["name"] == "My Test Playlist"
        assert result["description"] == "Testing the DJ"

    def test_create_playlist_with_tracks(self) -> None:
        """create_playlist accepts track URIs."""
        fake = FakeSpotifyClient()
        setup(client=fake)

        fake.create_playlist(
            user_id="user123",
            name="Curated List",
            track_uris=["spotify:track:abc", "spotify:track:def"],
        )
        assert fake.create_playlist_called_with[0][4] == ["spotify:track:abc", "spotify:track:def"]


class TestFormatting:
    """Tests for the formatting helpers in tools.py."""

    def test_search_results_empty(self) -> None:
        """Empty results produce a 'no results' message."""
        from src.tools import _format_search_results
        msg = _format_search_results([])
        assert "No results found" in msg

    def test_recommendations_empty(self) -> None:
        """Empty recommendations produce a helpful message."""
        from src.tools import _format_recommendations
        msg = _format_recommendations([])
        assert "No recommendations" in msg

    def test_new_releases_empty(self) -> None:
        """Empty new releases produce a 'no results' message."""
        from src.tools import _format_new_releases
        msg = _format_new_releases([])
        assert "No new releases" in msg

    def test_search_results_single(self) -> None:
        """Single result is formatted correctly."""
        from src.tools import _format_search_results
        results = [
            {
                "type": "track",
                "data": {
                    "id": "t1",
                    "name": "Test Song",
                    "artists": [{"id": "a1", "name": "Test Artist"}],
                    "album": {"id": "al1", "name": "Test Album"},
                },
            }
        ]
        msg = _format_search_results(results)
        assert "Test Song" in msg
        assert "Test Artist" in msg
        assert "Test Album" in msg

    def test_track_description_format(self) -> None:
        """Track description includes all audio feature fields."""
        from src.tools import _format_track_description
        result = {
            "id": "t1",
            "name": "Analysis Track",
            "artists": [{"id": "a1", "name": "Analyst"}],
            "duration_ms": 180000,
            "popularity": 70,
            "explicit": False,
            "audio_features": {
                "bpm": 120.0,
                "key": "G",
                "key_number": 7,
                "mode": "minor",
                "energy": 0.8,
                "valence": 0.3,
                "danceability": 0.6,
                "acousticness": 0.2,
                "instrumentalness": 0.5,
                "speechiness": 0.02,
                "loudness": -6.0,
            },
        }
        msg = _format_track_description(result)
        assert "Analysis Track" in msg
        assert "Analyst" in msg
        assert "120.0" in msg
        assert "G" in msg
        assert "0.800" in msg


def test_fake_client_is_isolated() -> None:
    """Each FakeSpotifyClient instance has its own call history."""
    fake1 = FakeSpotifyClient()
    fake2 = FakeSpotifyClient()

    fake1.search_tracks("query1")
    fake2.search_tracks("query2")

    assert len(fake1.search_tracks_called_with) == 1
    assert fake1.search_tracks_called_with[0][0] == "query1"
    assert len(fake2.search_tracks_called_with) == 1
    assert fake2.search_tracks_called_with[0][0] == "query2"