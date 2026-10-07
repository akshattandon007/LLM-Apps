"""Tests for doc_loader module."""

import pytest
import tempfile
import os
from pathlib import Path

from manualmate.doc_loader import load_document, chunk_text, chunk_document


class TestLoadDocument:
    def test_loads_text_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world. This is a test.")
            fpath = f.name
        try:
            text, source = load_document(fpath)
            assert "Hello world" in text
            assert source == Path(fpath).name
        finally:
            os.unlink(fpath)

    def test_raises_on_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            load_document("/nonexistent/file.txt")

    def test_raises_on_bad_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            fpath = f.name
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                load_document(fpath)
        finally:
            os.unlink(fpath)


class TestChunkText:
    def test_empty_text(self):
        assert chunk_text("") == []

    def test_short_text_stays_one_chunk(self):
        chunks = chunk_text("Short text.", chunk_size=500)
        assert len(chunks) == 1

    def test_long_text_splits_into_multiple_chunks(self):
        text = "This is sentence one. This is sentence two. " * 30
        chunks = chunk_text(text, chunk_size=200, overlap=30)
        assert len(chunks) > 1
        assert all(len(c) <= 250 for c in chunks)  # allow some overlap buffer

    def test_chunks_have_overlap(self):
        text = ("A very long paragraph with many sentences. " * 20 +
                "The crucial information is here. " * 5 +
                "More sentences to fill it out. " * 15)
        chunks = chunk_text(text, chunk_size=200, overlap=60)
        if len(chunks) > 1:
            # Overlap means consecutive chunks share some text
            assert chunks[0][-30:] in chunks[1] or chunks[1][-30:] in chunks[0]


class TestChunkDocument:
    def test_creates_chunk_objects(self):
        text = "Sentence one. Sentence two. Sentence three. " * 5
        chunks = chunk_document(text, source="test.txt", doc_id="test|test.txt")
        assert len(chunks) >= 1
        for c in chunks:
            assert c.source == "test.txt"
            assert c.doc_id == "test|test.txt"
            assert c.index >= 0
            assert c.text
            assert c.char_end >= c.char_start