"""
Spotify API client — wraps spotipy with clean typed interfaces.

NOTE: Spotify restricted /audio-features to apps with extended quota (Nov 2024).
We skip that endpoint entirely and rely on track metadata + genre data + Claude's
knowledge of artists/songs for mood analysis.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import spotipy

from src.spotify.models import Artist, RecentlyPlayedSession, Track

logger = logging.getLogger(__name__)

RECENTLY_PLAYED_MAX = 50


class SpotifyClient:
    def __init__(self, sp: spotipy.Spotify) -> None:
        self._sp = sp

    def get_recently_played(self, limit: int = 50) -> RecentlyPlayedSession:
        raw_tracks = self._fetch_recent_raw(limit)
        if not raw_tracks:
            return RecentlyPlayedSession(tracks=[])
        tracks = self._enrich_tracks(raw_tracks)
        logger.info(f"Fetched {len(tracks)} tracks.")
        return RecentlyPlayedSession(tracks=tracks)

    def _fetch_recent_raw(self, limit: int) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        remaining = limit
        cursor: int | None = None
        while remaining > 0:
            batch_size = min(remaining, RECENTLY_PLAYED_MAX)
            kwargs: dict[str, Any] = {"limit": batch_size}
            if cursor:
                kwargs["before"] = cursor
            result = self._sp.current_user_recently_played(**kwargs)
            batch = result.get("items", [])
            if not batch:
                break
            items.extend(batch)
            remaining -= len(batch)
            cursors = result.get("cursors") or {}
            before_cursor = cursors.get("before")
            if not before_cursor:
                break
            cursor = int(before_cursor)
        return items

    def _enrich_tracks(self, raw_items: list[dict[str, Any]]) -> list[Track]:
        tracks: list[Track] = []
        for item in raw_items:
            track_data = item.get("track") or {}
            played_at_str = item.get("played_at")
            track = self._map_track_item(track_data)
            if played_at_str:
                try:
                    track.played_at = datetime.fromisoformat(
                        played_at_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            tracks.append(track)

        # Artist genres — still accessible without extended quota
        artist_ids = list({a.id for t in tracks for a in t.artists if a.id})
        genres_map = self._fetch_artist_genres(artist_ids)
        for track in tracks:
            for artist in track.artists:
                if artist.id in genres_map:
                    artist.genres = genres_map[artist.id]["genres"]
                    artist.popularity = genres_map[artist.id]["popularity"]
        return tracks

    def _fetch_artist_genres(self, artist_ids: list[str]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for i in range(0, len(artist_ids), 50):
            batch = artist_ids[i : i + 50]
            try:
                response = self._sp.artists(batch)
                for artist in response.get("artists") or []:
                    if artist and artist.get("id"):
                        result[artist["id"]] = {
                            "genres": artist.get("genres", []),
                            "popularity": artist.get("popularity", 0),
                        }
            except Exception as e:
                logger.warning(f"Artist genres batch failed: {e}")
        return result

    def _map_track_item(self, item: dict[str, Any]) -> Track:
        artists = [
            Artist(id=a.get("id", ""), name=a.get("name", "Unknown"))
            for a in item.get("artists", [])
        ]
        album = item.get("album", {})
        release_date = album.get("release_date", "")
        release_year: int | None = None
        if release_date:
            try:
                release_year = int(release_date[:4])
            except ValueError:
                pass
        return Track(
            id=item.get("id", ""),
            name=item.get("name", "Unknown"),
            artists=artists,
            album_name=album.get("name", "Unknown"),
            album_release_year=release_year,
            popularity=item.get("popularity", 0),
            explicit=item.get("explicit", False),
        )
