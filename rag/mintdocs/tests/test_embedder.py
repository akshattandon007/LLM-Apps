"""Tests for the embedder module — simulated mode only (no sentence-transformers)."""

from mintdocs.embedder import Embedder
from mintdocs.models import Chunk, FilingMetadata
from datetime import date


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


class TestEmbedderSimulate:
    """Tests for the embedder in simulated mode.

    These tests do NOT require sentence-transformers to be installed.
    """

    def test_simulate_embed_text(self):
        """Simulated embedding should return a 384-dim vector."""
        embedder = Embedder(simulate=True)
        vec = embedder.embed_text("Apple faces supply chain risks in China.")
        assert len(vec) == 384
        assert all(isinstance(v, (int, float)) for v in vec)

    def test_simulate_embed_chunks(self):
        """embed_chunks should return (chunk, vector) pairs."""
        embedder = Embedder(simulate=True)
        chunks = [
            _make_chunk("The company operates globally."),
            _make_chunk("Risk factors include supply chain disruptions."),
        ]
        result = embedder.embed_chunks(chunks)
        assert len(result) == 2
        for chunk, vec in result:
            assert isinstance(chunk, Chunk)
            assert len(vec) == 384

    def test_simulate_deterministic(self):
        """Same text should produce the same simulated embedding."""
        embedder = Embedder(simulate=True)
        text = "Revenue grew 5% year over year."
        vec1 = embedder.embed_text(text)
        vec2 = embedder.embed_text(text)
        assert vec1 == vec2

    def test_simulate_different_text_different_vector(self):
        """Different texts should (almost certainly) produce different vectors."""
        embedder = Embedder(simulate=True)
        vec_a = embedder.embed_text("Revenue grew 5%.")
        vec_b = embedder.embed_text("Supply chain risks in China.")
        assert vec_a != vec_b

    def test_simulate_values_in_range(self):
        """Simulated embedding values should be between 0 and 1."""
        embedder = Embedder(simulate=True)
        vec = embedder.embed_text("Test text for range checking.")
        assert all(0 <= v <= 1 for v in vec)

    def test_simulate_no_model_loaded(self):
        """Embedder should NOT load sentence-transformers in simulate mode."""
        embedder = Embedder(simulate=True)
        assert embedder._model is None
        embedder.embed_text("Should not trigger model load.")
        assert embedder._model is None