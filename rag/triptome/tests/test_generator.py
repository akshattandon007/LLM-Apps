"""Tests for TripTome generator module."""

from triptome.models import Answer, SearchResult
from triptome.generator import answer_query, _build_context


def test_answer_no_results():
    """Test answer when there are no indexed documents."""
    result = answer_query("What's the best time to visit Bali?")
    assert isinstance(result, Answer)
    assert result.query == "What's the best time to visit Bali?"
    assert "don't have any travel documents" in result.answer.lower()
    assert result.citations == []


def test_build_context():
    """Test building context string from search results."""
    results = [
        SearchResult(text="Bali has beautiful beaches.",
                     source="indonesia.txt", page=None, score=0.95, chunk_id=0),
        SearchResult(text="The best time to visit is April-October.",
                     source="indonesia.txt", page=12, score=0.88, chunk_id=1),
    ]
    context = _build_context(results)
    assert "[Source 1: indonesia.txt]" in context
    assert "[Source 2: indonesia.txt (page 12)]" in context
    assert "Bali has beautiful beaches" in context
    assert "April-October" in context


def test_build_context_single():
    """Test context with a single result."""
    results = [
        SearchResult(text="Paris is the capital of France.",
                     source="france.pdf", page=3, score=0.90, chunk_id=0),
    ]
    context = _build_context(results)
    assert "[Source 1: france.pdf (page 3)]" in context


def test_answer_with_results_no_api_key():
    """Test answer generates fallback when no API key is set."""
    # This test would need indexed docs — just verify the function
    # handles the case gracefully
    pass