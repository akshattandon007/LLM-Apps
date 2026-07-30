"""
Pydantic models for Spotify API responses and internal data structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AudioFeatures(BaseModel):
    """Spotify audio features for a single track."""

    track_id: str
    danceability: float = Field(ge=0, le=1, description="How suitable for dancing (0–1)")
    energy: float = Field(ge=0, le=1, description="Perceptual intensity and activity (0–1)")
    key: int = Field(ge=-1, le=11, description="Estimated key (-1 = no key detected)")
    loudness: float = Field(description="Overall loudness in dB (typically -60 to 0)")
    mode: int = Field(ge=0, le=1, description="Modality: 1=Major, 0=Minor")
    speechiness: float = Field(ge=0, le=1, description="Presence of spoken words (0–1)")
    acousticness: float = Field(ge=0, le=1, description="Confidence of acoustic sound (0–1)")
    instrumentalness: float = Field(ge=0, le=1, description="No vocal content confidence (0–1)")
    liveness: float = Field(ge=0, le=1, description="Live audience detection (0–1)")
    valence: float = Field(ge=0, le=1, description="Musical positiveness / happiness (0–1)")
    tempo: float = Field(ge=0, description="Estimated tempo in BPM")
    duration_ms: int = Field(ge=0, description="Track duration in milliseconds")
    time_signature: int = Field(ge=1, description="Estimated time signature (beats per bar)")

    @property
    def mood_score(self) -> float:
        """Composite mood score weighted by valence and energy."""
        return (self.valence * 0.6) + (self.energy * 0.4)

    @property
    def is_major(self) -> bool:
        return self.mode == 1

    @property
    def duration_minutes(self) -> float:
        return self.duration_ms / 60_000


class Artist(BaseModel):
    """Spotify artist summary."""

    id: str
    name: str
    genres: list[str] = Field(default_factory=list)
    popularity: int = Field(ge=0, le=100, default=0)


class Track(BaseModel):
    """A single Spotify track with metadata."""

    id: str
    name: str
    artists: list[Artist]
    album_name: str
    album_release_year: Optional[int] = None
    popularity: int = Field(ge=0, le=100, default=0)
    explicit: bool = False
    audio_features: Optional[AudioFeatures] = None
    played_at: Optional[datetime] = None

    @property
    def primary_artist(self) -> str:
        return self.artists[0].name if self.artists else "Unknown"

    @property
    def all_genres(self) -> list[str]:
        genres: list[str] = []
        for artist in self.artists:
            genres.extend(artist.genres)
        return list(dict.fromkeys(genres))  # deduplicated, order preserved

    @property
    def display_name(self) -> str:
        return f"{self.name} — {self.primary_artist}"


class RecentlyPlayedSession(BaseModel):
    """A collection of recently played tracks with session metadata."""

    tracks: list[Track]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def total_duration_minutes(self) -> float:
        return sum(
            t.audio_features.duration_minutes
            for t in self.tracks
            if t.audio_features
        )

    @property
    def time_span_hours(self) -> Optional[float]:
        timestamps = [t.played_at for t in self.tracks if t.played_at]
        if len(timestamps) < 2:
            return None
        delta = max(timestamps) - min(timestamps)
        return delta.total_seconds() / 3600

    @property
    def tracks_with_features(self) -> list[Track]:
        return [t for t in self.tracks if t.audio_features is not None]


class MoodReport(BaseModel):
    """Final mood analysis output from the agent."""

    primary_mood: str
    confidence: float = Field(ge=0, le=1)
    energy_level: float = Field(ge=0, le=10)
    emotional_arc: str  # e.g. "gradually brightening", "stable melancholy"
    arc_direction: str  # "up", "down", "stable"

    # Audio feature summaries (0–1 scale)
    avg_valence: float
    avg_energy: float
    avg_danceability: float
    avg_acousticness: float
    avg_instrumentalness: float
    avg_tempo: float

    top_genres: list[str]
    dominant_mode: str  # "major" or "minor"

    insight: str  # Paragraph narrative
    recommendations: list[str]  # 2–3 song recommendations

    tracks_analysed: int
    session_duration_hours: Optional[float] = None

    @field_validator("confidence")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(v, 2)
