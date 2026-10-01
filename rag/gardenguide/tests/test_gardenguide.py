"""Tests for GardenGuide RAG engine — without hitting real APIs."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

# Add src to path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.doc_loader import (
    load_document,
    chunk_text,
    load_text,
    SUPPORTED_EXTENSIONS,
)


class TestDocLoader(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def _write(self, name: str, content: str) -> str:
        path = self.tmpdir / name
        path.write_text(content)
        return str(path)

    def test_load_text_basic(self):
        path = self._write("test.txt", "Hello world")
        text = load_text(path)
        self.assertEqual(text, "Hello world")

    def test_load_text_unicode(self):
        content = "🌱 Tomato seeds\n• Plant in spring"
        path = self._write("unicode.txt", content)
        text = load_text(path)
        self.assertEqual(text, content)

    def test_chunk_text_small(self):
        """Text smaller than chunk size returns as one chunk."""
        chunks = chunk_text("Hello world.", chunk_size=500)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "Hello world.")

    def test_chunk_text_splits_at_sentences(self):
        text = "This is the first sentence about tomatoes. "
        text += "This is the second sentence about watering. "
        text += "This is the third about harvesting."
        chunks = chunk_text(text, chunk_size=60, overlap=10)
        # Should create multiple chunks
        self.assertGreater(len(chunks), 1)
        # All chunks should contain complete sentences
        for chunk in chunks:
            self.assertTrue(chunk.endswith("."))

    def test_chunk_text_overlap(self):
        text = "Sentence A about seeds. "
        text *= 20  # Repeat to ensure multiple chunks
        chunks = chunk_text(text, chunk_size=80, overlap=30)
        self.assertGreater(len(chunks), 1)
        # Check overlap: consecutive chunks should share some text
        overlap_found = False
        for i in range(len(chunks) - 1):
            words = set(chunks[i].split())
            next_words = set(chunks[i + 1].split())
            if words & next_words:
                overlap_found = True
                break
        self.assertTrue(overlap_found, "No overlap found between consecutive chunks")

    def test_chunk_on_sentence_with_questions(self):
        text = "When should I plant? In spring. How deep? 1 inch."
        chunks = chunk_text(text, chunk_size=30, overlap=0)
        self.assertGreaterEqual(len(chunks), 2)

    def test_load_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            load_document("/tmp/nonexistent_file_xyz.txt")

    def test_load_unsupported_format(self):
        path = self._write("test.csv", "a,b,c\n1,2,3")
        with self.assertRaises(ValueError):
            load_document(path)

    def test_load_empty_file(self):
        path = self._write("empty.txt", "")
        with self.assertRaises(ValueError):
            load_document(path)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store_dir = str(Path(self.tmpdir) / "store")

    def _make_store(self):
        from src.rag_engine import VectorStore

        return VectorStore(store_dir=self.store_dir)

    def test_empty_store(self):
        store = self._make_store()
        results = store.search(np.zeros(384), top_k=3)
        self.assertEqual(results, [])

    def test_add_and_search(self):
        store = self._make_store()
        # Add two chunks with distinct embeddings
        emb1 = np.array([[1.0, 0.0, 0.0]])
        emb2 = np.array([[0.0, 1.0, 0.0]])
        store.add_chunks(
            ["Tomatoes need full sun.", "Lavender prefers dry soil."],
            "/docs/garden.txt",
            np.vstack([emb1, emb2]),
        )
        # Search with query close to emb1
        query = np.array([0.9, 0.1, 0.0])
        results = store.search(query, top_k=2)
        self.assertEqual(len(results), 2)
        # First result should be "Tomatoes need full sun."
        self.assertIn("Tomatoes", results[0][0])

    def test_persistence(self):
        """Store saves and reloads correctly."""
        store1 = self._make_store()
        emb = np.array([[1.0, 0.0]])
        store1.add_chunks(["Test chunk."], "/docs/test.txt", emb)
        del store1

        store2 = self._make_store()
        self.assertEqual(store2.chunk_count, 1)
        self.assertEqual(store2.chunks[0], "Test chunk.")

    def test_remove_doc(self):
        store = self._make_store()
        emb = np.array([[1.0, 0.0], [0.0, 1.0]])
        store.add_chunks(
            ["Chunk A.", "Chunk B."], "/docs/doc1.txt", emb
        )
        emb2 = np.array([[0.5, 0.5]])
        store.add_chunks(["Chunk C."], "/docs/doc2.txt", emb2)

        self.assertEqual(store.chunk_count, 3)
        store.remove_doc("/docs/doc1.txt")
        self.assertEqual(store.chunk_count, 1)
        self.assertEqual(store.chunks[0], "Chunk C.")


class TestRAGEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        # Create a test doc
        self.doc_path = self.tmpdir / "test_garden.txt"
        self.doc_path.write_text(
            "Tomatoes should be planted in full sun. "
            "They need at least 6 hours of direct sunlight daily. "
            "Plant seeds 1/4 inch deep in well-draining soil. "
            "Water deeply once a week, more in hot weather."
        )

    @patch("src.rag_engine.GardenRAG.client")
    def test_ingest_and_search(self, mock_client):
        from src.rag_engine import GardenRAG

        # Mock embeddings response
        mock_embed = MagicMock()
        mock_embed.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_embed

        store_dir = str(self.tmpdir / "rag_store")
        rag = GardenRAG(store_dir=store_dir)

        result = rag.ingest(str(self.doc_path))
        self.assertIn("chunks", result)
        self.assertGreater(result["chunks"], 0)
        self.assertIn("filepath", result)


if __name__ == "__main__":
    unittest.main()