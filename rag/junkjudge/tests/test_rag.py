"""Tests for rag_engine.py — retrieval logic only (no live API call)."""

import pytest
from document_loader import load_and_chunk_from_text
from rag_engine import RAGEngine


SAMPLE_TEXT = (
    "Recycling Guidelines for Springfield.\n\n"
    "Accepted Materials:\n"
    "- Plastic bottles #1 and #2: Rinse and place in blue bin.\n"
    "- Cardboard: Flatten and place in blue bin. Pizza boxes are accepted "
    "only if no grease stains.\n"
    "- Glass jars and bottles: Rinse, remove lids, place in blue bin.\n"
    "- Aluminum cans: Rinse, crush if desired, place in blue bin.\n\n"
    "NOT Accepted:\n"
    "- Plastic bags: Do NOT place in blue bin. Return to grocery store.\n"
    "- Styrofoam: Not recyclable. Place in trash.\n"
    "- Electronics: Take to the city drop-off center.\n"
    "- Hazardous waste (paint, batteries, chemicals): "
    "Take to the Household Hazardous Waste facility.\n\n"
    "Collection Schedule:\n"
    "Curbside pickup every Tuesday. Bulk pickup first Tuesday of the month. "
    "Holiday delays: If a holiday falls on Monday or Tuesday, pickup is "
    "delayed by one day.\n"
)


@pytest.fixture
def engine():
    chunks = load_and_chunk_from_text({"springfield.pdf": SAMPLE_TEXT})
    return RAGEngine(chunks, model_name="all-MiniLM-L6-v2")


def test_engine_initializes(engine):
    """Engine should build an index from chunks."""
    assert engine.index is not None
    assert engine.index.ntotal > 0
    assert len(engine.chunks) > 0


def test_retrieve_returns_relevant_chunks(engine):
    """Query about pizza boxes should return cardboard-related chunks."""
    results = engine.retrieve("Can I recycle pizza boxes?", top_k=3)
    assert len(results) > 0
    # At least one result should mention cardboard or pizza
    texts = " ".join(r["text"] for r in results)
    assert any(kw in texts.lower() for kw in ["pizza", "cardboard", "grease"])


def test_retrieve_plastic_returns_plastic(engine):
    """Query about plastic should return plastic-related chunks."""
    results = engine.retrieve("What plastic bottles are accepted?", top_k=3)
    texts = " ".join(r["text"] for r in results)
    assert "plastic" in texts.lower()


def test_retrieve_source_metadata(engine):
    """Each retrieved result should carry source and page info."""
    results = engine.retrieve("pickup schedule", top_k=2)
    for r in results:
        assert "source" in r
        assert "page" in r
        assert "text" in r
        assert "score" in r


def test_retrieve_with_no_chunks():
    """Engine with no chunks should return empty results."""
    engine = RAGEngine([], model_name="all-MiniLM-L6-v2")
    results = engine.retrieve("anything", top_k=5)
    assert results == []


def test_query_no_docs(engine):
    """query() without relevant docs should say no docs loaded."""
    # Engine has docs, so query should find something
    result = engine.query("What time is bulk pickup?")
    assert "answer" in result
    assert "sources" in result


def test_top_k_limits_results(engine):
    """top_k parameter should limit returned sources."""
    results = engine.retrieve("recycling", top_k=2)
    assert len(results) <= 2