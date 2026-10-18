"""Tests for TripTome indexer module."""

import tempfile
from pathlib import Path
from triptome.indexer import ingest_file, ingest_directory, _split_text
from triptome.models import Document


def test_split_text_basic():
    """Test basic text splitting into chunks."""
    text = """Paris is the capital of France.

It is known for its art, fashion, and culture.

The Eiffel Tower is the most famous landmark.

The Louvre Museum houses the Mona Lisa."""
    docs = _split_text(text, "test.txt", chunk_size=15, overlap=3)
    assert len(docs) > 1, "Should produce multiple chunks"
    assert all(isinstance(d, Document) for d in docs)
    assert all(d.source == "test.txt" for d in docs)


def test_split_text_small_chunk():
    """Test with very small chunk size to force many splits."""
    text = """Tokyo is the capital of Japan.

It is a vibrant city with amazing food.

The Shibuya crossing is world famous."""
    docs = _split_text(text, "tokyo.txt", chunk_size=5, overlap=1)
    assert len(docs) >= 2, "Should split into at least 2 chunks"


def test_split_text_empty():
    """Test with empty text."""
    docs = _split_text("", "empty.txt")
    assert docs == [], "Empty text should produce no chunks"


def test_split_text_single_para():
    """Test with a single paragraph (no blank-line breaks)."""
    text = "Bangkok. Chiang Mai. Phuket. These are the top three destinations in Thailand."
    docs = _split_text(text, "thailand.txt", chunk_size=10, overlap=2)
    assert len(docs) >= 1


def test_ingest_txt_file():
    """Test ingesting a .txt file."""
    with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", delete=False, encoding="utf-8") as f:
        f.write("Bali is an Indonesian island.\n\n"
                "It is known for its forested volcanic mountains.\n\n"
                "The island is a popular tourist destination.")
        tmp_path = f.name

    try:
        docs = ingest_file(Path(tmp_path), chunk_size=20, overlap=3)
        assert len(docs) >= 1
        assert docs[0].source == Path(tmp_path).name
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_ingest_md_file():
    """Test ingesting a .md file."""
    with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write("# Italy Travel Guide\n\n"
                "## Rome\n\n"
                "Rome is the capital city.\n\n"
                "## Florence\n\n"
                "Florence is known for Renaissance art.")
        tmp_path = f.name

    try:
        docs = ingest_file(Path(tmp_path))
        assert len(docs) >= 1
        assert docs[0].source == Path(tmp_path).name
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_ingest_unsupported():
    """Test ingesting an unsupported file type raises ValueError."""
    with tempfile.NamedTemporaryFile(
            suffix=".csv", mode="w", delete=False) as f:
        f.write("city,country\nParis,France")
        tmp_path = f.name

    try:
        import pytest
        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_file(Path(tmp_path))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_ingest_directory():
    """Test ingesting a directory with multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        (d / "japan.txt").write_text(
            "Tokyo is the capital of Japan.\n\n"
            "Osaka is known for street food.\n\n"
            "Kyoto has ancient temples.", encoding="utf-8")
        (d / "france.md").write_text(
            "# France\n\n"
            "Paris is the capital.\n\n"
            "Lyon is the gastronomy capital.", encoding="utf-8")

        docs = ingest_directory(d)
        assert len(docs) >= 2
        sources = set(doc.source for doc in docs)
        assert "japan.txt" in sources
        assert "france.md" in sources