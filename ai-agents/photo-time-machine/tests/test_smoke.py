"""Smoke tests for Photo Time Machine."""

from __future__ import annotations

import pytest

from pathlib import Path

from pydantic import ValidationError

from src.eras import ERAS, all_eras, get_era_by_decade
from src.gallery import build_gallery, build_photo_time_machine_output
from src.models import EraStyle, EraTransformation, PhotoTimeMachineOutput
from src.transformer import transform_photo


# ── Eras tests ───────────────────────────────────────────────────────────────


class TestEraDefinitions:
    def test_defines_at_least_six_eras(self):
        assert len(ERAS) >= 6, "Need at least 6 era definitions"

    def test_each_era_has_all_fields(self):
        for era in ERAS:
            assert era.decade
            assert era.title
            assert era.style_description
            assert era.visual_filter
            assert era.caption
            assert era.tagline
            assert len(era.accent_colors) >= 2

    def test_accent_colors_are_valid_hex(self):
        for era in ERAS:
            for colour in era.accent_colors:
                assert colour.startswith("#")
                assert len(colour) == 7

    def test_get_era_by_decade_finds_existing(self):
        era = get_era_by_decade("1990s")
        assert era is not None
        assert era.decade == "1990s"

    def test_get_era_by_decade_returns_none_for_missing(self):
        assert get_era_by_decade("1890s") is None

    def test_all_eras_returns_list(self):
        assert len(all_eras()) == len(ERAS)


# ── Model validation tests ───────────────────────────────────────────────────


class TestModels:
    def test_era_style_valid(self):
        era = EraStyle(
            decade="1980s",
            title="1980s — Rad Times",
            style_description="Big hair, neon spandex, leg warmers.",
            visual_filter="VHS grain with chromatic aberration.",
            caption="Totally radical!",
            tagline="Radical!",
            accent_colors=["#ff00ff", "#00ffff"],
        )
        assert era.decade == "1980s"

    def test_era_style_rejects_empty_decade(self):
        with pytest.raises(ValidationError):
            EraStyle(
                decade="",
                title="Test",
                style_description="x",
                visual_filter="x",
                caption="x",
                tagline="x",
                accent_colors=["#000"],
            )

    def test_era_transformation_valid(self):
        t = EraTransformation(
            era="1950s",
            title="1950s — Test",
            description="A greaser look",
            caption="Rock!",
            tagline="Rock around the clock",
        )
        assert t.era == "1950s"
        assert t.output_image is None

    def test_photo_time_machine_output_valid(
        self, sample_transformations: list[EraTransformation]
    ):
        output = PhotoTimeMachineOutput(
            original_name="test.jpg",
            eras=sample_transformations,
            gallery_message="Gallery test",
        )
        assert len(output.eras) == 6
        assert output.gallery_message == "Gallery test"

    def test_photo_time_machine_output_rejects_empty_eras(self):
        with pytest.raises(ValidationError):
            PhotoTimeMachineOutput(
                original_name="test.jpg",
                eras=[],
                gallery_message="Empty!",
            )


# ── Transformer tests ────────────────────────────────────────────────────────


class TestTransformer:
    def test_transform_photo_returns_all_eras(self, mock_photo_path: str):
        results = transform_photo(mock_photo_path, simulate=True)
        assert len(results) == len(ERAS)

    def test_each_result_has_non_empty_fields(self, mock_photo_path: str):
        results = transform_photo(mock_photo_path, simulate=True)
        for r in results:
            assert r.era
            assert r.title
            assert r.description
            assert "SIMULATED" in r.description
            assert r.caption
            assert r.tagline
            assert r.output_image is None

    def test_transform_photo_chronological(self, mock_photo_path: str):
        results = transform_photo(mock_photo_path, simulate=True)
        decades = [r.era for r in results]
        expected = ["1950s", "1970s", "1990s", "2000s", "2025", "2050s"]
        assert decades == expected

    def test_simulate_mode_description_includes_filter(
        self, mock_photo_path: str
    ):
        results = transform_photo(mock_photo_path, simulate=True)
        assert "Filter applied" in results[0].description


# ── Gallery tests ────────────────────────────────────────────────────────────


class TestGallery:
    def test_build_gallery_returns_string(
        self, sample_transformations: list[EraTransformation]
    ):
        output = PhotoTimeMachineOutput(
            original_name="test.jpg",
            eras=sample_transformations,
            gallery_message="Gallery test",
        )
        gallery = build_gallery(output)
        assert isinstance(gallery, str)
        assert len(gallery) > 100

    def test_gallery_includes_all_eras(
        self, sample_transformations: list[EraTransformation]
    ):
        output = PhotoTimeMachineOutput(
            original_name="test.jpg",
            eras=sample_transformations,
            gallery_message="Gallery test",
        )
        gallery = build_gallery(output)
        for era in sample_transformations:
            assert era.era in gallery
            assert era.caption in gallery

    def test_gallery_includes_original_name(
        self, sample_transformations: list[EraTransformation]
    ):
        output = PhotoTimeMachineOutput(
            original_name="my_selfie.png",
            eras=sample_transformations,
            gallery_message="Gallery!",
        )
        gallery = build_gallery(output)
        assert "my_selfie.png" in gallery

    def test_build_photo_time_machine_output(
        self, mock_photo_path: str, sample_transformations: list[EraTransformation]
    ):
        output = build_photo_time_machine_output(
            mock_photo_path, sample_transformations
        )
        assert output.original_name == mock_photo_path
        assert len(output.eras) == 6
        assert "1950s" in output.gallery_message


# ── Integration test ─────────────────────────────────────────────────────────


class TestIntegration:
    def test_full_simulated_flow(self, mock_photo_path: str):
        """Run transform + gallery assembly end-to-end with simulated data."""
        transformations = transform_photo(mock_photo_path, simulate=True)
        output = build_photo_time_machine_output(
            mock_photo_path, transformations
        )
        gallery = build_gallery(output)
        assert "1950s" in gallery
        assert "2050s" in gallery
        assert "PHOTO TIME MACHINE" in gallery
        assert mock_photo_path in gallery