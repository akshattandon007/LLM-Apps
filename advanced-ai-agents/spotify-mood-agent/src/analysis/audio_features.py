"""
Statistical aggregation of Spotify audio features across a track set.
Produces structured summaries fed to the Claude agent.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Optional

from src.spotify.models import RecentlyPlayedSession, Track


@dataclass
class FeatureStats:
    """Descriptive statistics for a single audio feature."""

    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    q1: float  # 25th percentile
    q3: float  # 75th percentile

    @property
    def range(self) -> float:
        return self.max_val - self.min_val

    def to_dict(self) -> dict[str, float]:
        return {
            "mean": round(self.mean, 3),
            "median": round(self.median, 3),
            "std_dev": round(self.std_dev, 3),
            "min": round(self.min_val, 3),
            "max": round(self.max_val, 3),
            "q1": round(self.q1, 3),
            "q3": round(self.q3, 3),
        }


@dataclass
class AudioFeatureSummary:
    """Aggregated audio feature stats for a session."""

    valence: FeatureStats
    energy: FeatureStats
    danceability: FeatureStats
    acousticness: FeatureStats
    instrumentalness: FeatureStats
    speechiness: FeatureStats
    liveness: FeatureStats
    tempo: FeatureStats
    loudness: FeatureStats

    avg_mode: float          # fraction of tracks in Major
    top_genres: list[str]    # top 5 genres by frequency
    track_count: int
    explicit_fraction: float

    # Temporal windows (if timestamps are available)
    first_half_valence: Optional[float] = None
    second_half_valence: Optional[float] = None
    first_half_energy: Optional[float] = None
    second_half_energy: Optional[float] = None

    @property
    def mood_direction(self) -> str:
        """Whether mood appears to be trending up, down, or stable."""
        if self.first_half_valence is None or self.second_half_valence is None:
            return "unknown"
        delta = self.second_half_valence - self.first_half_valence
        if delta > 0.08:
            return "up"
        elif delta < -0.08:
            return "down"
        return "stable"

    def to_dict(self) -> dict:
        return {
            "valence": self.valence.to_dict(),
            "energy": self.energy.to_dict(),
            "danceability": self.danceability.to_dict(),
            "acousticness": self.acousticness.to_dict(),
            "instrumentalness": self.instrumentalness.to_dict(),
            "speechiness": self.speechiness.to_dict(),
            "liveness": self.liveness.to_dict(),
            "tempo": self.tempo.to_dict(),
            "loudness": self.loudness.to_dict(),
            "avg_mode_major_fraction": round(self.avg_mode, 3),
            "top_genres": self.top_genres,
            "track_count": self.track_count,
            "explicit_fraction": round(self.explicit_fraction, 3),
            "temporal": {
                "first_half_valence": self.first_half_valence,
                "second_half_valence": self.second_half_valence,
                "first_half_energy": self.first_half_energy,
                "second_half_energy": self.second_half_energy,
                "mood_direction": self.mood_direction,
            },
        }


def _compute_stats(values: list[float]) -> FeatureStats:
    """Compute descriptive stats for a list of float values."""
    if not values:
        return FeatureStats(0, 0, 0, 0, 0, 0, 0)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    return FeatureStats(
        mean=statistics.mean(values),
        median=statistics.median(values),
        std_dev=statistics.stdev(values) if n > 1 else 0.0,
        min_val=sorted_vals[0],
        max_val=sorted_vals[-1],
        q1=q1,
        q3=q3,
    )


def _top_genres(tracks: list[Track], top_n: int = 5) -> list[str]:
    """Return the most common genres across all tracks."""
    counts: dict[str, int] = {}
    for track in tracks:
        for genre in track.all_genres:
            counts[genre] = counts.get(genre, 0) + 1
    return [g for g, _ in sorted(counts.items(), key=lambda x: -x[1])[:top_n]]


def _half_mean(values: list[float]) -> tuple[Optional[float], Optional[float]]:
    """Split a list in half and return mean of each half."""
    if len(values) < 4:
        return None, None
    mid = len(values) // 2
    return statistics.mean(values[:mid]), statistics.mean(values[mid:])


def analyse_session(session: RecentlyPlayedSession) -> AudioFeatureSummary:
    """
    Compute a full AudioFeatureSummary for a listening session.

    Args:
        session: The recently played session with tracks.

    Returns:
        AudioFeatureSummary with per-feature stats and genre data.
    """
    tracks_with_features = session.tracks_with_features
    if not tracks_with_features:
        raise ValueError("No tracks with audio features found in session.")

    def collect(attr: str) -> list[float]:
        return [getattr(t.audio_features, attr) for t in tracks_with_features]

    valence_vals = collect("valence")
    energy_vals = collect("energy")

    fh_valence, sh_valence = _half_mean(valence_vals)
    fh_energy, sh_energy = _half_mean(energy_vals)

    return AudioFeatureSummary(
        valence=_compute_stats(valence_vals),
        energy=_compute_stats(energy_vals),
        danceability=_compute_stats(collect("danceability")),
        acousticness=_compute_stats(collect("acousticness")),
        instrumentalness=_compute_stats(collect("instrumentalness")),
        speechiness=_compute_stats(collect("speechiness")),
        liveness=_compute_stats(collect("liveness")),
        tempo=_compute_stats(collect("tempo")),
        loudness=_compute_stats(collect("loudness")),
        avg_mode=statistics.mean(
            [t.audio_features.mode for t in tracks_with_features]  # type: ignore[union-attr]
        ),
        top_genres=_top_genres(tracks_with_features),
        track_count=len(tracks_with_features),
        explicit_fraction=sum(1 for t in tracks_with_features if t.explicit)
        / len(tracks_with_features),
        first_half_valence=fh_valence,
        second_half_valence=sh_valence,
        first_half_energy=fh_energy,
        second_half_energy=sh_energy,
    )
