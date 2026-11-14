#!/usr/bin/env python3
"""Tests for etymolog — word etymology journey explorer."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add parent to path for import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import etymolog


class TestDatamuse(unittest.TestCase):
    """Test Datamuse API integration."""

    @patch("etymolog.urllib.request.urlopen")
    def test_fetch_related_words_similar(self, mock_urlopen):
        """Test fetching similar words."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {"word": "serendipity", "score": 100},
            {"word": "luck", "score": 85},
            {"word": "chance", "score": 72},
        ]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = etymolog.fetch_related_words("serendipity", limit=3)
        self.assertIn("similar", result)
        self.assertEqual(len(result["similar"]), 3)
        self.assertEqual(result["similar"][0]["word"], "serendipity")

    @patch("etymolog.urllib.request.urlopen")
    def test_fetch_related_words_network_failure(self, mock_urlopen):
        """Test graceful handling of network errors."""
        mock_urlopen.side_effect = Exception("Connection failed")
        result = etymolog.fetch_related_words("testword")
        self.assertIn("similar", result)
        self.assertIn("similar_error", result)


class TestWiktionary(unittest.TestCase):
    """Test Wiktionary API integration."""

    @patch("etymolog.urllib.request.urlopen")
    def test_fetch_etymology_success(self, mock_urlopen):
        """Test fetching etymology returns expected structure."""
        # Mock parse API response
        parse_mock = MagicMock()
        parse_mock.read.return_value = json.dumps({
            "parse": {
                "text": {"*": "<div><p>From Old English <i>word</i></p></div>"}
            }
        }).encode()
        parse_mock.__enter__.return_value = parse_mock

        # Mock REST API response
        rest_mock = MagicMock()
        rest_mock.read.return_value = json.dumps({
            "en": [{"definition": "A unit of language"}]
        }).encode()
        rest_mock.__enter__.return_value = rest_mock

        # First call = parse, second = rest
        mock_urlopen.side_effect = [parse_mock, rest_mock]

        result = etymolog.fetch_etymology("word")
        self.assertIn("etymology", result)
        self.assertIn("definitions", result)

    @patch("etymolog.urllib.request.urlopen")
    def test_fetch_etymology_not_found(self, mock_urlopen):
        """Test handling of non-existent word."""
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            "https://en.wiktionary.org/w/api.php", 404,
            "Not Found", {}, None
        )
        result = etymolog.fetch_etymology("xyznonexistent123")
        self.assertIn("etymology", result)


class TestFallbackNarrative(unittest.TestCase):
    """Test fallback narrative generation."""

    def test_fallback_basic(self):
        """Test fallback generates structured output."""
        etymology = {"etymology": "From Old English cild.", "definitions": ["A young person"]}
        related = {
            "similar": [{"word": "kid", "score": 90}],
            "rhymes": [{"word": "wild", "score": 80}],
            "triggers": [{"word": "parent", "score": 85}],
        }
        narrative = etymolog._fallback_narrative("child", etymology, related)
        self.assertIn("Origin", narrative)
        self.assertIn("Definitions", narrative)
        self.assertIn("Similar Words", narrative)
        self.assertIn("child", narrative.lower())

    def test_fallback_empty_etymology(self):
        """Test fallback with missing etymology data."""
        etymology = {"etymology": "", "definitions": []}
        related = {"similar": [], "rhymes": [], "triggers": []}
        narrative = etymolog._fallback_narrative("test", etymology, related)
        self.assertIsInstance(narrative, str)
        self.assertGreater(len(narrative), 0)


class TestFormatOutput(unittest.TestCase):
    """Test output formatting."""

    def test_format_output_structure(self):
        """Test output has expected structure."""
        etymology = {"etymology": "Some origin", "definitions": ["A thing"]}
        related = {"similar": [], "rhymes": [], "triggers": []}
        narrative = "This word comes from ancient roots."

        output = etymolog.format_output("test", etymology, related, narrative)
        self.assertIn("e t y m o l o g", output)
        self.assertIn("Wiktionary", output)


class TestCLI(unittest.TestCase):
    """Test CLI argument handling."""

    def test_no_word_shows_help(self):
        """Test running without arguments."""
        # Should print help and exit
        with self.assertRaises(SystemExit):
            with patch("sys.stdin.read", return_value=""):
                from etymolog import main
                with patch("sys.argv", ["etymolog"]):
                    main()


if __name__ == "__main__":
    unittest.main()