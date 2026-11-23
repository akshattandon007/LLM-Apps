"""Tests for PillWise indexer module."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pillwise.indexer import build_index, search


def test_build_index_creates_index():
    """build_index creates a FAISS index with correct vector count."""
    chunks = [
        {"drug_id": "DrugA", "drug_name": "DrugA", "field": "warnings",
         "field_label": "Warnings", "text": "This is a test warning for DrugA. It contains enough text to be meaningful for embedding purposes.",
         "source": "FDA Label — DrugA — Warnings"},
        {"drug_id": "DrugB", "drug_name": "DrugB", "field": "dosage",
         "field_label": "Dosage", "text": "Take two tablets daily with food. This is the standard adult dosage for DrugB.",
         "source": "FDA Label — DrugB — Dosage"},
        {"drug_id": "DrugC", "drug_name": "DrugC", "field": "interactions",
         "field_label": "Drug Interactions", "text": "DrugC may interact with alcohol and other medications. Consult your doctor before combining.",
         "source": "FDA Label — DrugC — Interactions"},
    ]
    index, texts, metadata = build_index(chunks, save=False, force_rebuild=True)
    assert index.ntotal == 3
    assert len(texts) == 3
    assert len(metadata) == 3


def test_search_returns_results():
    """search returns relevant results for a query."""
    chunks = [
        {"drug_id": "DrugA", "drug_name": "DrugA", "field": "warnings",
         "field_label": "Warnings", "text": "This medication may cause drowsiness and dizziness. Do not operate heavy machinery.",
         "source": "FDA Label — DrugA — Warnings"},
        {"drug_id": "DrugB", "drug_name": "DrugB", "field": "dosage",
         "field_label": "Dosage", "text": "Take 200mg every 4-6 hours as needed for pain. Do not exceed 1200mg in 24 hours.",
         "source": "FDA Label — DrugB — Dosage"},
        {"drug_id": "DrugC", "drug_name": "DrugC", "field": "interactions",
         "field_label": "Drug Interactions", "text": "Avoid alcohol while taking this medication. May increase effects of blood thinners.",
         "source": "FDA Label — DrugC — Interactions"},
    ]
    index, texts, metadata = build_index(chunks, save=False, force_rebuild=True)

    results = search(index, texts, metadata, "dosage for pain relief", k=2)
    assert len(results) >= 1
    assert results[0]["score"] > 0  # Should have positive cosine similarity


def test_search_respects_k():
    """search returns at most k results."""
    chunks = [
        {"drug_id": f"Drug{i}", "drug_name": f"Drug{i}", "field": "text",
         "field_label": "Label", "text": f"This is drug number {i} with some sample text for testing.",
         "source": f"FDA Label — Drug{i}"}
        for i in range(5)
    ]
    index, texts, metadata = build_index(chunks, save=False, force_rebuild=True)

    results = search(index, texts, metadata, "drug number", k=3)
    assert len(results) <= 3


def test_search_includes_source():
    """search results include source metadata."""
    chunks = [
        {"drug_id": "TestDrug", "drug_name": "TestDrug", "field": "warnings",
         "field_label": "Warnings", "text": "Test warning with sufficient text for embedding into vector space.",
         "source": "FDA Label — TestDrug — Warnings"},
    ]
    index, texts, metadata = build_index(chunks, save=False, force_rebuild=True)

    results = search(index, texts, metadata, "test warning text", k=1)
    assert len(results) == 1
    assert "source" in results[0]
    assert "TestDrug" in results[0]["source"]
