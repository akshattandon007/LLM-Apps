"""Tests for ClipRef searcher."""

import pytest
from pathlib import Path

from clipref import searcher, utils
from clipref.models import SearchResult, Answer


def _make_dummy_results(n: int = 3) -> list[SearchResult]:
    """Create dummy search results for testing."""
    return [
        SearchResult(
            chunk_id=f"chunk_{i}",
            text=f"Sample context {i}. This is some text for testing.",
            source_file=f"file_{i}.md",
            source_path=f"/path/to/file_{i}.md",
            score=1.0 - (i * 0.1),
        )
        for i in range(n)
    ]


def test_generate_answer_no_key(monkeypatch):
    """Test generate_answer returns None when no API key is set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    results = _make_dummy_results()
    answer = searcher.generate_answer("test", results)
    assert answer is None


def test_search_empty_db(tmp_path):
    """Test search on an empty/non-existent database returns empty list."""
    results = searcher.search("test query", tmp_path / "empty_db", None)
    assert results == []


def test_search_empty_query(tmp_path):
    """Test search with empty query on empty db."""
    results = searcher.search("", tmp_path / "empty_db", None)
    assert results == []


class TestSearchResult:
    def test_str_short_text(self):
        """Test string representation with short text."""
        r = SearchResult(
            chunk_id="id1",
            text="Short text.",
            source_file="test.md",
            source_path="test.md",
            score=0.95,
        )
        s = str(r)
        assert "[0.950]" in s
        assert "test.md" in s
        assert "Short text." in s

    def test_str_long_text(self):
        """Test string representation truncates long text."""
        r = SearchResult(
            chunk_id="id2",
            text="A" * 300,
            source_file="long.md",
            source_path="long.md",
            score=0.5,
        )
        s = str(r)
        assert "..." in s  # truncated indicator


class TestAnswer:
    def test_str_with_sources(self):
        """Test Answer string representation includes sources."""
        sources = _make_dummy_results(2)
        a = Answer(text="This is the answer.", sources=sources, model="test-model")
        s = str(a)
        assert "This is the answer." in s
        assert "--- Sources ---" in s
        assert "file_0.md" in s
        assert "file_1.md" in s

    def test_empty_sources(self):
        """Test Answer with no sources still renders."""
        a = Answer(text="Answer text.", sources=[], model="test")
        s = str(a)
        assert "Answer text." in s