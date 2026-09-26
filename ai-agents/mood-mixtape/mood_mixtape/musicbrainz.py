"""MusicBrainz API client — free, zero-auth music metadata."""

from __future__ import annotations

import json
import time
from typing import Optional

import httpx

from .models import Track

MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "MoodMixtape/0.1.0 (akshattandon4@gmail.com)"

# Rate limiting: MusicBrainz allows 1 request per second
_MINIMUM_INTERVAL = 1.0  # seconds
_last_request_time: float = 0.0

_client: Optional[httpx.Client] = None


def set_client(client: Optional[httpx.Client]) -> None:
    """Inject a test client. Pass None to reset to real HTTP."""
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client()


def _rate_limit() -> None:
    """Ensure we don't exceed MusicBrainz rate limits."""
    global _last_request_time
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < _MINIMUM_INTERVAL:
        time.sleep(_MINIMUM_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def _get(endpoint: str, params: dict) -> dict:
    """Make a rate-limited GET request to MusicBrainz."""
    _rate_limit()
    url = f"{MUSICBRAINZ_BASE}/{endpoint}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    client = _get_client()
    response = client.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def search_recordings(query: str, limit: int = 25) -> list[Track]:
    """Search MusicBrainz for recordings matching a query.

    Args:
        query: Search query (artist, song title, genre, mood keywords).
        limit: Max results (MusicBrainz max is 100).

    Returns:
        List of Track objects from MusicBrainz.
    """
    data = _get(
        "recording",
        {"query": query, "limit": min(limit, 100), "fmt": "json"},
    )
    tracks: list[Track] = []
    for recording in data.get("recordings", []):
        title = recording.get("title", "Unknown Title")
        # Get the first artist credit
        artist_credits = recording.get("artist-credit", [])
        if artist_credits and isinstance(artist_credits[0], dict):
            artist_name = artist_credits[0].get("name", "Unknown Artist")
        else:
            artist_name = "Unknown Artist"
        # Get release title
        releases = recording.get("releases", [])
        release_title = releases[0].get("title") if releases else None
        tracks.append(
            Track(
                title=title,
                artist=artist_name,
                release=release_title,
                recording_id=recording.get("id"),
            )
        )
    return tracks


def get_popular_tracks(limit: int = 50) -> list[Track]:
    """Fetch currently popular tracks via tag-based query.

    Uses 'tag:popular' to get a broad set of currently popular recordings.
    This is a best-effort approach since MusicBrainz doesn't have a
    dedicated 'trending' endpoint.
    """
    # Search by star ratings and popularity tags
    tracks = search_recordings("tag:popular", limit=limit)
    if len(tracks) < limit:
        # Fallback: broad genre search
        more_tracks = search_recordings("tag:rock OR tag:pop OR tag:electronic", limit=limit - len(tracks))
        tracks.extend(more_tracks)
    return tracks


def search_by_mood_keywords(keywords: list[str], limit: int = 30) -> list[Track]:
    """Search MusicBrainz using mood keywords (e.g. 'happy', 'melancholy', 'energetic').

    Uses MusicBrainz tags and artist/recording names for mood-based discovery.

    Args:
        keywords: List of mood/emotion keywords.
        limit: Max results.

    Returns:
        Deduplicated list of Track objects.
    """
    all_tracks: list[Track] = []
    seen: set[str] = set()

    for keyword in keywords:
        for query in [
            f"tag:{keyword} AND tag:recording",
            keyword,
        ]:
            try:
                results = search_recordings(query, limit=max(10, limit // len(keywords)))
                for track in results:
                    key = f"{track.title}|{track.artist}"
                    if key not in seen:
                        seen.add(key)
                        all_tracks.append(track)
            except Exception:
                continue

    return all_tracks[:limit]