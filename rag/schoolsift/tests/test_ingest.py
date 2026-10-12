"""Ingestion tests: PDF/txt extraction and chunking behavior."""
from pathlib import Path

from schoolsift.ingest import (
    CHUNK_MAX,
    chunk_page,
    extract_pages,
    ingest_folder,
)


def test_extract_pdf_pages(newsletter_pdf: Path):
    pages = extract_pages(newsletter_pdf)
    assert len(pages) == 2
    assert "Book Fair" in pages[0]["text"]
    assert pages[0]["number"] == 1 and pages[1]["number"] == 2


def test_extract_txt_single_page(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("hello there", encoding="utf-8")
    pages = extract_pages(p)
    assert len(pages) == 1
    assert pages[0]["number"] == 1
    assert "hello" in pages[0]["text"]


def test_chunk_metadata_and_size():
    chunks = chunk_page("spam and eggs " * 80, 3)
    assert chunks
    assert all(c["page"] == 3 for c in chunks)
    assert all(len(c["text"]) <= CHUNK_MAX + 20 for c in chunks)


def test_empty_page_yields_no_chunks():
    assert chunk_page("   \n  ", 2) == []


def test_ingest_folder(sample_folder: Path):
    docs = ingest_folder(sample_folder)
    assert len(docs) == 3
    by_title = {d["title"]: d for d in docs}
    assert "newsletter-october" in by_title
    assert by_title["newsletter-october"]["pages"] == 2
    assert all(
        c["page"] in (1, 2)
        for c in by_title["newsletter-october"]["chunks"]
    )
    assert by_title["permission-slip-science-fair"]["pages"] == 1
    assert "pta-notes" in by_title