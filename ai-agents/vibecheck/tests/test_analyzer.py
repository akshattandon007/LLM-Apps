"""
Tests for the VibeCheck analyzer module.
Uses a mock provider to avoid real API calls.
"""

import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vibecheck.analyzer import (
    analyze_text,
    compare_texts,
    ToneAnalysis,
    ComparisonResult,
    _try_parse_json,
)


class MockProvider:
    """Returns canned JSON responses for testing."""

    def __init__(self, response_json: dict):
        self.response_json = response_json

    def query(self, prompt: str) -> str:
        return json.dumps(self.response_json)


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def neutral_text():
    return "The meeting is scheduled for 3 PM. Please bring the quarterly report."


@pytest.fixture
def frustrated_text():
    return "I've asked three times already and nobody has responded to my email. This is getting ridiculous. I need an answer today or this project is going to miss the deadline."


@pytest.fixture
def assertive_text():
    return "Per our discussion, I expect the deliverables by Friday EOD. If there are blockers, escalate to me directly. This timeline is non-negotiable."


@pytest.fixture
def mock_neutral_result():
    return {
        "overall_tone": "Neutral and factual, straightforward scheduling communication",
        "emotional_subtext": ["No strong emotions detected", "Slight urgency in the request to bring the report"],
        "clarity_score": 9,
        "confidence_level": "moderate",
        "formality": "neutral",
        "detected_mood": "neutral",
        "potential_misinterpretations": ["Could be read as abrupt if the recipient expects a warmer tone"],
        "rewrite_suggestions": ["Add a greeting to soften the request", "Consider 'Could you please bring...' instead of 'Please bring...'"],
        "key_strengths": ["Clear and direct", "Includes relevant context (time and required item)"],
    }


@pytest.fixture
def mock_frustrated_result():
    return {
        "overall_tone": "Frustrated and urgent, expressing repeated unaddressed concerns",
        "emotional_subtext": ["Frustration from being ignored", "Anxiety about project deadline", "Underlying fear of failure"],
        "clarity_score": 7,
        "confidence_level": "assertive",
        "formality": "casual",
        "detected_mood": "frustrated",
        "potential_misinterpretations": ["Could come across as aggressive or accusatory", "May make recipients defensive"],
        "rewrite_suggestions": ["Start with a neutral observation rather than complaint", "Use 'I' statements instead of accusations"],
        "key_strengths": ["Clearly communicates the stakes", "Shows investment in project success"],
    }


# ── _try_parse_json tests ────────────────────────────────────────────────

class TestTryParseJson:
    def test_plain_json(self):
        text = '{"key": "value"}'
        result = _try_parse_json(text)
        assert result == {"key": "value"}

    def test_json_with_code_fences(self):
        text = '```json\n{"key": "value"}\n```'
        result = _try_parse_json(text)
        assert result == {"key": "value"}

    def test_json_with_fences_no_lang(self):
        text = '```\n{"key": "value"}\n```'
        result = _try_parse_json(text)
        assert result == {"key": "value"}

    def test_invalid_json(self):
        text = "This is not JSON"
        result = _try_parse_json(text)
        assert result is None

    def test_empty_string(self):
        assert _try_parse_json("") is None


# ── analyze_text tests ──────────────────────────────────────────────────

class TestAnalyzeText:
    def test_empty_text(self):
        result = analyze_text("")
        assert result.overall_tone == "No text provided to analyze."

    def test_whitespace_only(self):
        result = analyze_text("   ")
        assert result.overall_tone == "No text provided to analyze."

    def test_neutral_text(self, neutral_text, mock_neutral_result):
        provider = MockProvider(mock_neutral_result)
        result = analyze_text(neutral_text, provider)

        assert result.overall_tone == mock_neutral_result["overall_tone"]
        assert result.clarity_score == mock_neutral_result["clarity_score"]
        assert result.detected_mood == mock_neutral_result["detected_mood"]
        assert len(result.emotional_subtext) == 2
        assert len(result.rewrite_suggestions) == 2
        assert result.raw_llm_response is not None

    def test_frustrated_text(self, frustrated_text, mock_frustrated_result):
        provider = MockProvider(mock_frustrated_result)
        result = analyze_text(frustrated_text, provider)

        assert result.overall_tone == mock_frustrated_result["overall_tone"]
        assert result.detected_mood == "frustrated"
        assert result.formality == "casual"
        assert len(result.potential_misinterpretations) == 2

    def test_parsing_failure_returns_raw_response(self, neutral_text):
        """When LLM returns unparseable text, still return ToneAnalysis with raw response."""
        class BadProvider:
            def query(self, prompt):
                return "This is not JSON at all. Sorry!"

        result = analyze_text(neutral_text, BadProvider())
        # Should have empty fields but the raw response
        assert result.overall_tone == ""
        assert result.clarity_score == 0
        assert "Sorry" in result.raw_llm_response


# ── compare_texts tests ──────────────────────────────────────────────────

class TestCompareTexts:
    def test_compare_different_texts(self, frustrated_text, assertive_text,
                                      mock_frustrated_result):
        """Compare a frustrated and an assertive version of a message."""
        class CompareProvider:
            def __init__(self):
                self.call_count = 0

            def query(self, prompt):
                self.call_count += 1
                if self.call_count <= 2:
                    return json.dumps(mock_frustrated_result)
                return json.dumps({
                    "original_tone": "Frustrated and urgent",
                    "rewritten_tone": "Assertive and professional",
                    "differences": [
                        "Changed from emotional to factual framing",
                        "Reduced intensity of complaints",
                        "Added concrete deadlines and expectations",
                    ],
                    "improvement_areas": [
                        "Original could be perceived as aggressive",
                        "Rewrite maintains firmness without accusation",
                    ],
                })

        provider = CompareProvider()
        result = compare_texts(frustrated_text, assertive_text, provider)

        assert result.original.detected_mood == "frustrated"
        assert len(result.differences) == 3
        assert len(result.improvement_areas) == 2


# ── Integration sanity tests ─────────────────────────────────────────────

class TestToneAnalysisDataclass:
    def test_default_values(self):
        ta = ToneAnalysis()
        assert ta.overall_tone == ""
        assert ta.clarity_score == 0
        assert ta.emotional_subtext == []
        assert ta.rewrite_suggestions == []
        assert ta.key_strengths == []

    def test_confidence_level_valid_values(self):
        for level in ["low", "moderate", "high", "assertive", "passive"]:
            ta = ToneAnalysis(confidence_level=level)
            assert ta.confidence_level == level