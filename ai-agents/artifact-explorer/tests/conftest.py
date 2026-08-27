"""Fixtures for Artifact Explorer smoke tests."""

import pytest

from src.models import Artifact, IdentificationResult, ArtifactCard


@pytest.fixture
def mock_identification() -> IdentificationResult:
    return IdentificationResult(
        name="Aloe Vera (Aloe barbadensis miller)",
        category="plant",
        description="A succulent with thick, fleshy green leaves edged with small white teeth.",
    )


@pytest.fixture
def mock_artifact() -> Artifact:
    return Artifact(
        name="Aloe Vera (Aloe barbadensis miller)",
        category="plant",
        description="A succulent with thick, fleshy green leaves edged with small white teeth.",
        origin="Arabian Peninsula",
        era="Ancient (2200 BCE)",
        history="Used by Sumerians, Egyptians, and Greeks for medicinal purposes.",
        cultural_significance="The only plant-based treatment recommended by the American Academy of Dermatology for sunburn.",
        practical_uses="Snap off a leaf and apply gel to minor burns.",
        fun_facts=["Over 500 species exist but only one has significant medicinal properties.",
                    "The gel is 99% water."],
    )


@pytest.fixture
def mock_card() -> ArtifactCard:
    return ArtifactCard(
        title="ARTIFACT EXPLORER — ALOE VERA",
        body="A rich text card body",
        tags=["plant", "Aloe"],
    )