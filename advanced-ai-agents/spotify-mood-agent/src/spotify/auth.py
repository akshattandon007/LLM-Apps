"""
Spotify OAuth2 authentication using spotipy.
Handles token acquisition, caching, and refresh.
"""

from __future__ import annotations

import os
from pathlib import Path

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Scopes required by the agent
REQUIRED_SCOPES = " ".join([
    "user-read-recently-played",
    "user-read-currently-playing",
    "user-top-read",
    "user-read-private",
])


def get_spotify_client(cache_path: str | Path = ".spotify_token_cache") -> spotipy.Spotify:
    """
    Create and return an authenticated Spotify client.

    Uses Authorization Code Flow with PKCE-style PKCE-ready cache.
    On first run, opens a browser for user authorisation.
    Subsequent runs use the cached token (auto-refreshed).

    Args:
        cache_path: Path to store the OAuth token cache.

    Returns:
        Authenticated spotipy.Spotify client.

    Raises:
        EnvironmentError: If required env vars are missing.
        spotipy.SpotifyException: If authentication fails.
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID and "
            "SPOTIFY_CLIENT_SECRET in your .env file.\n"
            "Get credentials at: https://developer.spotify.com/dashboard"
        )

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=REQUIRED_SCOPES,
        cache_path=str(cache_path),
        open_browser=True,
    )

    return spotipy.Spotify(auth_manager=auth_manager)


def check_auth_status(client: spotipy.Spotify) -> dict[str, str]:
    """
    Verify auth works and return basic user info.

    Returns:
        Dict with display_name, email, country, product (free/premium).
    """
    me = client.me()
    return {
        "display_name": me.get("display_name", "Unknown"),
        "id": me.get("id", ""),
        "country": me.get("country", ""),
        "product": me.get("product", "unknown"),
    }
