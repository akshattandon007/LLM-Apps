"""
Tests for the mood agent tool executor.
Tests the tool execution logic without making real Claude API calls.
"""

import json
from unittest.mock import MagicMock

import pytest

from src.agent.tools import ToolExecutor
from src.analysis.audio_features import analyse_session
from src.analysis.trajectory import compute_trajectory
from src.spotify.models import Artist, AudioFeatures, RecentlyPlayedSession, Track


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_full_track(i: int, valence: float, energy: float) -> Track:
    af = AudioFeatures(
        track_id=f"t{i}",
        danceability=0.5,
        energy=energy,
        key=5,
        loudness=-10.0,
        mode=0,
        speechiness=0.03,
        acousticness=0.7,
        instrumentalness=0.01,
        liveness=0.1,
        valence=valence,
        tempo=100.0,
        duration_ms=210_000,
        time_signature=4,
    )
    artist = Artist(
        id=f"a{i}",
        name=f"Artist {i}",
        genres=["lo-fi", "indie folk"] if i % 2 == 0 else ["ambient"],
        popularity=60,
    )
    return Track(
        id=f"t{i}",
        name=f"Track {i}",
        artists=[artist],
        album_name="Album",
        album_release_year=2020,
        audio_features=af,
        explicit=False,
    )


def make_test_executor(n_tracks: int = 8) -> ToolExecutor:
    tracks = [make_full_track(i, valence=0.2 + i * 0.08, energy=0.3 + i * 0.05) for i in range(n_tracks)]
    session = RecentlyPlayedSession(tracks=tracks)
    summary = analyse_session(session)
    trajectory = compute_trajectory(tracks)
    return ToolExecutor(session, summary, trajectory)


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestToolExecutor:

    def test_get_track_list(self):
        executor = make_test_executor()
        result_str = executor.execute("get_track_list", {"limit": 5})
        result = json.loads(result_str)
        assert isinstance(result, list)
        assert len(result) == 5
        assert result[0]["name"] == "Track 0"
        assert "audio_features" not in result[0]  # should not include raw features

    def test_get_track_list_full(self):
        executor = make_test_executor(8)
        result_str = executor.execute("get_track_list", {})
        result = json.loads(result_str)
        assert len(result) == 8

    def test_get_audio_feature_stats(self):
        executor = make_test_executor()
        result_str = executor.execute("get_audio_feature_stats", {})
        result = json.loads(result_str)
        assert "valence" in result
        assert "energy" in result
        assert "top_genres" in result
        assert "track_count" in result
        assert result["track_count"] == 8

    def test_get_mood_trajectory(self):
        executor = make_test_executor(6)
        result_str = executor.execute("get_mood_trajectory", {})
        result = json.loads(result_str)
        assert "direction" in result
        assert "arc_label" in result
        assert "valence_trend" in result

    def test_get_genre_analysis(self):
        executor = make_test_executor()
        result_str = executor.execute("get_genre_analysis", {})
        result = json.loads(result_str)
        assert "genre_breakdown" in result
        assert "total_unique_genres" in result
        genres = [g["genre"] for g in result["genre_breakdown"]]
        assert "lo-fi" in genres or "indie folk" in genres

    def test_get_track_deep_dive(self):
        executor = make_test_executor()
        result_str = executor.execute("get_track_deep_dive", {"limit": 3})
        result = json.loads(result_str)
        assert len(result) == 3
        assert "audio_features" in result[0]
        assert "valence" in result[0]["audio_features"]
        assert "mood_score" in result[0]["audio_features"]

    def test_synthesise_mood_valid(self):
        executor = make_test_executor()
        mood_data = {
            "primary_mood": "Melancholic Introspection",
            "confidence": 0.82,
            "energy_level": 3.5,
            "emotional_arc": "Stable sadness",
            "arc_direction": "stable",
            "avg_valence": 0.35,
            "avg_energy": 0.4,
            "avg_danceability": 0.5,
            "avg_acousticness": 0.7,
            "avg_instrumentalness": 0.01,
            "avg_tempo": 100.0,
            "top_genres": ["lo-fi", "indie folk"],
            "dominant_mode": "minor",
            "insight": "Deep in reflection tonight.",
            "recommendations": ["Bon Iver — Holocene"],
        }
        result_str = executor.execute("synthesise_mood", {"mood_json": json.dumps(mood_data)})
        result = json.loads(result_str)
        assert result["status"] == "accepted"
        assert executor.final_result is not None
        assert executor.final_result["primary_mood"] == "Melancholic Introspection"

    def test_synthesise_mood_invalid_json(self):
        executor = make_test_executor()
        result_str = executor.execute("synthesise_mood", {"mood_json": "not valid json {"})
        result = json.loads(result_str)
        assert result["status"] == "error"

    def test_unknown_tool(self):
        executor = make_test_executor()
        result_str = executor.execute("nonexistent_tool", {})
        result = json.loads(result_str)
        assert "error" in result

    def test_trajectory_insufficient_data(self):
        """When only 1 track, trajectory should return informative error."""
        tracks = [make_full_track(0, 0.5, 0.5)]
        session = RecentlyPlayedSession(tracks=tracks)
        summary = analyse_session(session)
        executor = ToolExecutor(session, summary, trajectory=None)
        result_str = executor.execute("get_mood_trajectory", {})
        result = json.loads(result_str)
        assert "error" in result
