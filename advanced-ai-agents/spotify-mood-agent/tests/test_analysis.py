"""
Tests for audio feature analysis and trajectory detection.
"""

import pytest

from src.analysis.audio_features import analyse_session, _compute_stats, _top_genres
from src.analysis.trajectory import compute_trajectory, _linear_slope, _volatility
from src.spotify.models import Artist, AudioFeatures, RecentlyPlayedSession, Track
from tests.fixtures.mock_spotify import MOCK_AUDIO_FEATURES


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_track(
    track_id: str,
    name: str,
    valence: float,
    energy: float,
    genres: list[str] | None = None,
) -> Track:
    af = AudioFeatures(
        track_id=track_id,
        danceability=0.5,
        energy=energy,
        key=5,
        loudness=-10.0,
        mode=1,
        speechiness=0.03,
        acousticness=0.5,
        instrumentalness=0.0,
        liveness=0.1,
        valence=valence,
        tempo=120.0,
        duration_ms=200_000,
        time_signature=4,
    )
    artist = Artist(id="a1", name="Test Artist", genres=genres or [])
    return Track(id=track_id, name=name, artists=[artist], album_name="Test Album", audio_features=af)


def make_session(tracks: list[Track]) -> RecentlyPlayedSession:
    return RecentlyPlayedSession(tracks=tracks)


# ─── AudioFeatures tests ─────────────────────────────────────────────────────

class TestComputeStats:
    def test_basic_stats(self):
        stats = _compute_stats([0.1, 0.3, 0.5, 0.7, 0.9])
        assert abs(stats.mean - 0.5) < 0.01
        assert stats.min_val == 0.1
        assert stats.max_val == 0.9
        assert stats.std_dev > 0

    def test_single_value(self):
        stats = _compute_stats([0.4])
        assert stats.mean == 0.4
        assert stats.std_dev == 0.0

    def test_empty_returns_zeros(self):
        stats = _compute_stats([])
        assert stats.mean == 0


class TestTopGenres:
    def test_returns_most_common(self):
        tracks = [
            make_track("t1", "A", 0.5, 0.5, ["indie folk", "lo-fi"]),
            make_track("t2", "B", 0.5, 0.5, ["indie folk", "pop"]),
            make_track("t3", "C", 0.5, 0.5, ["lo-fi"]),
        ]
        genres = _top_genres(tracks)
        assert genres[0] == "indie folk"  # appears twice
        assert "lo-fi" in genres

    def test_respects_limit(self):
        tracks = [make_track(f"t{i}", f"T{i}", 0.5, 0.5, [f"genre{i}"]) for i in range(20)]
        genres = _top_genres(tracks, top_n=5)
        assert len(genres) <= 5


class TestAnalyseSession:
    def test_basic_analysis(self):
        tracks = [
            make_track("t1", "Happy", 0.8, 0.7, ["pop"]),
            make_track("t2", "Sad", 0.2, 0.3, ["indie folk"]),
            make_track("t3", "Mid", 0.5, 0.5, ["pop"]),
        ]
        session = make_session(tracks)
        summary = analyse_session(session)
        assert abs(summary.valence.mean - 0.5) < 0.05
        assert summary.track_count == 3

    def test_no_features_raises(self):
        track = Track(id="t1", name="T", artists=[], album_name="A")
        session = make_session([track])
        with pytest.raises(ValueError):
            analyse_session(session)

    def test_temporal_split(self):
        # First half sad, second half happy
        tracks = [
            make_track("t1", "A", 0.8, 0.5),
            make_track("t2", "B", 0.7, 0.5),
            make_track("t3", "C", 0.2, 0.5),
            make_track("t4", "D", 0.3, 0.5),
        ]
        session = make_session(tracks)
        summary = analyse_session(session)
        # first_half_valence should be > second_half_valence (older tracks = higher indices)
        assert summary.first_half_valence is not None
        assert summary.second_half_valence is not None


# ─── Trajectory tests ─────────────────────────────────────────────────────────

class TestLinearSlope:
    def test_increasing(self):
        assert _linear_slope([0.1, 0.3, 0.5, 0.7, 0.9]) > 0

    def test_decreasing(self):
        assert _linear_slope([0.9, 0.7, 0.5, 0.3, 0.1]) < 0

    def test_flat(self):
        assert _linear_slope([0.5, 0.5, 0.5, 0.5]) == 0.0

    def test_single_value(self):
        assert _linear_slope([0.5]) == 0.0


class TestVolatility:
    def test_stable(self):
        assert _volatility([0.5, 0.5, 0.5]) == 0.0

    def test_volatile(self):
        assert _volatility([0.1, 0.9, 0.1, 0.9]) > 0.5

    def test_single(self):
        assert _volatility([0.5]) == 0.0


class TestComputeTrajectory:
    def test_returns_none_for_too_few_tracks(self):
        tracks = [make_track("t1", "A", 0.5, 0.5)]
        assert compute_trajectory(tracks) is None

    def test_upward_arc(self):
        # Tracks in reverse-chron order (most recent first).
        # Chronologically: a gradual increase from 0.2 to 0.5 (10 steps).
        # Small, steady deltas stay below the volatility threshold (0.15).
        n = 10
        vals = [0.2 + i * 0.03 for i in range(n)]  # 0.20 … 0.47, step 0.03
        tracks = [make_track(f"t{i}", f"T{i}", vals[i], 0.5) for i in range(n - 1, -1, -1)]
        traj = compute_trajectory(tracks)
        assert traj is not None
        assert traj.direction == "up"

    def test_downward_arc(self):
        # Chronologically: a gradual decline from 0.5 to 0.2 (10 steps).
        n = 10
        vals = [0.5 - i * 0.03 for i in range(n)]  # 0.50 … 0.23, step 0.03
        tracks = [make_track(f"t{i}", f"T{i}", vals[i], 0.5) for i in range(n - 1, -1, -1)]
        traj = compute_trajectory(tracks)
        assert traj is not None
        assert traj.direction == "down"

    def test_volatile_arc(self):
        tracks = [
            make_track(f"t{i}", f"T{i}", v, 0.5)
            for i, v in enumerate([0.9, 0.1, 0.9, 0.1, 0.9, 0.1])
        ]
        traj = compute_trajectory(tracks)
        assert traj is not None
        assert traj.direction == "volatile"

    def test_to_dict_structure(self):
        tracks = [make_track(f"t{i}", f"T{i}", 0.5, 0.5) for i in range(5)]
        traj = compute_trajectory(tracks)
        assert traj is not None
        d = traj.to_dict()
        assert "valence_trend" in d
        assert "direction" in d
        assert "arc_label" in d
        assert "sample_points" in d
