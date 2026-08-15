"""Pytest fixtures for Spotify DJ tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from src.spotify_client import FakeSpotifyClient


@pytest.fixture
def fake_client() -> Generator[FakeSpotifyClient, None, None]:
    """Provide a fresh FakeSpotifyClient for each test."""
    client = FakeSpotifyClient()
    yield client
    # No cleanup needed for fake client