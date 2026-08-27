"""Smoke tests for Artifact Explorer.

These tests validate the core pipeline end-to-end using fake/mock data,
without any external API calls.
"""

import pytest
from src.models import Artifact, IdentificationResult
from src.identifier import identify_from_text, ARTIFACT_LIBRARY
from src.historian import generate_story
from src.gallery import format_card, print_card


class TestIdentifier:
    """Identification layer — text-based fuzzy matching."""

    def setup_method(self):
        """Ensure the library is loaded before each test."""
        assert len(ARTIFACT_LIBRARY) >= 8, "Library must have at least 8 artifacts"

    def test_identify_by_exact_name(self):
        result = identify_from_text("aloe vera")
        assert result is not None
        assert result.category == "plant"

    def test_identify_by_description(self):
        result = identify_from_text("succulent with thick fleshy leaves")
        assert result is not None
        assert "Aloe" in result.name

    def test_identify_by_partial_keyword(self):
        result = identify_from_text("roman coin silver")
        assert result is not None
        assert "Denarius" in result.name

    def test_identify_unknown_object(self):
        result = identify_from_text("quantum flux capacitor")
        assert result is None

    def test_all_artifacts_have_required_fields(self):
        for key, data in ARTIFACT_LIBRARY.items():
            assert "name" in data, f"{key} missing 'name'"
            assert "category" in data, f"{key} missing 'category'"
            assert "description" in data, f"{key} missing 'description'"

    def test_every_artifact_has_story(self):
        for key, data in ARTIFACT_LIBRARY.items():
            ident = IdentificationResult(
                name=data["name"],
                category=data["category"],
                description=data["description"],
            )
            story = generate_story(ident)
            assert story.history, f"{key} has empty history"
            assert story.cultural_significance, f"{key} has empty cultural_significance"
            assert len(story.fun_facts) >= 1, f"{key} has no fun facts"

    def test_fallback_story_generated(self):
        unknown = IdentificationResult(
            name="Mystery Widget",
            category="unknown",
            description="Some mystery object.",
        )
        story = generate_story(unknown)
        assert "Mystery Widget" in story.history


class TestHistorian:
    """Story generation layer."""

    def setup_method(self):
        self.ident = IdentificationResult(
            name="Kodak Brownie No. 2",
            category="vintage camera",
            description="A box camera with meniscus lens.",
        )

    def test_generate_story_returns_artifact(self):
        artifact = generate_story(self.ident)
        assert isinstance(artifact, Artifact)
        assert artifact.name == "Kodak Brownie No. 2"

    def test_story_has_all_fields(self):
        artifact = generate_story(self.ident)
        assert artifact.origin
        assert artifact.era
        assert artifact.history
        assert artifact.cultural_significance
        assert artifact.practical_uses
        assert len(artifact.fun_facts) >= 2


class TestGallery:
    """Output formatting layer."""

    def setup_method(self):
        self.artifact = Artifact(
            name="Test Object",
            category="test",
            description="A test object description.",
            origin="Testland",
            era="2024",
            history="This is a test history.",
            cultural_significance="Test significance.",
            practical_uses="For testing.",
            fun_facts=["First fun fact.", "Second fun fact."],
        )

    def test_format_card_returns_card(self):
        card = format_card(self.artifact)
        assert card.title
        assert card.body
        assert len(card.tags) >= 1

    def test_print_card_does_not_error(self, capsys):
        print_card(self.artifact)
        captured = capsys.readouterr()
        assert "Test Object" in captured.out
        assert "TEST" in captured.out

    def test_card_includes_all_sections(self, capsys):
        print_card(self.artifact)
        captured = capsys.readouterr()
        assert "ORIGIN" in captured.out
        assert "STORY" in captured.out
        assert "CULTURAL SIGNIFICANCE" in captured.out
        assert "PRACTICAL USES" in captured.out
        assert "FUN FACTS" in captured.out


class TestPipeline:
    """End-to-end pipeline test (identified → historian → gallery)."""

    def setup_method(self):
        self.query = "amous purple crystals in rock"

    def test_describe_pipeline(self):
        ident = identify_from_text(self.query)
        assert ident is not None, "Should identify amethyst"
        artifact = generate_story(ident)
        assert "Amethyst" in artifact.name
        card = format_card(artifact)
        assert "Amethyst" in card.body

    def test_simulate_all_artifacts(self):
        """Run the full pipeline for every artifact in the library."""
        for data in ARTIFACT_LIBRARY.values():
            ident = IdentificationResult(
                name=data["name"],
                category=data["category"],
                description=data["description"],
            )
            artifact = generate_story(ident)
            card = format_card(artifact)
            assert data["name"] in card.body