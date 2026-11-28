"""Tests for the chunker module — section-level splitting of SEC filing text."""

from datetime import date

from mintdocs.chunker import chunk_filing
from mintdocs.models import FilingMetadata


def _make_metadata(
    ticker="AAPL",
    company="Apple Inc.",
    filing_type="10-K",
    filing_date="2024-10-31",
    accession="000032019324000001",
):
    return FilingMetadata(
        company_name=company,
        ticker=ticker,
        cik="0000320193",
        filing_type=filing_type,
        filing_date=date.fromisoformat(filing_date),
        accession_number=accession,
        primary_doc="https://www.sec.gov/...",
    )


SAMPLE_10K = """
UNITED STATES SECURITIES AND EXCHANGE COMMISSION
FORM 10-K

Item 1. Business
Apple Inc. designs, manufactures and markets smartphones,
personal computers, tablets, wearables and accessories worldwide.

Item 1A. Risk Factors
The Company's operations are subject to global economic conditions.
Supply chain disruptions concentrated in Asia could impact manufacturing.
The Company faces intense competition in all markets.

Item 1B. Unresolved Staff Comments
None.

Item 2. Properties
The Company leases and owns facilities worldwide.

Item 7. Management's Discussion and Analysis
Revenue for fiscal year 2024 was $391.0 billion.
Net income was $97.0 billion.

Item 8. Financial Statements
See consolidated financial statements.
"""

SAMPLE_10Q = """
Item 1. Financial Statements
Revenue was $94.8 billion for the quarter.

Item 2. Management's Discussion and Analysis
Revenue increased 5% year over year.

Item 1A. Risk Factors
There have been no material changes to risk factors.
"""


class TestChunkFiling:
    """Tests for chunk_filing on simulated filing text."""

    def test_chunks_10k_sections(self):
        """A 10-K filing should be split into section chunks."""
        meta = _make_metadata()
        chunks = chunk_filing(SAMPLE_10K, meta)
        # Should produce chunks for Business, Risk Factors, Properties, MD&A, Financial
        headers = [c.section_header for c in chunks]
        assert "Item 1: Business" in headers
        assert "Item 1A: Risk Factors" in headers
        assert "Item 2: Properties" in headers
        assert any("Item 7" in h for h in headers)
        assert "Item 8: Financial Statements" in headers

    def test_chunks_have_metadata(self):
        """Each chunk should carry its filing metadata."""
        meta = _make_metadata()
        chunks = chunk_filing(SAMPLE_10K, meta)
        for chunk in chunks:
            assert chunk.metadata.ticker == "AAPL"
            assert chunk.metadata.company_name == "Apple Inc."
            assert chunk.metadata.filing_type == "10-K"

    def test_chunks_have_text_content(self):
        """Each chunk should contain its section's text."""
        meta = _make_metadata()
        chunks = chunk_filing(SAMPLE_10K, meta)
        risk_chunk = [c for c in chunks if "Risk Factors" in c.section_header]
        assert len(risk_chunk) == 1
        assert "supply chain" in risk_chunk[0].section_text.lower()

    def test_skips_admin_sections(self):
        """Administrative sections like 'None' or 'Not applicable' should be skipped."""
        meta = _make_metadata()
        chunks = chunk_filing(SAMPLE_10K, meta)
        headers = [c.section_header for c in chunks]
        # "Item 1B: Unresolved Staff Comments" is "None" content — should be skipped
        assert "Item 1B: Unresolved Staff Comments" not in headers

    def test_10q_chunking(self):
        """10-Q filings should also be split correctly."""
        meta = _make_metadata(filing_type="10-Q", filing_date="2024-07-27")
        chunks = chunk_filing(SAMPLE_10Q, meta)
        headers = [c.section_header for c in chunks]
        assert "Item 1: Financial Statements" in headers
        assert any("Item 2: Management" in h for h in headers)
        assert "Item 1A: Risk Factors" in headers

    def test_empty_text_returns_no_chunks(self):
        """Empty or very short text should return an empty list."""
        meta = _make_metadata()
        chunks = chunk_filing("   ", meta)
        assert len(chunks) == 0

    def test_no_section_headers(self):
        """Text with no Item headers becomes one 'Full Filing' chunk."""
        meta = _make_metadata()
        chunks = chunk_filing("Some random financial text that is long enough to keep.", meta)
        assert len(chunks) == 1
        assert chunks[0].section_header == "Full Filing"

    def test_chunk_to_dict_roundtrip(self):
        """Chunk.to_dict and Chunk.from_dict should round-trip cleanly."""
        meta = _make_metadata()
        chunks = chunk_filing(SAMPLE_10K, meta)
        for chunk in chunks:
            d = chunk.to_dict()
            restored = type(chunk).from_dict(d)
            assert restored.section_header == chunk.section_header
            assert restored.section_text == chunk.section_text
            assert restored.metadata.ticker == chunk.metadata.ticker