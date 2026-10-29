#!/usr/bin/env python3
"""Unit tests for Ingenius."""

import json
import sys
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ingenius


class TestBuildPrompt(unittest.TestCase):
    """Test prompt construction."""

    def test_basic_prompt(self):
        """Basic ingredient only."""
        system, user = ingenius.build_prompt("buttermilk", None, None)
        self.assertIn("buttermilk", user)
        self.assertIn("chef and food scientist", system)
        self.assertIn("valid json", system.lower())

    def test_with_recipe(self):
        """Ingredient + recipe context."""
        _, user = ingenius.build_prompt("fish sauce", "pad thai", None)
        self.assertIn("fish sauce", user)
        self.assertIn("pad thai", user)

    def test_quick_mood(self):
        """Quick mood modifier."""
        _, user = ingenius.build_prompt("butter", None, "quick")
        self.assertIn("fastest option", user)

    def test_pantry_mood(self):
        """Pantry mood modifier."""
        _, user = ingenius.build_prompt("butter", None, "pantry")
        self.assertIn("pantry staples", user)

    def test_gourmet_mood(self):
        """Gourmet mood modifier."""
        _, user = ingenius.build_prompt("butter", None, "gourmet")
        self.assertIn("best flavour", user)


class TestFormatOutput(unittest.TestCase):
    """Test output formatting."""

    def test_basic_format(self):
        """Standard 3-substitute output."""
        data = {
            "substitutes": [
                {"name": "Yogurt", "ratio": "1 cup replaces 1 cup", "chemistry": "Lactic acid", "tip": "Thin with milk"},
                {"name": "Milk + Lemon", "ratio": "1 cup minus 1 tbsp", "chemistry": "Acid curdles milk", "tip": "Let sit 5 min"},
                {"name": "Kefir", "ratio": "1 cup replaces 1 cup", "chemistry": "Fermented culture", "tip": "Shake first"},
            ]
        }
        out = ingenius.format_output(data, "buttermilk")
        self.assertIn("Yogurt", out)
        self.assertIn("buttermilk", out)
        self.assertIn("1 cup replaces 1 cup", out)

    def test_empty(self):
        """Empty substitutes list."""
        out = ingenius.format_output({"substitutes": []}, "x")
        self.assertIn("No substitutes", out)


class TestCallLlm(unittest.TestCase):
    """Test LLM integration (mocked)."""

    @patch("ingenius.requests.post")
    def test_successful_call(self, mock_post):
        """Mock a successful OpenRouter response."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"substitutes": [{"name": "Yogurt"}]}'}}]
        }
        mock_post.return_value = mock_resp

        # Temporarily set env
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            # Re-init the module-level variable
            ingenius.OPENROUTER_API_KEY = "test-key"
            result = ingenius.call_llm("system prompt", "user prompt")

        self.assertIn("substitutes", result)
        self.assertEqual(result["substitutes"][0]["name"], "Yogurt")

    @patch("ingenius.requests.post")
    def test_markdown_wrapped_json(self, mock_post):
        """LLM returns JSON inside a markdown code block."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {
                "content": "```json\n{\"substitutes\": [{\"name\": \"Honey\"}]}\n```"
            }}]
        }
        mock_post.return_value = mock_resp

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            ingenius.OPENROUTER_API_KEY = "test-key"
            result = ingenius.call_llm("system", "user")

        self.assertEqual(result["substitutes"][0]["name"], "Honey")


class TestCliIntegration(unittest.TestCase):
    """Test CLI entry point."""

    def test_help(self):
        """--help prints usage."""
        result = subprocess.run(
            [sys.executable, "-m", "ingenius", "--help"],
            capture_output=True, text=True, cwd="/tmp/ingenius"
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Ingenius", result.stdout)

    def test_no_api_key(self):
        """Without env var, should print error."""
        env = os.environ.copy()
        env.pop("OPENROUTER_API_KEY", None)
        result = subprocess.run(
            [sys.executable, "-m", "ingenius", "buttermilk"],
            capture_output=True, text=True, cwd="/tmp/ingenius",
            env=env
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPENROUTER_API_KEY", result.stderr)


if __name__ == "__main__":
    unittest.main()