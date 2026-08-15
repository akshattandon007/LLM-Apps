"""Spotify Web API client — handles auth, search, recommendations, and playlists."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from src.models import Album, Artist, Playlist, Track

logger = logging.getLogger(__name__)

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS_BASE = "https://accounts.spotify.com/api"

KEY_NAMES = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
]


class SpotifyAuthError(Exception):
    """Raised when Spotify authentication fails."""

    pass


class SpotifyAPIError(Exception):
    """Raised when a Spotify API request fails."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(f"Spotify API error {status}: {message}")


class SpotifyClient:
    """Wrapper around the Spotify Web API.

    Uses client-credentials flow for read operations.
    Write operations (create/modify playlists) require explicit auth-code setup.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET", "")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._http = httpx.Client(timeout=30.0)

    # ── Auth ──────────────────────────────────────────────────────────────

    def _ensure_token(self) -> str:
        """Get a valid client-credentials token, refreshing if expired."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if not self.client_id or not self.client_secret:
            raise SpotifyAuthError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set"
            )

        encoded = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        resp = self._http.post(
            f"{SPOTIFY_ACCOUNTS_BASE}/token",
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )

        if resp.status_code != 200:
            raise SpotifyAuthError(
                f"Token request failed ({resp.status_code}): {resp.text}"
            )

        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"] - 60  # 60s buffer
        return self._access_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._ensure_token()}"}

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{SPOTIFY_API_BASE}{path}"
        resp = self._http.get(url, headers=self._headers(), params=params)
        if resp.status_code != 200:
            raise SpotifyAPIError(resp.status_code, resp.text)
        return resp.json()

    def _post(
        self, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{SPOTIFY_API_BASE}{path}"
        resp = self._http.post(url, headers=self._headers(), json=body or {})
        if resp.status_code not in (200, 201):
            raise SpotifyAPIError(resp.status_code, resp.text)
        return resp.json()

    @staticmethod
    def _parse_track(item: dict[str, Any]) -> Track:
        artists = [
            Artist(
                id=a.get("id", ""),
                name=a.get("name", "Unknown"),
                genres=[],
                popularity=0,
                followers=0,
                images=[],
                external_urls=a.get("external_urls", {}),
            )
            for a in item.get("artists", [])
        ]

        album_data = item.get("album")
        album = None
        if album_data:
            album = Album(
                id=album_data.get("id", ""),
                name=album_data.get("name", ""),
                artists=[
                    Artist(id=a.get("id", ""), name=a.get("name", "Unknown"))
                    for a in album_data.get("artists", [])
                ],
                release_date=album_data.get("release_date", ""),
                total_tracks=album_data.get("total_tracks", 0),
                images=album_data.get("images", []),
                external_urls=album_data.get("external_urls", {}),
                album_type=album_data.get("album_type", "album"),
                uri=album_data.get("uri", ""),
            )

        return Track(
            id=item.get("id", ""),
            name=item.get("name", "Unknown Track"),
            artists=artists,
            album=album,
            duration_ms=item.get("duration_ms", 0),
            popularity=item.get("popularity", 0),
            explicit=item.get("explicit", False),
            uri=item.get("uri", ""),
            external_urls=item.get("external_urls", {}),
            preview_url=item.get("preview_url"),
        )

    @staticmethod
    def _parse_artist(item: dict[str, Any]) -> Artist:
        return Artist(
            id=item.get("id", ""),
            name=item.get("name", "Unknown"),
            genres=item.get("genres", []),
            popularity=item.get("popularity", 0),
            followers=item.get("followers", {}).get("total", 0)
            if isinstance(item.get("followers"), dict)
            else 0,
            images=item.get("images", []),
            external_urls=item.get("external_urls", {}),
        )

    @staticmethod
    def _parse_album(item: dict[str, Any]) -> Album:
        return Album(
            id=item.get("id", ""),
            name=item.get("name", ""),
            artists=[
                Artist(id=a.get("id", ""), name=a.get("name", "Unknown"))
                for a in item.get("artists", [])
            ],
            release_date=item.get("release_date", ""),
            total_tracks=item.get("total_tracks", 0),
            images=item.get("images", []),
            external_urls=item.get("external_urls", {}),
            album_type=item.get("album_type", "album"),
            uri=item.get("uri", ""),
        )

    def _parse_playlist(self, data: dict[str, Any]) -> Playlist:
        tracks_data = data.get("tracks", {})
        tracks_items = tracks_data.get("items", []) if isinstance(tracks_data, dict) else []
        tracks = []
        for item in tracks_items:
            track_data = item.get("track")
            if track_data:
                tracks.append(self._parse_track(track_data))

        owner_data = data.get("owner", {})
        owner_name = owner_data.get("display_name", "") if isinstance(owner_data, dict) else ""

        return Playlist(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            owner=owner_name,
            public=data.get("public", True),
            tracks=tracks,
            tracks_total=tracks_data.get("total", len(tracks))
            if isinstance(tracks_data, dict)
            else len(tracks),
            external_urls=data.get("external_urls", {}),
            uri=data.get("uri", ""),
            images=data.get("images", []),
        )

    # ── Search ────────────────────────────────────────────────────────────

    def search_tracks(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search Spotify for tracks, artists, and albums."""
        data = self._get(
            "/search",
            params={"q": query, "type": "track,artist,album", "limit": min(limit, 50)},
        )

        results: list[dict[str, Any]] = []

        # Tracks
        for item in data.get("tracks", {}).get("items", []):
            results.append({"type": "track", "data": self._parse_track(item).model_dump(mode="json")})

        # Artists
        for item in data.get("artists", {}).get("items", []):
            results.append({"type": "artist", "data": self._parse_artist(item).model_dump(mode="json")})

        # Albums
        for item in data.get("albums", {}).get("items", []):
            results.append({"type": "album", "data": self._parse_album(item).model_dump(mode="json")})

        return results[:limit]

    # ── Recommendations ───────────────────────────────────────────────────

    def get_recommendations(
        self,
        seed_tracks: list[str] | None = None,
        seed_artists: list[str] | None = None,
        seed_genres: list[str] | None = None,
        target_energy: float | None = None,
        target_valence: float | None = None,
        target_bpm: float | None = None,
        target_danceability: float | None = None,
        target_acousticness: float | None = None,
        target_instrumentalness: float | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get AI-curated track recommendations."""
        params: dict[str, Any] = {"limit": min(limit, 100)}

        if seed_tracks:
            params["seed_tracks"] = ",".join(seed_tracks[:5])
        if seed_artists:
            params["seed_artists"] = ",".join(seed_artists[:5])
        if seed_genres:
            params["seed_genres"] = ",".join(seed_genres[:5])
        if target_energy is not None:
            params["target_energy"] = target_energy
        if target_valence is not None:
            params["target_valence"] = target_valence
        if target_bpm is not None:
            params["target_tempo"] = target_bpm
        if target_danceability is not None:
            params["target_danceability"] = target_danceability
        if target_acousticness is not None:
            params["target_acousticness"] = target_acousticness
        if target_instrumentalness is not None:
            params["target_instrumentalness"] = target_instrumentalness

        data = self._get("/recommendations", params=params)
        tracks = data.get("tracks", [])

        return [{"type": "track", "data": self._parse_track(t).model_dump(mode="json")} for t in tracks]

    # ── New Releases ──────────────────────────────────────────────────────

    def get_new_releases(
        self, limit: int = 10, country: str = "US"
    ) -> list[dict[str, Any]]:
        """Get the latest album releases."""
        data = self._get(
            "/browse/new-releases",
            params={"limit": min(limit, 50), "country": country},
        )
        albums = data.get("albums", {}).get("items", [])
        return [
            {"type": "album", "data": self._parse_album(a).model_dump(mode="json")}
            for a in albums
        ]

    # ── Artist ────────────────────────────────────────────────────────────

    def get_artist_top_tracks(
        self, artist_id: str, market: str = "US"
    ) -> list[dict[str, Any]]:
        """Get an artist's top tracks by market."""
        data = self._get(f"/artists/{artist_id}/top-tracks", params={"market": market})
        tracks = data.get("tracks", [])
        return [
            {"type": "track", "data": self._parse_track(t).model_dump(mode="json")}
            for t in tracks
        ]

    def get_artist(self, artist_id: str) -> dict[str, Any]:
        """Get detailed artist info."""
        data = self._get(f"/artists/{artist_id}")
        return self._parse_artist(data).model_dump(mode="json")

    # ── Track Details / Audio Features ────────────────────────────────────

    def get_track(self, track_id: str) -> Track:
        """Get track metadata."""
        data = self._get(f"/tracks/{track_id}")
        return self._parse_track(data)

    def get_audio_features(self, track_id: str) -> dict[str, Any]:
        """Get audio features for a track (BPM, key, energy, etc.)."""
        return self._get(f"/audio-features/{track_id}")

    def describe_track(self, track_id: str) -> dict[str, Any]:
        """Get rich description: track metadata + audio features."""
        track = self.get_track(track_id)
        features = self.get_audio_features(track_id)

        key_num = features.get("key")
        key_name = KEY_NAMES[key_num] if key_num is not None and 0 <= key_num < 12 else None
        mode = features.get("mode")  # 0 minor, 1 major
        mode_str = "major" if mode == 1 else "minor" if mode == 0 else None

        track.bpm = features.get("tempo")
        track.key = key_num
        track.key_name = key_name
        track.mode = mode if mode is not None else None
        track.energy = features.get("energy")
        track.valence = features.get("valence")
        track.danceability = features.get("danceability")
        track.acousticness = features.get("acousticness")
        track.instrumentalness = features.get("instrumentalness")
        track.speechiness = features.get("speechiness")
        track.loudness = features.get("loudness")

        result = track.model_dump(mode="json")
        result["audio_features"] = {
            "bpm": track.bpm,
            "key": key_name,
            "key_number": key_num,
            "mode": mode_str,
            "energy": track.energy,
            "valence": track.valence,
            "danceability": track.danceability,
            "acousticness": track.acousticness,
            "instrumentalness": track.instrumentalness,
            "speechiness": track.speechiness,
            "loudness": track.loudness,
        }
        return result

    # ── Playlists (write operations) ──────────────────────────────────────

    def get_playlist(self, playlist_id: str) -> dict[str, Any]:
        """Get playlist details and tracks."""
        data = self._get(f"/playlists/{playlist_id}")
        return self._parse_playlist(data).model_dump(mode="json")

    def create_playlist(
        self,
        user_id: str,
        name: str,
        description: str = "",
        public: bool = True,
        track_uris: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new playlist for a user (requires auth-code token).

        NOTE: This requires user-level authorization (OAuth auth-code flow),
        not just client credentials. Pass a user-scoped token via set_user_token().
        """
        data = self._post(
            f"/users/{user_id}/playlists",
            body={
                "name": name,
                "description": description,
                "public": public,
            },
        )
        playlist = self._parse_playlist(data)

        if track_uris:
            self._post(
                f"/playlists/{playlist.id}/tracks",
                body={"uris": track_uris},
            )

        return playlist.model_dump(mode="json")

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()


class FakeSpotifyClient:
    """In-memory fake for testing — no network calls."""

    def __init__(self) -> None:
        self.search_tracks_called_with: list[tuple] = []
        self.get_recommendations_called_with: list[tuple] = []
        self.get_new_releases_called_with: list[tuple] = []
        self.get_artist_top_tracks_called_with: list[tuple] = []
        self.describe_track_called_with: list[str] = []
        self.get_playlist_called_with: list[str] = []
        self.create_playlist_called_with: list[tuple] = []

    def search_tracks(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        self.search_tracks_called_with.append((query, limit))
        return [
            {
                "type": "track",
                "data": {
                    "id": "fake-track-001",
                    "name": f"Fake Song: {query}",
                    "artists": [{"id": "art-1", "name": "Fake Artist"}],
                    "album": {
                        "id": "alb-1",
                        "name": "Fake Album",
                        "artists": [{"id": "art-1", "name": "Fake Artist"}],
                        "release_date": "2024-01-01",
                        "total_tracks": 10,
                        "images": [],
                        "album_type": "album",
                    },
                    "duration_ms": 240000,
                    "popularity": 50,
                    "explicit": False,
                    "uri": "spotify:track:fake-track-001",
                    "external_urls": {"spotify": "https://open.spotify.com/track/fake-track-001"},
                    "preview_url": None,
                    "bpm": None,
                    "key": None,
                    "energy": None,
                    "valence": None,
                    "danceability": None,
                    "acousticness": None,
                },
            }
        ]

    def get_recommendations(
        self,
        seed_tracks=None,
        seed_artists=None,
        seed_genres=None,
        target_energy=None,
        target_valence=None,
        target_bpm=None,
        target_danceability=None,
        target_acousticness=None,
        target_instrumentalness=None,
        limit=20,
    ):
        self.get_recommendations_called_with.append((
            seed_tracks, seed_artists, seed_genres,
            target_energy, target_valence, target_bpm,
            target_danceability, target_acousticness, target_instrumentalness,
            limit,
        ))
        bpm = target_bpm or 120
        return [
            {
                "type": "track",
                "data": {
                    "id": "fake-rec-001",
                    "name": f"Recommended Track ({bpm}BPM)",
                    "artists": [{"id": "art-2", "name": "AI Curator"}],
                    "album": {"id": "alb-2", "name": "AI Picks", "artists": [{"id": "art-2", "name": "AI Curator"}], "release_date": "2024-06-01", "total_tracks": 1, "images": [], "album_type": "single"},
                    "duration_ms": 200000,
                    "popularity": 70,
                    "explicit": False,
                    "uri": "spotify:track:fake-rec-001",
                    "external_urls": {"spotify": "https://open.spotify.com/track/fake-rec-001"},
                    "preview_url": None,
                    "bpm": None,
                    "key": None,
                    "energy": None,
                    "valence": None,
                    "danceability": None,
                    "acousticness": None,
                },
            }
        ]

    def get_new_releases(self, limit=10, country="US"):
        self.get_new_releases_called_with.append((limit, country))
        return [
            {
                "type": "album",
                "data": {
                    "id": "fake-alb-001",
                    "name": "New Fake Album",
                    "artists": [{"id": "art-3", "name": "New Artist"}],
                    "release_date": "2025-01-15",
                    "total_tracks": 8,
                    "images": [],
                    "external_urls": {"spotify": "https://open.spotify.com/album/fake-alb-001"},
                    "album_type": "album",
                    "uri": "spotify:album:fake-alb-001",
                },
            }
        ]

    def get_artist_top_tracks(self, artist_id: str, market="US"):
        self.get_artist_top_tracks_called_with.append((artist_id, market))
        return [
            {
                "type": "track",
                "data": {
                    "id": "fake-artist-track-001",
                    "name": "Artist Top Hit",
                    "artists": [{"id": artist_id, "name": "Famous Artist"}],
                    "album": {"id": "alb-hit", "name": "Greatest Hits", "artists": [{"id": artist_id, "name": "Famous Artist"}], "release_date": "2023-01-01", "total_tracks": 12, "images": [], "album_type": "album"},
                    "duration_ms": 210000,
                    "popularity": 85,
                    "explicit": False,
                    "uri": f"spotify:track:fake-artist-track-001",
                    "external_urls": {"spotify": "https://open.spotify.com/track/fake-artist-track-001"},
                    "preview_url": None,
                },
            }
        ]

    def describe_track(self, track_id: str):
        self.describe_track_called_with.append(track_id)
        return {
            "id": track_id,
            "name": "Described Track",
            "artists": [{"id": "art-4", "name": "Descriptive Artist"}],
            "album": None,
            "duration_ms": 180000,
            "popularity": 60,
            "explicit": False,
            "uri": f"spotify:track:{track_id}",
            "external_urls": {"spotify": f"https://open.spotify.com/track/{track_id}"},
            "preview_url": None,
            "bpm": None,
            "key": None,
            "energy": None,
            "valence": None,
            "danceability": None,
            "acousticness": None,
            "audio_features": {
                "bpm": 105.0,
                "key": "C",
                "key_number": 0,
                "mode": "major",
                "energy": 0.65,
                "valence": 0.5,
                "danceability": 0.7,
                "acousticness": 0.3,
                "instrumentalness": 0.1,
                "speechiness": 0.05,
                "loudness": -8.5,
            },
        }

    def get_playlist(self, playlist_id: str):
        self.get_playlist_called_with.append(playlist_id)
        return {
            "id": playlist_id,
            "name": "Fake Playlist",
            "description": "A playlist for testing",
            "owner": "Test User",
            "public": True,
            "tracks": [
                {
                    "id": "fake-pt-1",
                    "name": "Playlist Track 1",
                    "artists": [{"id": "art-5", "name": "Playlist Artist"}],
                    "album": {"id": "alb-pl", "name": "Playlist Album", "artists": [{"id": "art-5", "name": "Playlist Artist"}], "release_date": "2024-03-01", "total_tracks": 5, "images": [], "album_type": "album"},
                    "duration_ms": 190000,
                    "popularity": 55,
                    "explicit": False,
                    "uri": "spotify:track:fake-pt-1",
                    "external_urls": {"spotify": "https://open.spotify.com/track/fake-pt-1"},
                    "preview_url": None,
                    "bpm": None,
                    "key": None,
                    "energy": None,
                    "valence": None,
                    "danceability": None,
                    "acousticness": None,
                }
            ],
            "tracks_total": 1,
            "external_urls": {"spotify": f"https://open.spotify.com/playlist/{playlist_id}"},
            "uri": f"spotify:playlist:{playlist_id}",
            "images": [],
        }

    def get_artist(self, artist_id: str):
        return {"id": artist_id, "name": "Famous Artist", "genres": ["electronic", "ambient"], "popularity": 80, "followers": 1000000, "images": [], "external_urls": {"spotify": f"https://open.spotify.com/artist/{artist_id}"}}

    def get_track(self, track_id: str):
        return Track(
            id=track_id,
            name="Fake Track",
            artists=[Artist(id="art-1", name="Fake Artist")],
        )

    def create_playlist(self, user_id, name, description="", public=True, track_uris=None):
        self.create_playlist_called_with.append((user_id, name, description, public, track_uris))
        return {
            "id": "fake-playlist-created",
            "name": name,
            "description": description,
            "owner": user_id,
            "public": public,
            "tracks": [],
            "tracks_total": 0,
            "external_urls": {"spotify": "https://open.spotify.com/playlist/fake-playlist-created"},
            "uri": "spotify:playlist:fake-playlist-created",
            "images": [],
        }

    def close(self) -> None:
        pass