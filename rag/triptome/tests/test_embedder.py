"""Tests for TripTome embedder (vector store) module."""

import tempfile
from pathlib import Path
from triptome.models import Document
from triptome.embedder import index_documents, search, get_stats, reset


def test_index_and_search():
    """Test basic index → search round trip."""
    reset()
    docs = [
        Document(text="Paris is the capital of France. It has the Eiffel Tower.",
                 source="france.txt", chunk_id=0),
        Document(text="Tokyo is the capital of Japan. It has Shibuya crossing.",
                 source="japan.txt", chunk_id=1),
        Document(text="Sydney is a city in Australia with the Opera House.",
                 source="australia.txt", chunk_id=2),
    ]
    count = index_documents(docs)
    assert count == 3, "Should have indexed 3 documents"

    # Search for Paris
    results = search("Eiffel Tower", n_results=2)
    assert len(results) > 0, "Should find at least one result"
    top = results[0]
    assert "Paris" in top.text or "Eiffel" in top.text
    assert top.score > 0.3

    # Search for Japan
    results = search("Japan city", n_results=2)
    assert len(results) > 0
    assert any("Tokyo" in r.text for r in results)

    # Check stats
    stats = get_stats()
    assert stats["total_chunks"] >= 3
    assert "france.txt" in stats["sources"]


def test_search_empty():
    """Test search when nothing is indexed (after reset)."""
    reset()
    results = search("anything", n_results=2)
    assert results == []


def test_index_duplicate_ids():
    """Test indexing documents with the same source but different content."""
    reset()
    docs = [
        Document(text="London has the Tower Bridge.", source="uk.txt", chunk_id=0),
        Document(text="London has Buckingham Palace.", source="uk.txt", chunk_id=1),
    ]
    count = index_documents(docs)
    assert count == 2

    # Search
    results = search("Tower Bridge", n_results=2)
    tower_results = [r for r in results if "Tower Bridge" in r.text]
    assert len(tower_results) >= 1


def test_get_stats_empty():
    """Test stats on an empty collection."""
    reset()
    stats = get_stats()
    assert stats["total_chunks"] == 0
    assert stats["sources"] == []
    assert stats["source_count"] == 0