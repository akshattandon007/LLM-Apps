"""arXiv API client — search and fetch papers."""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from .models import ArxivPaper

ARXIV_QUERY_URL = "http://export.arxiv.org/api/query"
ARXIV_ABS_URL = "https://arxiv.org/abs"
ARXIV_PDF_URL = "https://arxiv.org/pdf"

_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject a mock client for testing."""
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client or httpx.Client()


def search_arxiv(
    query: str,
    max_results: int = 10,
    start: int = 0,
    sort_by: str = "relevance",
) -> list[ArxivPaper]:
    """Search arXiv and return paper metadata.

    Args:
        query: Search query with optional field prefixes (ti:, au:, abs:, cat:).
        max_results: Max results (up to 2000).
        start: Result offset for paging.
        sort_by: 'relevance', 'lastUpdatedDate', or 'submittedDate'.

    Returns:
        List of ArxivPaper objects.
    """
    params: dict[str, Any] = {
        "search_query": query,
        "start": start,
        "max_results": min(max_results, 2000),
        "sortBy": sort_by,
    }

    client = _get_client()
    resp = client.get(ARXIV_QUERY_URL, params=params)
    resp.raise_for_status()

    papers = _parse_feed(resp.text)

    # Be nice to arXiv — 3-second gap between requests
    time.sleep(3)

    return papers


def fetch_paper(arxiv_id: str) -> ArxivPaper | None:
    """Fetch a single paper by its arXiv ID."""
    client = _get_client()
    resp = client.get(ARXIV_QUERY_URL, params={"id_list": arxiv_id})
    resp.raise_for_status()

    papers = _parse_feed(resp.text)
    return papers[0] if papers else None


def _parse_feed(xml: str) -> list[ArxivPaper]:
    """Parse an Atom XML feed from arXiv."""
    root = ET.fromstring(xml)
    papers: list[ArxivPaper] = []

    for entry in root.findall("atom:entry", _NAMESPACES):
        arxiv_id = _get_text(entry, "atom:id", "").split("/")[-1]
        title = _clean_html(_get_text(entry, "atom:title", ""))
        abstract = _clean_html(_get_text(entry, "atom:summary", ""))
        published = _get_text(entry, "atom:published", "")
        updated = _get_text(entry, "atom:updated", "")

        authors: list[str] = []
        for author_elem in entry.findall("atom:author", _NAMESPACES):
            name = _get_text(author_elem, "atom:name", "")
            if name:
                authors.append(name)

        categories: list[str] = []
        for cat_elem in entry.findall("atom:category", _NAMESPACES):
            term = cat_elem.get("term", "")
            if term:
                categories.append(term)

        # Links
        pdf_url = ""
        abs_url = ""
        for link in entry.findall("atom:link", _NAMESPACES):
            href = link.get("href", "")
            rel = link.get("rel", "")
            title_attr = link.get("title", "")
            if "pdf" in title_attr.lower() or rel == "related":
                pdf_url = href
            elif rel == "alternate":
                abs_url = href

        if not pdf_url:
            pdf_url = f"{ARXIV_PDF_URL}/{arxiv_id}.pdf"
        if not abs_url:
            abs_url = f"{ARXIV_ABS_URL}/{arxiv_id}"

        papers.append(ArxivPaper(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            categories=categories,
            published=published,
            updated=updated,
            pdf_url=pdf_url,
            abs_url=abs_url,
        ))

    return papers


def _get_text(element: ET.Element, path: str, default: str = "") -> str:
    """Get text from a sub-element."""
    child = element.find(path, _NAMESPACES)
    return child.text.strip() if child is not None and child.text else default


def _clean_html(text: str) -> str:
    """Basic HTML tag stripping."""
    import re
    return re.sub(r"<[^>]+>", "", text).strip()