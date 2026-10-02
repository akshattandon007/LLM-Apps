"""Tests for DreamDecoder journal persistence module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.models import DreamEntry, DreamInterpretation
from src import journal


class TestJournal(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.journal_path = os.path.join(self.tmpdir, "journal.json")
        self._orig_path = journal.JOURNAL_PATH
        journal.JOURNAL_PATH = self.journal_path

    def tearDown(self):
        journal.JOURNAL_PATH = self._orig_path
        if os.path.exists(self.journal_path):
            os.unlink(self.journal_path)

    def test_save_and_load(self):
        entry = DreamEntry(dream_text="Test dream")
        journal.save_entry(entry)
        loaded = journal.load_all()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].dream_text, "Test dream")

    def test_search_by_text(self):
        e1 = DreamEntry(dream_text="Flying over mountains", interpretation=DreamInterpretation(
            interpretation="Freedom", symbols=["sky"], mood="peaceful", themes=["freedom"]
        ))
        e2 = DreamEntry(dream_text="Swimming in the ocean")
        journal.save_entry(e1)
        journal.save_entry(e2)

        results = journal.search_entries("flying")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].dream_text, "Flying over mountains")

        results = journal.search_entries("ocean")
        self.assertEqual(len(results), 1)

    def test_search_by_symbol(self):
        entry = DreamEntry(dream_text="Strange dream", interpretation=DreamInterpretation(
            interpretation="Complex analysis", symbols=["door", "light"], mood="mysterious", themes=["transition"]
        ))
        journal.save_entry(entry)
        results = journal.search_entries("door")
        self.assertEqual(len(results), 1)

    def test_delete_entry(self):
        e1 = DreamEntry(dream_text="First")
        e2 = DreamEntry(dream_text="Second")
        journal.save_entry(e1)
        journal.save_entry(e2)
        self.assertTrue(journal.delete_entry(e1.id))
        self.assertEqual(len(journal.load_all()), 1)
        self.assertFalse(journal.delete_entry("nonexistent"))

    def test_clear_all(self):
        journal.save_entry(DreamEntry(dream_text="A"))
        journal.save_entry(DreamEntry(dream_text="B"))
        count = journal.clear_all()
        self.assertEqual(count, 2)
        self.assertEqual(len(journal.load_all()), 0)

    def test_compute_stats_empty(self):
        stats = journal.compute_stats()
        self.assertEqual(stats.total_entries, 0)

    def test_compute_stats_with_entries(self):
        interp1 = DreamInterpretation(
            interpretation="Analysis", symbols=["flying", "sky"], mood="peaceful", themes=["freedom"]
        )
        interp2 = DreamInterpretation(
            interpretation="Analysis2", symbols=["water", "flying"], mood="anxious", themes=["emotion"]
        )
        journal.save_entry(DreamEntry(dream_text="Dream A", interpretation=interp1))
        journal.save_entry(DreamEntry(dream_text="Dream B", interpretation=interp2))

        stats = journal.compute_stats()
        self.assertEqual(stats.total_entries, 2)
        self.assertIn(("flying", 2), stats.top_symbols)
        self.assertIn("peaceful", stats.mood_distribution)
        self.assertIn("anxious", stats.mood_distribution)


if __name__ == "__main__":
    unittest.main()