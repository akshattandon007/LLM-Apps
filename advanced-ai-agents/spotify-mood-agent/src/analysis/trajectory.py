"""
Temporal mood arc detection.
Analyses how valence and energy evolve over the listening session.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.spotify.models import Track


@dataclass
class TrajectoryPoint:
    """Mood snapshot at a point in the session."""
    position: int       # Track index (0 = most recent)
    valence: float
    energy: float
    track_name: str


@dataclass
class MoodTrajectory:
    """Full temporal mood arc for a session."""

    points: list[TrajectoryPoint]
    valence_trend: float     # Positive = increasing valence over time
    energy_trend: float      # Positive = increasing energy over time
    direction: str           # "up", "down", "stable", "volatile"
    arc_label: str           # Human-readable arc description
    volatility: float        # Std dev of valence deltas

    def to_dict(self) -> dict:
        return {
            "valence_trend": round(self.valence_trend, 4),
            "energy_trend": round(self.energy_trend, 4),
            "direction": self.direction,
            "arc_label": self.arc_label,
            "volatility": round(self.volatility, 4),
            "sample_points": [
                {
                    "position": p.position,
                    "valence": round(p.valence, 3),
                    "energy": round(p.energy, 3),
                    "track": p.track_name,
                }
                for p in self.points[::max(1, len(self.points) // 5)]  # 5 sample points
            ],
        }


def _linear_slope(values: list[float]) -> float:
    """Simple least-squares slope for a sequence of values."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _volatility(values: list[float]) -> float:
    """Mean absolute delta between consecutive values."""
    if len(values) < 2:
        return 0.0
    deltas = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
    return sum(deltas) / len(deltas)


def _arc_label(direction: str, valence_slope: float, energy_slope: float) -> str:
    """Generate a human-readable arc description."""
    labels = {
        ("up", True, True): "Brightening energy and mood",
        ("up", True, False): "Gradually lifting spirits",
        ("up", False, True): "Building energy",
        ("down", True, False): "Reflective wind-down",
        ("down", False, True): "Growing intensity",
        ("down", False, False): "Deepening introspection",
        ("stable", True, True): "Consistently upbeat",
        ("stable", False, False): "Consistently melancholic",
        ("volatile", True, True): "Emotionally unpredictable",
    }
    key = (direction, valence_slope > 0, energy_slope > 0)
    return labels.get(key, "Varied emotional journey")


def compute_trajectory(tracks: list[Track]) -> Optional[MoodTrajectory]:
    """
    Compute the mood trajectory across a list of tracks.

    Tracks should be in reverse-chronological order (most recent first),
    as returned by Spotify's recently played endpoint.
    We reverse them internally for chronological analysis.

    Returns None if insufficient data.
    """
    tracks_with_features = [t for t in tracks if t.audio_features]
    if len(tracks_with_features) < 3:
        return None

    # Reverse to chronological order (oldest first)
    chronological = list(reversed(tracks_with_features))

    points = [
        TrajectoryPoint(
            position=i,
            valence=t.audio_features.valence,  # type: ignore[union-attr]
            energy=t.audio_features.energy,    # type: ignore[union-attr]
            track_name=t.display_name,
        )
        for i, t in enumerate(chronological)
    ]

    valence_vals = [p.valence for p in points]
    energy_vals = [p.energy for p in points]

    v_slope = _linear_slope(valence_vals)
    e_slope = _linear_slope(energy_vals)
    vol = _volatility(valence_vals)

    # Classify direction
    if vol > 0.15:
        direction = "volatile"
    elif abs(v_slope) < 0.002:
        direction = "stable"
    elif v_slope > 0:
        direction = "up"
    else:
        direction = "down"

    return MoodTrajectory(
        points=points,
        valence_trend=v_slope,
        energy_trend=e_slope,
        direction=direction,
        arc_label=_arc_label(direction, v_slope, e_slope),
        volatility=vol,
    )
