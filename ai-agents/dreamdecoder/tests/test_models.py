"""Tests for DreamDecoder journal module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.models import DreamEntry, DreamInterpretation, DreamStats


class TestDreamEntry(unittest.TestCase):
    def test_entry_creates_id(self):
        entry = DreamEntry(dream_text="I dreamed of flying")
        self.assertEqual(len(entry.id), 12)
        self.assertTrue(entry.id.isalnum())

    def test_entry_to_dict_roundtrip(self):
        interp = DreamInterpretation(
            interpretation="A dream about freedom",
            symbols=["flying", "sky"],
            mood="peaceful",
            themes=["freedom"],
        )
        entry = DreamEntry(dream_text="I flew over mountains", interpretation=interp, tags=["fun"])
        d = entry.to_dict()
        restored = DreamEntry.from_dict(d)
        self.assertEqual(restored.dream_text, entry.dream_text)
        self.assertEqual(restored.tags, entry.tags)
        self.assertIsNotNone(restored.interpretation)
        if restored.interpretation:
            self.assertEqual(restored.interpretation.mood, "peaceful")
            self.assertEqual(restored.interpretation.symbols, ["flying", "sky"])

    def test_entry_no_interpretation(self):
        entry = DreamEntry(dream_text="Just a short dream")
        d = entry.to_dict()
        restored = DreamEntry.from_dict(d)
        self.assertIsNone(restored.interpretation)


class TestDreamStats(unittest.TestCase):
    def test_stats_defaults(self):
        stats = DreamStats()
        self.assertEqual(stats.total_entries, 0)
        self.assertEqual(stats.top_symbols, [])
        self.assertEqual(stats.mood_distribution, {})


if __name__ == "__main__":
    unittest.main()