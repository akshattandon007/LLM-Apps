"""
tests/test_document_loader.py
──────────────────────────────
Unit tests for the document_loader module.
Uses unittest.mock to avoid real HTTP calls.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from document_loader import (
    _clean_text,
    _collect_links,
    _extract_text_from_html,
    _same_domain,
    load_documents_from_url,
)

# ── _clean_text ───────────────────────────────────────────────────────────────

def test_clean_text_collapses_whitespace():
    raw = "  Hello  \n\n  World  \n   "
    result = _clean_text(raw)
    assert "Hello" in result
    assert "World" in result


def test_clean_text_removes_short_lines():
    raw = "a\n\nReal content here that is long enough"
    result = _clean_text(raw)
    # 'a' should be filtered (len <= 2)
    assert "a\n" not in result
    assert "Real content" in result


# ── _same_domain ──────────────────────────────────────────────────────────────

def test_same_domain_true():
    assert _same_domain(
        "https://developers.facebook.com/docs/",
        "https://developers.facebook.com/docs/graph-api/",
    )


def test_same_domain_false():
    assert not _same_domain(
        "https://developers.facebook.com/docs/",
        "https://example.com/page",
    )


# ── _collect_links ────────────────────────────────────────────────────────────

SAMPLE_HTML = """
<html><body>
  <a href="/docs/graph-api/">Graph API</a>
  <a href="https://developers.facebook.com/docs/messenger/">Messenger</a>
  <a href="https://external.com/page">External</a>
  <a href="/docs/graph-api/#section">Anchor</a>
</body></html>
"""

def test_collect_links_stays_on_domain():
    base = "https://developers.facebook.com/docs/"
    links = _collect_links(SAMPLE_HTML, base)
    assert all("developers.facebook.com" in l for l in links)
    # External link should be excluded
    assert not any("external.com" in l for l in links)


def test_collect_links_strips_anchors():
    base = "https://developers.facebook.com/docs/"
    links = _collect_links(SAMPLE_HTML, base)
    assert not any("#" in l for l in links)


def test_collect_links_deduplicates():
    base = "https://developers.facebook.com/docs/"
    links = _collect_links(SAMPLE_HTML, base)
    assert len(links) == len(set(links))


# ── _extract_text_from_html ───────────────────────────────────────────────────

CONTENT_HTML = """
<html>
<head><title>Graph API Reference</title></head>
<body>
  <nav>Navigation links here</nav>
  <main>
    <h1>Graph API</h1>
    <p>The Graph API is the primary way to read and write to the Facebook social graph.</p>
    <p>To use it, send HTTP requests to the endpoint.</p>
  </main>
  <footer>Footer content</footer>
</body>
</html>
"""

def test_extract_text_contains_main_content():
    text = _extract_text_from_html(CONTENT_HTML, "https://example.com")
    assert "Graph API" in text
    assert "Facebook social graph" in text


def test_extract_text_removes_nav_and_footer():
    text = _extract_text_from_html(CONTENT_HTML, "https://example.com")
    # nav and footer should be stripped
    assert "Navigation links here" not in text
    assert "Footer content" not in text


# ── load_documents_from_url (integration with mock) ──────────────────────────

MOCK_HTML = """
<html>
<head><title>Facebook Graph API</title></head>
<body>
  <main>
    <h1>Graph API Overview</h1>
    <p>The Graph API is the primary way for apps to read and write to the Facebook
    social graph. The Graph API is named after the idea of a "social graph" —
    a representation of the information on Facebook.</p>
    <h2>Endpoints</h2>
    <p>All endpoints accept GET and POST requests and are available at
    https://graph.facebook.com/{version}/{node-id}.</p>
  </main>
</body>
</html>
"""


@patch("document_loader.requests.get")
def test_load_documents_returns_chunks(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_resp.text = MOCK_HTML
    mock_resp.url = "https://developers.facebook.com/docs/"
    mock_get.return_value = mock_resp

    docs = load_documents_from_url(
        "https://developers.facebook.com/docs/",
        chunk_size=300,
        chunk_overlap=50,
        crawl=False,  # Don't follow links in test
    )
    assert len(docs) >= 1
    # All chunks should have source metadata
    for doc in docs:
        assert "source" in doc.metadata


@patch("document_loader.requests.get")
def test_load_documents_raises_on_empty_page(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.text = "<html><body></body></html>"
    mock_resp.url = "https://example.com"
    mock_get.return_value = mock_resp

    with pytest.raises(ValueError, match="No content"):
        load_documents_from_url(
            "https://example.com",
            crawl=False,
        )
