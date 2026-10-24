"""Tests for sugarcoat — AI Message Diplomat."""

import json
import pytest
from unittest.mock import patch, MagicMock

from sugarcoat_engine import (
    rephrase_message,
    get_supported_tones,
    get_supported_styles,
    _make_system_prompt,
    _make_user_prompt,
    TONE_INSTRUCTIONS,
    STYLE_INSTRUCTIONS,
)


class TestHelpers:
    def test_get_supported_tones(self):
        tones = get_supported_tones()
        assert "gentle" in tones
        assert "empathetic" in tones
        assert "professional" in tones
        assert len(tones) >= 5

    def test_get_supported_styles(self):
        styles = get_supported_styles()
        assert "diplomatic" in styles
        assert "direct" in styles
        assert len(styles) >= 5

    def test_make_system_prompt_includes_tone(self):
        prompt = _make_system_prompt("gentle", "diplomatic")
        assert TONE_INSTRUCTIONS["gentle"] in prompt
        assert STYLE_INSTRUCTIONS["diplomatic"] in prompt

    def test_make_user_prompt_basic(self):
        prompt = _make_user_prompt("I can't come to your party")
        assert "I can't come to your party" in prompt

    def test_make_user_prompt_with_context(self):
        prompt = _make_user_prompt("I can't come", context="friend's birthday")
        assert "CONTEXT:" in prompt
        assert "friend's birthday" in prompt

    def test_make_user_prompt_with_history(self):
        history = [
            {"sender": "me", "text": "Can we meet Friday?"},
            {"sender": "them", "text": "Sure!"},
        ]
        prompt = _make_user_prompt("Actually I can't", history=history)
        assert "CONVERSATION HISTORY" in prompt
        assert "Can we meet Friday?" in prompt
        assert "Sure!" in prompt


class TestRephraseMessage:
    def test_successful_rephrase(self):
        """Test that a valid API response is parsed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "rephrased": "I'm so sorry, but I won't be able to make it to your party.",
                        "explanation": "Softer opening, acknowledges regret upfront.",
                        "alternatives": ["Sadly I can't make it.", "Wish I could be there!"],
                    })
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_response):
            result = rephrase_message(
                message="I can't come to your party",
                tone="gentle",
                style="diplomatic",
                api_key="test-key",
            )

        assert result["rephrased"] == "I'm so sorry, but I won't be able to make it to your party."
        assert result["explanation"] is not None
        assert len(result["alternatives"]) == 2

    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="API key is required"):
            rephrase_message("hello", api_key="")

    def test_fallback_when_not_json(self):
        """If the model returns plain text instead of JSON, wrap it."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Here's a better way to say that: I'm sorry I can't come."
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_response):
            result = rephrase_message(
                message="I can't come",
                api_key="test-key",
            )

        assert "I'm sorry" in result["rephrased"]

    def test_http_error_propagates(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.json.return_value = {}

        with patch("httpx.post", return_value=mock_response):
            with pytest.raises(Exception, match="HTTP 429"):
                rephrase_message("hello", api_key="test-key")

    def test_markdown_fence_removal(self):
        """Model sometimes wraps JSON in ``` fences."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "```json\n{\"rephrased\": \"Clean version.\", \"explanation\": null}\n```"
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_response):
            result = rephrase_message(
                message="Not great text",
                api_key="test-key",
            )

        assert result["rephrased"] == "Clean version."


class TestToneStyleDefinitions:
    """Each tone/style has its own instruction text."""

    def test_all_tones_have_instructions(self):
        for tone in get_supported_tones():
            assert tone in TONE_INSTRUCTIONS, f"Missing instruction for tone: {tone}"
            assert len(TONE_INSTRUCTIONS[tone]) > 10

    def test_all_styles_have_instructions(self):
        for style in get_supported_styles():
            assert style in STYLE_INSTRUCTIONS, f"Missing instruction for style: {style}"
            assert len(STYLE_INSTRUCTIONS[style]) > 10