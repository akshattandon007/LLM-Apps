"""Answer-builder tests: citations and key dates must appear in output."""
from datetime import date
from pathlib import Path

from schoolsift.answer import build_answer
from schoolsift.index import build
from schoolsift.ingest import ingest_folder
from schoolsift.search import search

TODAY = date(2026, 10, 12)


def _ask(folder: Path, question: str):
    store = build(ingest_folder(folder))
    return build_answer(
        store, question, search(store, question),
        today=TODAY,
    )


def test_answer_cites_source_and_dates(sample_folder: Path):
    out = _ask(sample_folder, "when is the science fair")
    assert "Science Fair" in out
    assert "permission-slip-science-fair" in out
    assert "p.1" in out
    assert "2026-11-20" in out          # science fair date
    assert "2026-10-28" in out          # slip due date
    assert "deadline" in out.lower()


def test_answer_contains_direct_sentence(sample_folder: Path):
    out = _ask(sample_folder, "when is the science fair")
    assert "will take place on November 20" in out


def test_answer_does_not_quote_title_fragment(sample_folder: Path):
    # The permission slip's title sits on its own line inside the chunk. The
    # answer must quote the date-carrying sentence, not the title fragment.
    out = _ask(sample_folder, "when is the science fair")
    answer_line = out.splitlines()[1]  # "A: ..."
    assert answer_line.startswith("A: The Maplewood Science Fair"), answer_line
    assert "A: Science Fair Permission Slip" not in out


def test_answer_book_fair_from_newsletter(sample_folder: Path):
    out = _ask(sample_folder, "when is the book fair")
    assert "Book Fair" in out
    assert "2026-10-14" in out
    assert "newsletter-october" in out


def test_answer_no_hits_message():
    out = build_answer(None, "quantum astrophysics", [], today=TODAY)
    assert "couldn't find" in out


def test_answer_deduplicates_dates(sample_folder: Path):
    out = _ask(sample_folder, "book fair")
    # October 14 appears once in the Key dates block.
    dates_block = out.split("Key dates found")[1] if "Key dates found" in out else ""
    assert dates_block.count("2026-10-14") <= 1