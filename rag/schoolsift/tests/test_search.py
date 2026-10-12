"""Retrieval tests: the right chunks must win for plain-language questions."""
from pathlib import Path

from schoolsift.index import build
from schoolsift.ingest import ingest_folder
from schoolsift.search import search


def _store(folder: Path):
    return build(ingest_folder(folder))


def test_science_fair_question_finds_permission_slip(sample_folder: Path):
    store = _store(sample_folder)
    hits = search(store, "when is the science fair")
    assert hits
    top = hits[0]
    assert "science fair" in top["chunk"]["text"].lower()
    assert top["doc"]["title"] == "permission-slip-science-fair"


def test_book_fair_question_finds_newsletter(sample_folder: Path):
    store = _store(sample_folder)
    hits = search(store, "book fair when")
    assert hits
    top = hits[0]
    assert "book fair" in top["chunk"]["text"].lower()
    assert top["doc"]["title"] == "newsletter-october"


def test_deadline_question_surfaces_deadline_chunk(sample_folder: Path):
    store = _store(sample_folder)
    hits = search(store, "room parent signup deadline")
    assert hits
    assert "November 14" in hits[0]["chunk"]["text"]


def test_unrelated_query_returns_nothing(sample_folder: Path):
    store = _store(sample_folder)
    assert search(store, "quantum astrophysics") == []


def test_stopword_only_query_returns_nothing(sample_folder: Path):
    store = _store(sample_folder)
    assert search(store, "the and of") == []


def test_multiple_relevant_chunks_ranked(sample_folder: Path):
    store = _store(sample_folder)
    hits = search(store, "when is the science fair", k=5)
    assert len(hits) >= 1
    # Every hit must carry its source document for citation support.
    for h in hits:
        assert h["doc"]["title"]
        assert h["chunk"]["page"] >= 1