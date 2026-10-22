"""Tests for swellcast core scoring logic."""

import pytest
from swellcast.core import _compute_score, _wave_origin_angle
from swellcast.models import SurfDay
from datetime import date


class TestWaveOriginAngle:
    def test_offshore(self):
        # swell from S (180°), wind from N (0°) = offshore
        assert _wave_origin_angle(180, 0) == "offshore"

    def test_onshore(self):
        # swell from S (180°), wind from S (180°) = onshore
        assert _wave_origin_angle(180, 180) == "onshore"

    def test_cross_shore(self):
        # swell from S (180°), wind from E (90°) = cross-shore
        assert _wave_origin_angle(180, 90) == "cross-shore"

    def test_wrap_around(self):
        # swell from N (350°), wind from S (170°) — diff=180 → offshore
        assert _wave_origin_angle(350, 170) == "offshore"

    def test_none_returns_unknown(self):
        assert _wave_origin_angle(None, 0) == "unknown"
        assert _wave_origin_angle(180, None) == "unknown"


class TestComputeScore:
    def test_excellent_surf(self):
        """Long-period swell, good wave height, offshore wind = excellent."""
        day = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=1.5,
            wave_dir_deg=180,
            wave_period_s=14.0,
            swell_height_m=1.4,
            swell_dir_deg=185,
            swell_period_s=16.0,
            wind_speed_kmh=10,
            wind_dir_deg=0,
        )
        score, label, cond = _compute_score(day)
        assert score >= 7.0
        assert "Excellent" in label

    def test_flat(self):
        """Small waves = poor."""
        day = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=0.2,
            wave_period_s=4.0,
            wind_speed_kmh=5,
            wind_dir_deg=180,
            wave_dir_deg=180,
        )
        score, label, cond = _compute_score(day)
        assert score < 4.0
        assert "Poor" in label or "Fair" in label

    def test_onshore_degrades(self):
        """Onshore wind reduces score vs offshore."""
        onshore = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=1.5,
            wave_dir_deg=180,
            wave_period_s=10.0,
            wind_speed_kmh=15,
            wind_dir_deg=180,  # onshore
        )
        offshore = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=1.5,
            wave_dir_deg=180,
            wave_period_s=10.0,
            wind_speed_kmh=15,
            wind_dir_deg=0,  # offshore
        )
        s1, _, _ = _compute_score(onshore)
        s2, _, _ = _compute_score(offshore)
        assert s2 > s1

    def test_heavy_wind_penalty(self):
        """High wind reduces score."""
        calm = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=1.0,
            wave_dir_deg=180,
            wave_period_s=8.0,
            wind_speed_kmh=10,
            wind_dir_deg=0,
        )
        gusty = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=1.0,
            wave_dir_deg=180,
            wave_period_s=8.0,
            wind_speed_kmh=50,
            wind_dir_deg=0,
        )
        s1, _, _ = _compute_score(calm)
        s2, _, _ = _compute_score(gusty)
        assert s1 > s2

    def test_score_clamped(self):
        """Score never exceeds 10 or goes below 0."""
        perfect = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=1.2,
            wave_dir_deg=180,
            wave_period_s=18.0,
            swell_height_m=1.2,
            swell_dir_deg=185,
            swell_period_s=20.0,
            wind_speed_kmh=5,
            wind_dir_deg=0,
        )
        score, _, _ = _compute_score(perfect)
        assert score <= 10.0

        terrible = SurfDay(
            dt=date(2026, 10, 22),
            wave_height_m=4.5,
            wave_period_s=3.0,
            wind_speed_kmh=60,
            wind_dir_deg=180,
            wave_dir_deg=180,
        )
        score2, _, _ = _compute_score(terrible)
        assert score2 >= 0.0

    def test_minimal_data(self):
        """Even with minimal data, score should compute without crash."""
        day = SurfDay(dt=date(2026, 10, 22), wave_height_m=1.0)
        score, label, cond = _compute_score(day)
        assert 0 <= score <= 10
        assert label
        assert cond


class TestCoreImport:
    def test_wind_dir_label(self):
        from swellcast.core import _wind_dir_label
        assert _wind_dir_label(0) == "N"
        assert _wind_dir_label(90) == "E"
        assert _wind_dir_label(180) == "S"
        assert _wind_dir_label(270) == "W"
        assert _wind_dir_label(45) == "NE"
        assert _wind_dir_label(11) == "N"
        assert _wind_dir_label(None) == "N/A"