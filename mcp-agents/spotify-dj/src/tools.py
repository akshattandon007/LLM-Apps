"""MCP tool definitions for the Spotify DJ agent.

Uses a module-level _client singleton (set via setup()) for testability.
All tools are async functions decorated with @server.tool().
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.models import RecommendationParams
from src.spotify_client import FakeSpotifyClient, SpotifyClient

logger = logging.getLogger(__name__)

# Module-level client singleton — injected by setup()
_client: SpotifyClient | FakeSpotifyClient | None = None


def setup(client: SpotifyClient | FakeSpotifyClient | None = None) -> None:
    """Initialize the module-level client.

    Call once at startup with a real or fake client. Real clients
    read credentials from the environment automatically.
    """
    global _client
    if client is not None:
        _client = client
    else:
        _client = SpotifyClient()
    logger.info("Spotify client initialized: %s", type(_client).__name__)


def _get_client() -> SpotifyClient | FakeSpotifyClient:
    """Get the current client, raising if not initialized."""
    if _client is None:
        raise RuntimeError(
            "Spotify client not initialized. Call setup() first."
        )
    return _client


# ── MCP Tool definitions ──────────────────────────────────────────────

def register_tools(server: Any) -> None:
    """Register all MCP tools on the given server instance.

    Each tool is a decorated async function on the server.
    """

    @server.tool()
    async def search_tracks(
        query: str,
        limit: int = 10,
    ) -> str:
        """Search Spotify for tracks, albums, and artists by keyword.

        Args:
            query: Search query (track name, artist, album).
            limit: Maximum results to return (default 10, max 50).
        """
        client = _get_client()
        results = client.search_tracks(query, limit=limit)
        return _format_search_results(results)

    @server.tool()
    async def get_recommendations(
        seed_tracks: Optional[list[str]] = None,
        seed_artists: Optional[list[str]] = None,
        seed_genres: Optional[list[str]] = None,
        target_energy: Optional[float] = None,
        target_valence: Optional[float] = None,
        target_bpm: Optional[float] = None,
        target_danceability: Optional[float] = None,
        target_acousticness: Optional[float] = None,
        target_instrumentalness: Optional[float] = None,
        limit: int = 20,
    ) -> str:
        """Get AI-curated track recommendations based on seeds + audio targets.

        Args:
            seed_tracks: List of Spotify track IDs to seed recommendations.
            seed_artists: List of Spotify artist IDs to seed recommendations.
            seed_genres: List of genre seeds (e.g. ['ambient', 'electronic']).
            target_energy: Target energy level (0.0 to 1.0).
            target_valence: Target valence / mood (0.0 sad to 1.0 happy).
            target_bpm: Target BPM / tempo.
            target_danceability: Target danceability (0.0 to 1.0).
            target_acousticness: Target acousticness (0.0 to 1.0).
            target_instrumentalness: Target instrumentalness (0.0 to 1.0).
            limit: Maximum number of recommendations (default 20, max 100).
        """
        client = _get_client()
        results = client.get_recommendations(
            seed_tracks=seed_tracks or [],
            seed_artists=seed_artists or [],
            seed_genres=seed_genres or [],
            target_energy=target_energy,
            target_valence=target_valence,
            target_bpm=target_bpm,
            target_danceability=target_danceability,
            target_acousticness=target_acousticness,
            target_instrumentalness=target_instrumentalness,
            limit=limit,
        )
        return _format_recommendations(results)

    @server.tool()
    async def get_new_releases(
        limit: int = 10,
        country: str = "US",
    ) -> str:
        """Get the latest album releases on Spotify.

        Args:
            limit: Maximum number of releases (default 10, max 50).
            country: ISO 3166-1 alpha-2 country code (default 'US').
        """
        client = _get_client()
        results = client.get_new_releases(limit=limit, country=country)
        return _format_new_releases(results)

    @server.tool()
    async def get_artist_top_tracks(
        artist_id: str,
        market: str = "US",
    ) -> str:
        """Get an artist's top tracks by market.

        Args:
            artist_id: Spotify artist ID (e.g. '4tZwfgrHOc3mvqYlEYSvVi').
            market: ISO 3166-1 alpha-2 country code (default 'US').
        """
        client = _get_client()
        results = client.get_artist_top_tracks(artist_id, market=market)
        return _format_track_list(results, f"Top Tracks")

    @server.tool()
    async def describe_track(track_id: str) -> str:
        """Get detailed audio features for a track — BPM, key, energy, valence, etc.

        Args:
            track_id: Spotify track ID (e.g. '11dFghVXANMlKmJXsNCbNl').
        """
        client = _get_client()
        result = client.describe_track(track_id)
        return _format_track_description(result)

    @server.tool()
    async def get_playlist(playlist_id: str) -> str:
        """Get a Spotify playlist's details and tracks.

        Args:
            playlist_id: Spotify playlist ID (e.g. '37i9dQZF1DXcBWIGoYBM5M').
        """
        client = _get_client()
        result = client.get_playlist(playlist_id)
        return _format_playlist(result)

    @server.tool()
    async def create_playlist(
        name: str,
        description: str = "",
        track_uris: Optional[list[str]] = None,
        user_id: str = "",
    ) -> str:
        """Create a new Spotify playlist.

        NOTE: This write operation requires user-level Spotify authorization
        (OAuth auth-code flow), not just client credentials.

        Args:
            name: Playlist name.
            description: Optional playlist description.
            track_uris: List of Spotify track URIs to add (e.g. ['spotify:track:...']).
            user_id: Spotify user ID for the playlist owner.
        """
        client = _get_client()
        result = client.create_playlist(
            user_id=user_id or "me",
            name=name,
            description=description,
            track_uris=track_uris or [],
        )
        return _format_playlist(result)


# ── Formatting helpers ─────────────────────────────────────────────────


def _format_search_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No results found."

    lines = [f"Found {len(results)} result(s):\n"]
    for i, item in enumerate(results, 1):
        kind = item.get("type", "?")
        data = item.get("data", {})
        if kind == "track":
            artists = ", ".join(a.get("name", "?") for a in data.get("artists", []))
            album = data.get("album", {}).get("name", "?")
            lines.append(
                f"{i}. [TRACK] {data.get('name', '?')} "
                f"by {artists} — {album}"
            )
        elif kind == "artist":
            genres = ", ".join(data.get("genres", [])) or "N/A"
            lines.append(
                f"{i}. [ARTIST] {data.get('name', '?')} "
                f"(popularity: {data.get('popularity', '?')}, genres: {genres})"
            )
        elif kind == "album":
            artists = ", ".join(a.get("name", "?") for a in data.get("artists", []))
            lines.append(
                f"{i}. [ALBUM] {data.get('name', '?')} "
                f"by {artists} ({data.get('release_date', '?')})"
            )
    return "\n".join(lines)


def _format_recommendations(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No recommendations found. Try different seed parameters."

    lines = [f"🎧 {len(results)} recommendations:\n"]
    for i, item in enumerate(results, 1):
        data = item.get("data", {})
        artists = ", ".join(a.get("name", "?") for a in data.get("artists", []))
        album = data.get("album", {}).get("name", "?")
        dur = data.get("duration_ms", 0) // 1000
        dur_str = f"{dur // 60}:{dur % 60:02d}"
        pop = data.get("popularity", "?")
        lines.append(
            f"{i}. {data.get('name', '?')} — {artists}\n"
            f"   Album: {album} | {dur_str} | Popularity: {pop}"
        )
    return "\n".join(lines)


def _format_new_releases(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No new releases found."

    lines = [f"🆕 {len(results)} new releases:\n"]
    for i, item in enumerate(results, 1):
        data = item.get("data", {})
        artists = ", ".join(a.get("name", "?") for a in data.get("artists", []))
        lines.append(
            f"{i}. {data.get('name', '?')} — {artists}\n"
            f"   Released: {data.get('release_date', '?')} | "
            f"Tracks: {data.get('total_tracks', '?')}"
        )
    return "\n".join(lines)


def _format_track_list(
    results: list[dict[str, Any]], label: str = "Tracks"
) -> str:
    if not results:
        return f"No {label.lower()} found."

    lines = [f"🎵 {label} ({len(results)}):\n"]
    for i, item in enumerate(results, 1):
        data = item.get("data", {})
        artists = ", ".join(a.get("name", "?") for a in data.get("artists", []))
        dur = data.get("duration_ms", 0) // 1000
        dur_str = f"{dur // 60}:{dur % 60:02d}"
        lines.append(
            f"{i}. {data.get('name', '?')} — {artists} [{dur_str}]"
        )
    return "\n".join(lines)


def _format_track_description(result: dict[str, Any]) -> str:
    audio = result.get("audio_features", {})
    artists = ", ".join(a.get("name", "?") for a in result.get("artists", [])) if result.get("artists") else "?"
    dur = result.get("duration_ms", 0) // 1000
    dur_str = f"{dur // 60}:{dur % 60:02d}"

    lines = [
        f"🎵 {result.get('name', '?')} — {artists}",
        f"   Duration: {dur_str}",
        f"   Popularity: {result.get('popularity', '?')}",
        f"   Explicit: {'Yes' if result.get('explicit') else 'No'}",
        "",
        "📊 Audio Features:",
        f"   BPM:       {audio.get('bpm', '?')}",
        f"   Key:       {audio.get('key', '?')} {audio.get('mode', '?')}",
        f"   Energy:    {audio.get('energy', '?'):.3f}",
        f"   Valence:   {audio.get('valence', '?'):.3f}",
        f"   Dance:     {audio.get('danceability', '?'):.3f}",
        f"   Acoustic:  {audio.get('acousticness', '?'):.3f}",
        f"   Instru:    {audio.get('instrumentalness', '?'):.3f}",
        f"   Speech:    {audio.get('speechiness', '?'):.3f}",
        f"   Loudness:  {audio.get('loudness', '?'):.2f} dB",
    ]
    return "\n".join(lines)


def _format_playlist(result: dict[str, Any]) -> str:
    tracks = result.get("tracks", [])
    lines = [
        f"📋 {result.get('name', '?')}",
        f"   By: {result.get('owner', '?')}",
        f"   Description: {result.get('description', 'N/A')}",
        f"   Public: {'Yes' if result.get('public') else 'No'}",
        f"   Tracks: {result.get('tracks_total', len(tracks))}",
        f"   URL: {result.get('external_urls', {}).get('spotify', 'N/A')}",
        "",
        "🎵 Tracklist:",
    ]
    if not tracks:
        lines.append("   (empty)")
    else:
        for i, track in enumerate(tracks, 1):
            artists = ", ".join(a.get("name", "?") for a in track.get("artists", [])) if track.get("artists") else "?"
            lines.append(f"   {i}. {track.get('name', '?')} — {artists}")
    return "\n".join(lines)