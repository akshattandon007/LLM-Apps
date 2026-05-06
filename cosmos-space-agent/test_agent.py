"""
Tests for the COSMOS Space Agent.
Run: pytest tests/ -v
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import create_client, run_agent


class TestAgentCreation(unittest.TestCase):
    """Test agent initialization."""

    def test_create_client_requires_api_key(self):
        """Should raise ValueError if no API key set."""
        with patch.dict(os.environ, {}, clear=True):
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            with self.assertRaises((ValueError, KeyError)):
                create_client()

    def test_create_client_with_key(self):
        """Should create client when API key is present."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-123"}):
            with patch("anthropic.Anthropic") as mock_anthropic:
                mock_anthropic.return_value = MagicMock()
                client = create_client()
                self.assertIsNotNone(client)


class TestPlanetTracker(unittest.TestCase):
    """Test planet tracker script argument validation."""

    def test_valid_planets(self):
        """All solar system planets should be accepted."""
        from scripts.planet_tracker import VALID_PLANETS

        expected = {"mercury", "venus", "earth", "mars", "jupiter",
                    "saturn", "uranus", "neptune", "pluto", "all"}
        self.assertEqual(VALID_PLANETS, expected)

    def test_invalid_planet_not_in_set(self):
        """Random strings should not be in valid planets."""
        from scripts.planet_tracker import VALID_PLANETS

        self.assertNotIn("krypton", VALID_PLANETS)
        self.assertNotIn("tatooine", VALID_PLANETS)
        self.assertNotIn("", VALID_PLANETS)


class TestConversationHistory(unittest.TestCase):
    """Test conversation history management."""

    def test_history_appends_user_message(self):
        """run_agent should append user message to history."""
        mock_client = MagicMock()

        # Mock a simple text response
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Here are the latest Mars missions..."

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.stop_reason = "end_turn"

        mock_client.messages.create.return_value = mock_response

        history = []
        response_text, updated_history = run_agent(
            "Tell me about Mars missions", history, mock_client
        )

        # Check user message was added
        self.assertTrue(any(
            msg["role"] == "user" and "Mars" in str(msg["content"])
            for msg in updated_history
        ))

        # Check assistant message was added
        self.assertTrue(any(msg["role"] == "assistant" for msg in updated_history))

    def test_history_preserves_previous_context(self):
        """History should accumulate across multiple turns."""
        mock_client = MagicMock()

        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = "Saturn has 146 known moons."

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.stop_reason = "end_turn"

        mock_client.messages.create.return_value = mock_response

        history = [
            {"role": "user", "content": "What about Jupiter?"},
            {"role": "assistant", "content": [mock_block]},
        ]

        _, updated_history = run_agent("Now tell me about Saturn", history, mock_client)

        # Should have 4 entries: 2 original + 1 new user + 1 new assistant
        self.assertEqual(len(updated_history), 4)


class TestResponseExtraction(unittest.TestCase):
    """Test that text is properly extracted from API responses."""

    def test_extracts_text_from_response(self):
        """Should extract text blocks from multi-block responses."""
        mock_client = MagicMock()

        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Jupiter is the largest planet."

        tool_block = MagicMock()
        tool_block.type = "tool_use"

        mock_response = MagicMock()
        mock_response.content = [tool_block, text_block]  # mixed blocks
        mock_response.stop_reason = "end_turn"

        mock_client.messages.create.return_value = mock_response

        response_text, _ = run_agent("Tell me about Jupiter", [], mock_client)
        self.assertIn("Jupiter", response_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
