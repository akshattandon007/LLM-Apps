"""Tests for the WikiPilot MCP server."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from wikipilot_client import (
    ArticleNotFound,
    WikipediaError,
    search_articles,
    get_summary,
    get_article,
    get_random_article,
    on_this_day,
    get_related_articles,
    get_article_categories,
)


# ── Search ─────────────────────────────────────────────────────────────────


def test_search_articles_returns_results():
    results = search_articles("Python programming", limit=5)
    assert len(results) > 0
    assert any("Python" in r["title"] for r in results)
    for r in results:
        assert "title" in r
        assert "page_id" in r
        assert "snippet" in r
        assert "url" in r
        assert r["url"].startswith("https://en.wikipedia.org/")


def test_search_articles_handles_no_results():
    results = search_articles("zzzzzznotarealarticleeeeeeeee", limit=3)
    assert results == [] or len(results) == 0


def test_search_articles_limit():
    results = search_articles("Wikipedia", limit=3)
    assert len(results) <= 3


# ── Summary ────────────────────────────────────────────────────────────────


def test_get_summary_known_article():
    info = get_summary("Python (programming language)")
    assert info["title"] == "Python (programming language)"
    assert len(info["extract"]) > 50
    assert "page_id" in info


def test_get_summary_missing_article():
    with pytest.raises(ArticleNotFound):
        get_summary("FakeNonExistentArticleXYZ123")


# ── Article ────────────────────────────────────────────────────────────────


def test_get_article_known():
    info = get_article("Earth")
    assert info["title"] == "Earth"
    assert len(info.get("content", "")) > 200 or len(info.get("extract", "")) > 200


# ── Random ─────────────────────────────────────────────────────────────────


def test_get_random_article():
    info = get_random_article()
    assert "title" in info
    assert len(info["title"]) > 0
    assert "extract" in info
    assert "page_id" in info


# ── On this day ────────────────────────────────────────────────────────────


def test_on_this_day_known_date():
    events = on_this_day(month=7, day=20)
    assert len(events) > 0
    for ev in events:
        assert "year" in ev
        assert "description" in ev
        assert isinstance(ev["year"], int)


def test_on_this_day_defaults():
    """Should work without args (defaults to today)."""
    events = on_this_day()
    assert len(events) > 0


# ── Related ────────────────────────────────────────────────────────────────


def test_get_related_articles():
    items = get_related_articles("Albert Einstein", limit=3)
    assert len(items) <= 3
    assert len(items) > 0
    for item in items:
        assert "title" in item
        assert "url" in item


def test_get_related_articles_missing():
    """Should return an empty list for non-existent article (not crash)."""
    items = get_related_articles("TotallyFakeArticle12345")
    assert items == []


# ── Categories ─────────────────────────────────────────────────────────────


def test_get_article_categories():
    cats = get_article_categories("Moon")
    assert len(cats) > 0
    assert all(isinstance(c, str) for c in cats)


def test_get_article_categories_missing():
    with pytest.raises(ArticleNotFound):
        get_article_categories("SomeFakePage99999")


# ── Error handling ─────────────────────────────────────────────────────────


def test_invalid_title_type():
    """Passing an empty string should raise an error."""
    with pytest.raises((ArticleNotFound, WikipediaError, Exception)):
        get_summary("")


def test_search_special_chars():
    """Should handle special characters gracefully."""
    results = search_articles("café résumé", limit=3)
    # Should not crash; may return results or empty
    assert isinstance(results, list)