"""Data models for Mood Mixtape."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Track:
    """A single track from MusicBrainz."""

    title: str
    artist: str
    release: Optional[str] = None
    recording_id: Optional[str] = None
    source: str = "live"


@dataclass
class MixtapeSong:
    """A curated song in the final mixtape."""

    title: str
    artist: str
    why_it_fits: str  # LLM-generated explanation of why this song matches the mood


@dataclass
class Mixtape:
    """The final curated mixtape output."""

    mood: str
    mood_description: str
    playlist_name: str
    cover_art_description: str  # DALL-E prompt for cover art
    vibe_description: str
    songs: list[MixtapeSong] = field(default_factory=list)
    total_duration_minutes: Optional[int] = None