"""Parallel search agents — web, arXiv, HN, and blog search.

Each searcher is an independent function with an injectable _client for testing.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models import SearchResult, SourceType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Web search (DuckDuckGo)
# ---------------------------------------------------------------------------

_web_client = None


def set_web_client(client):
    global _web_client
    _web_client = client


def _get_web_client():
    return _web_client


def search_web(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search the web using DuckDuckGo."""
    client = _get_web_client()
    if client is not None:
        return client.search(query, source=SourceType.WEB)

    # Real implementation using duckduckgo_search
    results = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source=SourceType.WEB,
                        source_name=r.get("source", "web"),
                        published=None,
                        relevance_score=1.0 - (i * 0.1) if i < 10 else 0.0,
                    )
                )
    except Exception as e:
        logger.warning("Web search failed: %s", e)
    return results


# ---------------------------------------------------------------------------
# arXiv search
# ---------------------------------------------------------------------------

_arxiv_client = None


def set_arxiv_client(client):
    global _arxiv_client
    _arxiv_client = client


def _get_arxiv_client():
    return _arxiv_client


def search_arxiv(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search arXiv for academic papers."""
    client = _get_arxiv_client()
    if client is not None:
        return client.search(query, source=SourceType.ARXIV)

    results = []
    try:
        import feedparser

        encoded = query.replace(" ", "+")
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}&max_results={max_results}&sortBy=relevance"
        feed = feedparser.parse(url)
        for i, entry in enumerate(feed.entries):
            results.append(
                SearchResult(
                    title=entry.get("title", "").replace("\n", " ").strip(),
                    url=entry.get("link", ""),
                    snippet=entry.get("summary", "").replace("\n", " ").strip()[:300],
                    source=SourceType.ARXIV,
                    source_name="arXiv",
                    published=entry.get("published", ""),
                    relevance_score=1.0 - (i * 0.1) if i < 10 else 0.0,
                )
            )
    except Exception as e:
        logger.warning("arXiv search failed: %s", e)
    return results


# ---------------------------------------------------------------------------
# Hacker News (Algolia API)
# ---------------------------------------------------------------------------

_hn_client = None


def set_hn_client(client):
    global _hn_client
    _hn_client = client


def _get_hn_client():
    return _hn_client


def search_hn(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search Hacker News via Algolia API."""
    client = _get_hn_client()
    if client is not None:
        return client.search(query, source=SourceType.HN)

    results = []
    try:
        import httpx

        encoded = query.replace(" ", "%20")
        url = f"https://hn.algolia.com/api/v1/search?query={encoded}&hitsPerPage={max_results}"
        resp = httpx.get(url, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        for i, hit in enumerate(data.get("hits", [])):
            results.append(
                SearchResult(
                    title=hit.get("title", ""),
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                    snippet=hit.get("story_text", "") or hit.get("comment_text", "") or "",
                    source=SourceType.HN,
                    source_name="Hacker News",
                    published=hit.get("created_at", ""),
                    relevance_score=1.0 - (i * 0.1) if i < 10 else 0.0,
                )
            )
    except Exception as e:
        logger.warning("HN search failed: %s", e)
    return results


# ---------------------------------------------------------------------------
# Blog / general web search (reuses DuckDuckGo with blog filter heuristic)
# ---------------------------------------------------------------------------

_blog_client = None


def set_blog_client(client):
    global _blog_client
    _blog_client = client


def _get_blog_client():
    return _blog_client


def search_blogs(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search for blog posts and long-form articles.

    Uses DuckDuckGo with a blog-focused heuristic query.
    """
    client = _get_blog_client()
    if client is not None:
        return client.search(query, source=SourceType.BLOG)

    results = []
    try:
        from duckduckgo_search import DDGS

        blog_query = f'{query} (blog OR "insights" OR "deep dive")'
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(blog_query, max_results=max_results)):
                url = r.get("href", "")
                # Heuristic: prefer subdomains/paths that look like blogs
                results.append(
                    SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", ""),
                        source=SourceType.BLOG,
                        source_name="blog",
                        published=None,
                        relevance_score=1.0 - (i * 0.1) if i < 10 else 0.0,
                    )
                )
    except Exception as e:
        logger.warning("Blog search failed: %s", e)
    return results


# ---------------------------------------------------------------------------
# Orchestrator — run all searchers in parallel
# ---------------------------------------------------------------------------

def search_all(query: str, max_per_source: int = 5) -> dict[SourceType, list[SearchResult]]:
    """Run all searchers in parallel and return a dict keyed by source type."""
    searchers = {
        SourceType.WEB: search_web,
        SourceType.ARXIV: search_arxiv,
        SourceType.HN: search_hn,
        SourceType.BLOG: search_blogs,
    }

    results: dict[SourceType, list[SearchResult]] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(fn, query, max_per_source): st
            for st, fn in searchers.items()
        }
        for future in as_completed(future_map):
            st = future_map[future]
            try:
                results[st] = future.result()
            except Exception as e:
                logger.error("Search %s failed: %s", st.value, e)
                results[st] = []

    return results