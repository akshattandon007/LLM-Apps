"""Tests for the indexer module — building and loading indices."""

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest

from mintdocs.indexer import Indexer, IndexerError
from mintdocs.models import Chunk, FilingMetadata


def _make_chunk(text: str, header: str = "Item 1: Business") -> Chunk:
    return Chunk(
        section_header=header,
        section_text=text,
        metadata=FilingMetadata(
            company_name="Apple Inc.",
            ticker="AAPL",
            cik="0000320193",
            filing_type="10-K",
            filing_date=date.fromisoformat("2024-10-31"),
            accession_number="000032019324000001",
            primary_doc="https://www.sec.gov/...",
        ),
    )


class TestIndexerSimulate:
    """Tests for the indexer in simulated mode (no FAISS)."""

    def test_build_index_creates_metadata(self, tmp_path: Path):
        """build_index should create a metadata.json file."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)

        chunks_with_emb = [
            (_make_chunk("The company operates globally.", "Item 1: Business"), [0.1] * 384),
            (_make_chunk("Risk factors include supply chain.", "Item 1A: Risk Factors"), [0.2] * 384),
        ]

        result_dir = indexer.build_index(chunks_with_emb, ticker="AAPL")
        assert result_dir.exists()
        assert (result_dir / "metadata.json").exists()

    def test_metadata_content(self, tmp_path: Path):
        """Metadata JSON should contain the correct fields."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)

        chunks_with_emb = [
            (_make_chunk("Business text here.", "Item 1: Business"), [0.1] * 384),
        ]

        indexer.build_index(chunks_with_emb, ticker="AAPL")

        meta_path = index_dir / "AAPL" / "metadata.json"
        data = json.loads(meta_path.read_text())
        assert len(data) == 1
        entry = data[0]
        assert entry["section_header"] == "Item 1: Business"
        assert entry["section_text"] == "Business text here."
        assert entry["company_name"] == "Apple Inc."
        assert entry["ticker"] == "AAPL"
        assert entry["filing_type"] == "10-K"
        assert entry["filing_date"] == "2024-10-31"

    def test_load_metadata(self, tmp_path: Path):
        """load_metadata should return Chunk objects matching what was stored."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)

        chunks_with_emb = [
            (_make_chunk("Business text.", "Item 1: Business"), [0.1] * 384),
            (_make_chunk("Risk factors text.", "Item 1A: Risk Factors"), [0.2] * 384),
        ]
        indexer.build_index(chunks_with_emb, ticker="AAPL")

        loaded = indexer.load_metadata("AAPL")
        assert len(loaded) == 2
        assert loaded[0].section_header == "Item 1: Business"
        assert loaded[1].section_header == "Item 1A: Risk Factors"
        assert loaded[0].section_text == "Business text."
        assert loaded[1].section_text == "Risk factors text."
        assert loaded[0].metadata.company_name == "Apple Inc."

    def test_index_exists(self, tmp_path: Path):
        """index_exists returns True/False correctly."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)
        assert not indexer.index_exists("AAPL")

        chunks_with_emb = [
            (_make_chunk("Text.", "Item 1: Business"), [0.1] * 384),
        ]
        indexer.build_index(chunks_with_emb, ticker="AAPL")
        assert indexer.index_exists("AAPL")
        assert not indexer.index_exists("MSFT")

    def test_list_indexed_tickers(self, tmp_path: Path):
        """list_indexed_tickers returns all tickers with metadata."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)

        assert indexer.list_indexed_tickers() == []

        c1 = [(_make_chunk("Apple text.", "Item 1"), [0.1] * 384)]
        c2 = [(_make_chunk("MS text.", "Item 1"), [0.1] * 384)]
        indexer.build_index(c1, ticker="AAPL")
        indexer.build_index(c2, ticker="MSFT")

        tickers = indexer.list_indexed_tickers()
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_load_metadata_raises_on_missing(self, tmp_path: Path):
        """load_metadata should raise IndexerError when no index exists."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)
        with pytest.raises(IndexerError, match="No metadata"):
            indexer.load_metadata("AAPL")

    def test_no_faiss_file_in_simulate(self, tmp_path: Path):
        """Simulated index should NOT create a FAISS file."""
        index_dir = tmp_path / "indices"
        indexer = Indexer(index_dir=index_dir, simulate=True)

        chunks_with_emb = [
            (_make_chunk("Text.", "Item 1"), [0.1] * 384),
        ]
        indexer.build_index(chunks_with_emb, ticker="AAPL")
        assert not (index_dir / "AAPL" / "index.faiss").exists()