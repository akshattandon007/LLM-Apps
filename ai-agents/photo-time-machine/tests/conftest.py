"""Shared fixtures for Photo Time Machine tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.models import EraTransformation


@pytest.fixture
def mock_photo_path() -> str:
    """Return a path that simulates an uploaded selfie."""
    return "selfie_mock.jpg"


@pytest.fixture
def sample_transformations() -> list[EraTransformation]:
    """Return a representative list of era transformations for gallery tests."""
    from src.eras import all_eras

    eras = all_eras()
    return [
        EraTransformation(
            era=e.decade,
            title=e.title,
            description=f"Simulated {e.decade} look: {e.style_description}",
            caption=e.caption,
            tagline=e.tagline,
            output_image=None,
        )
        for e in eras
    ]