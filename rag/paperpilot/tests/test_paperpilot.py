"""Tests for PaperPilot."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from paperpilot.arxiv_client import search_arxiv, fetch_paper, _parse_feed
from paperpilot.indexer import PaperIndex
from paperpilot.models import ArxivPaper, Chunk, SearchHit


# ── Sample arXiv XML response ───────────────────────────────────────────

SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <entry>
    <id>http://arxiv.org/abs/2401.00001</id>
    <title>Test Paper: Attention Is All You Need</title>
    <summary>This paper introduces the Transformer model. It relies entirely on self-attention mechanisms without recurrence. Experiments show superior translation quality.</summary>
    <author><name>Jane Smith</name></author>
    <published>2024-01-01T00:00:00Z</published>
    <updated>2024-01-02T00:00:00Z</updated>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.LG"/>
    <link href="http://arxiv.org/abs/2401.00001" rel="alternate" type="text/html"/>
    <link href="http://arxiv.org/pdf/2401.00001" rel="related" type="application/pdf" title="PDF"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2402.00002</id>
    <title>Understanding Deep Learning</title>
    <summary>A comprehensive overview of deep learning techniques. Covers CNNs, RNNs, and transformers with practical examples and theoretical foundations.</summary>
    <author><name>John Doe</name></author>
    <published>2024-02-01T00:00:00Z</published>
    <updated>2024-02-02T00:00:00Z</updated>
    <arxiv:primary_category term="cs.LG"/>
    <category term="cs.LG"/>
    <link href="http://arxiv.org/abs/2402.00002" rel="alternate"/>
    <link href="http://arxiv.org/pdf/2402.00002" rel="related" title="pdf"/>
  </entry>
</feed>"""


# ── Tests: arXiv client ─────────────────────────────────────────────────


def test_parse_feed():
    """Test parsing of Atom XML feed."""
    papers = _parse_feed(SAMPLE_ATOM_XML)
    assert len(papers) == 2

    p1 = papers[0]
    assert p1.arxiv_id == "2401.00001"
    assert "Attention" in p1.title
    assert "Jane Smith" in p1.authors
    assert "self-attention" in p1.abstract
    assert "cs.CL" in p1.categories
    assert "pdf" in p1.pdf_url.lower()
    assert "arxiv.org" in p1.abs_url

    p2 = papers[1]
    assert p2.arxiv_id == "2402.00002"
    assert "Deep Learning" in p2.title
    assert "John Doe" in p2.authors
    assert len(p2.categories) == 1


def test_search_arxiv_mock():
    """Test search with mock HTTP client."""
    from paperpilot import arxiv_client

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SAMPLE_ATOM_XML)

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    arxiv_client.set_client(mock_client)

    try:
        papers = search_arxiv("test query", max_results=5)
        assert len(papers) == 2
        assert papers[0].title == "Test Paper: Attention Is All You Need"
    finally:
        arxiv_client.set_client(None)


def test_fetch_paper_mock():
    """Test single paper fetch with mock."""
    from paperpilot import arxiv_client

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SAMPLE_ATOM_XML)

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    arxiv_client.set_client(mock_client)

    try:
        paper = fetch_paper("2401.00001")
        assert paper is not None
        assert paper.arxiv_id == "2401.00001"
    finally:
        arxiv_client.set_client(None)


# ── Tests: Indexer ──────────────────────────────────────────────────────


@pytest.fixture
def sample_papers():
    return [
        ArxivPaper(
            arxiv_id="2401.00001",
            title="Attention Is All You Need",
            authors=["Jane Smith"],
            abstract="This paper introduces the Transformer model. It relies entirely on self-attention mechanisms without recurrence. Experiments on machine translation show that the Transformer achieves superior quality while being more parallelizable.",
            categories=["cs.CL", "cs.LG"],
            published="2024-01-01",
        ),
        ArxivPaper(
            arxiv_id="2402.00002",
            title="Understanding Deep Learning",
            authors=["John Doe"],
            abstract="A comprehensive overview of deep learning techniques. This book covers CNNs, RNNs, and transformers. Each chapter includes practical examples and theoretical foundations.",
            categories=["cs.LG"],
            published="2024-02-01",
        ),
    ]


def test_index_add_papers(sample_papers):
    """Test adding papers to index."""
    index = PaperIndex()
    added = index.add_papers(sample_papers)
    assert added > 0
    assert index.paper_count == 2
    assert index.chunk_count == added


def test_index_search(sample_papers):
    """Test searching indexed papers."""
    index = PaperIndex()
    index.add_papers(sample_papers)

    hits = index.search("attention mechanism", k=2)
    assert len(hits) > 0
    assert all(isinstance(h, SearchHit) for h in hits)
    # First result should be about attention
    assert hits[0].score > -1.0  # cosine similarity range


def test_index_persistence(sample_papers):
    """Test save and load of index."""
    import paperpilot.indexer as idx_mod

    orig_dir = idx_mod.INDEX_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            idx_mod.INDEX_DIR = Path(tmp)

            index = PaperIndex()
            index.add_papers(sample_papers)
            index.save()

            # New instance should load
            index2 = PaperIndex()
            loaded = index2.load()
            assert loaded
            assert index2.paper_count == 2
    finally:
        idx_mod.INDEX_DIR = orig_dir


def test_list_papers(sample_papers):
    """Test listing indexed papers."""
    index = PaperIndex()
    index.add_papers([sample_papers[0]])

    papers = index.list_papers()
    assert len(papers) == 1
    assert papers[0]["id"] == "2401.00001"
    assert "Attention" in papers[0]["title"]


# ── Tests: LLM module ───────────────────────────────────────────────────


def test_query_papers_no_hits():
    """Test query with no context."""
    from paperpilot.llm import query_papers
    result = query_papers("test", [])
    assert "No relevant papers found" in result


def test_query_papers_with_hits():
    """Test query with context (uses mock LLM)."""
    from paperpilot.llm import query_papers

    chunk = Chunk(text="Transformers use attention mechanisms.", paper_id="2401.00001",
                  title="Attention Paper", chunk_index=0)
    hit = SearchHit(chunk=chunk, score=0.95)

    with patch("paperpilot.llm._get_client") as mock_get:
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Transformers use attention mechanisms."
        mock_resp.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_resp
        mock_get.return_value = mock_client

        result = query_papers("How do transformers work?", [hit])
        assert "attention" in result.lower()


# ── Tests: Model ────────────────────────────────────────────────────────


def test_arxiv_paper_short_id():
    """Test short_id property."""
    p = ArxivPaper(arxiv_id="2401.00001", title="Test")
    assert p.short_id == "2401.00001"

    p2 = ArxivPaper(arxiv_id="arxiv:2401.00001", title="Test")
    assert p2.short_id == "2401.00001"