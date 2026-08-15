"""Pydantic models for Spotify data structures."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Artist(BaseModel):
    """A Spotify artist."""

    id: str
    name: str
    genres: list[str] = Field(default_factory=list)
    popularity: int = 0
    followers: int = 0
    images: list[dict[str, Any]] = Field(default_factory=list)
    external_urls: dict[str, str] = Field(default_factory=dict)


class Album(BaseModel):
    """A Spotify album."""

    id: str
    name: str
    artists: list[Artist] = Field(default_factory=list)
    release_date: str = ""
    total_tracks: int = 0
    images: list[dict[str, Any]] = Field(default_factory=list)
    external_urls: dict[str, str] = Field(default_factory=dict)
    album_type: str = "album"
    uri: str = ""


class Track(BaseModel):
    """A Spotify track with optional audio features."""

    id: str
    name: str
    artists: list[Artist] = Field(default_factory=list)
    album: Optional[Album] = None
    duration_ms: int = 0
    popularity: int = 0
    explicit: bool = False
    uri: str = ""
    external_urls: dict[str, str] = Field(default_factory=dict)
    preview_url: Optional[str] = None

    # Audio features (populated by describe_track)
    bpm: Optional[float] = None
    key: Optional[int] = None
    key_name: Optional[str] = None
    mode: Optional[int] = None  # 0 = minor, 1 = major
    energy: Optional[float] = None
    valence: Optional[float] = None
    danceability: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    speechiness: Optional[float] = None
    loudness: Optional[float] = None

    @property
    def duration_formatted(self) -> str:
        """Human-readable duration: MM:SS."""
        seconds = self.duration_ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"

    @property
    def artist_names(self) -> str:
        """Comma-separated artist names."""
        return ", ".join(a.name for a in self.artists)

    @property
    def key_mode(self) -> str:
        """Musical key and mode, e.g. 'C major' or 'A minor'."""
        key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        if self.key is None:
            return "Unknown"
        name = key_names[self.key] if 0 <= self.key < 12 else "?"
        mode_str = "major" if self.mode == 1 else "minor"
        return f"{name} {mode_str}"


class Playlist(BaseModel):
    """A Spotify playlist."""

    id: str
    name: str
    description: str = ""
    owner: str = ""
    public: bool = True
    tracks: list[Track] = Field(default_factory=list)
    tracks_total: int = 0
    external_urls: dict[str, str] = Field(default_factory=dict)
    uri: str = ""
    images: list[dict[str, Any]] = Field(default_factory=dict)


class RecommendationParams(BaseModel):
    """Parameters for Spotify recommendation requests."""

    seed_tracks: list[str] = Field(default_factory=list)
    seed_artists: list[str] = Field(default_factory=list)
    seed_genres: list[str] = Field(default_factory=list)
    target_energy: Optional[float] = None
    target_valence: Optional[float] = None
    target_bpm: Optional[float] = None
    target_danceability: Optional[float] = None
    target_acousticness: Optional[float] = None
    target_instrumentalness: Optional[float] = None
    limit: int = 20