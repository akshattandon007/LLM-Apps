"""WikiPilot — Wikipedia REST API client.

Wraps the Wikipedia /api/rest_v1/ endpoints and the legacy action=query API.
All requests are free, zero-auth, and rate-limited by common sense (one
request at a time, no aggressive batching).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

USER_AGENT = "WikiPilotMCP/1.0 (MCP server; +https://github.com/akshattandon007/LLM-Apps)"
API_BASE = "https://en.wikipedia.org/api/rest_v1"
WIKI_BASE = "https://en.wikipedia.org/w/api.php"


class WikipediaError(Exception):
    """Base exception for Wikipedia API failures."""


class ArticleNotFound(WikipediaError):
    """The requested article does not exist."""


def _fetch(url: str, *, max_bytes: int = 512_000, timeout: int = 15) -> dict[str, Any]:
    """Fetch a URL and return the parsed JSON body.

    Raises ArticleNotFound on 404, WikipediaError on other failures.
    """
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read(max_bytes)
            return json.loads(raw)
    except HTTPError as exc:
        if exc.code == 404:
            raise ArticleNotFound(f"Not found: {url}") from exc
        raise WikipediaError(f"HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise WikipediaError(f"Network error: {exc.reason}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise WikipediaError(f"Parse error: {exc}") from exc


def _fetch_legacy(params: dict[str, str], *, max_bytes: int = 512_000) -> dict[str, Any]:
    """Fetch from the legacy action=query API (for search / categories / extracts)."""
    params["format"] = "json"
    qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    url = f"{WIKI_BASE}?{qs}"
    return _fetch(url, max_bytes=max_bytes)


def _resolve_title(title: str) -> str | None:
    """Resolve a title to its canonical form. Returns None if not found."""
    params = {
        "action": "query",
        "titles": title.replace(" ", "_"),
        "prop": "info",
        "inprop": "",
    }
    data = _fetch_legacy(params)
    pages = data.get("query", {}).get("pages", {})
    for pid, pg in pages.items():
        if pid != "-1" and "title" in pg:
            return pg["title"]
    return None


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def search_articles(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Search Wikipedia articles by keyword.

    Args:
        query: Free-text search string.
        limit: Max results (1-50).

    Returns:
        List of {title, page_id, snippet, url}.
    """
    data = _fetch_legacy({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": str(min(max(limit, 1), 50)),
        "srprop": "snippet",
    })
    results: list[dict[str, Any]] = []
    for hit in data.get("query", {}).get("search", []):
        results.append({
            "title": hit.get("title", ""),
            "page_id": hit.get("pageid", 0),
            "snippet": _strip_html(hit.get("snippet", "")),
            "url": f"https://en.wikipedia.org/wiki/{quote(hit.get('title', '').replace(' ', '_'))}",
        })
    return results


def get_summary(title: str) -> dict[str, Any]:
    """Get an article summary (intro paragraph, thumbnail, basic metadata).

    Args:
        title: Wikipedia article title (case-sensitive).

    Returns:
        Dict with keys: title, extract, thumbnail_url, url, page_id.
    """
    page = quote(title.replace(" ", "_"))
    data = _fetch(f"{API_BASE}/page/summary/{page}")
    return {
        "title": data.get("title", title),
        "extract": data.get("extract", ""),
        "thumbnail_url": (data.get("thumbnail") or {}).get("source"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "page_id": data.get("pageid", 0),
    }


def get_article(title: str) -> dict[str, Any]:
    """Get the full plain-text content of an article.

    Uses the legacy action=query with prop=extracts&explaintext to get
    clean plain text (no HTML markup).

    Args:
        title: Wikipedia article title.

    Returns:
        Dict with keys: title, content, url, page_id.
    """
    page = title.replace(" ", "_")
    # First get metadata via summary
    try:
        summary = get_summary(title)
    except ArticleNotFound:
        raise
    except WikipediaError:
        summary = {"title": title, "url": "", "page_id": 0}

    # Get full extract in plain text
    data = _fetch_legacy({
        "action": "query",
        "titles": page,
        "prop": "extracts",
        "explaintext": "1",
        "exlimit": "1",
        "exintro": "0",
    }, max_bytes=1_000_000)

    pages_data = data.get("query", {}).get("pages", {})
    content = ""
    for pid, pg in pages_data.items():
        if pid != "-1":
            content = pg.get("extract", "") or ""
            break

    return {
        "title": summary.get("title", title),
        "content": content,
        "url": summary.get("url", f"https://en.wikipedia.org/wiki/{quote(page)}"),
        "page_id": summary.get("page_id", 0),
    }


def get_random_article() -> dict[str, Any]:
    """Fetch a random Wikipedia article summary.

    Returns:
        Same shape as get_summary().
    """
    data = _fetch(f"{API_BASE}/page/random/summary")
    return {
        "title": data.get("title", ""),
        "extract": data.get("extract", ""),
        "thumbnail_url": (data.get("thumbnail") or {}).get("source"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        "page_id": data.get("pageid", 0),
    }


def on_this_day(*, month: int | None = None, day: int | None = None) -> list[dict[str, Any]]:
    """Get historical events that happened on a given date.

    Defaults to the current date in UTC if month/day are omitted.

    Returns:
        List of {year, description, url} events.
    """
    now = datetime.now(timezone.utc)
    m = month if month is not None else now.month
    d = day if day is not None else now.day
    # onthisday feed events are large; use a generous limit
    data = _fetch(f"{API_BASE}/feed/onthisday/events/{m}/{d}", max_bytes=2_000_000)
    events: list[dict[str, Any]] = []
    for ev in data.get("events", []):
        events.append({
            "year": ev.get("year", 0),
            "description": _strip_html(ev.get("text", "")),
            "url": (ev.get("content_urls") or {}).get("desktop", {}).get("page", ""),
        })
    return events


def get_related_articles(title: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Get related/similar article titles using the links API.

    Uses action=query with generator=links to find pages that link to the
    same topics as the given article.

    Args:
        title: Wikipedia article title.
        limit: Max related pages.

    Returns:
        List of {title, url} dicts.
    """
    page = title.replace(" ", "_")
    # Use prop=linkshere to find pages that link to this article
    data = _fetch_legacy({
        "action": "query",
        "titles": page,
        "generator": "links",
        "gpllimit": str(min(max(limit, 1), 50)),
        "prop": "info",
        "inprop": "url",
    })

    pages = data.get("query", {}).get("pages", {})
    results: list[dict[str, Any]] = []
    for pid, pg in pages.items():
        if pid == "-1" or pid == str(pg.get("pageid", pid)):
            # Skip the source page itself
            if pg.get("title", "").lower() == title.lower():
                continue
            results.append({
                "title": pg.get("title", ""),
                "url": pg.get("fullurl", f"https://en.wikipedia.org/wiki/{quote(pg.get('title', '').replace(' ', '_'))}"),
            })

    return results[:limit]


def get_article_categories(title: str) -> list[str]:
    """Get the category list for an article.

    Args:
        title: Wikipedia article title.

    Returns:
        Sorted list of category names (without the 'Category:' prefix).
    """
    page = title.replace(" ", "_")
    data = _fetch_legacy({
        "action": "query",
        "titles": page,
        "prop": "categories",
        "cllimit": "max",
    })
    pages = data.get("query", {}).get("pages", {})

    # Check if article exists
    for pid, pg in pages.items():
        if pid == "-1":
            raise ArticleNotFound(f"Article not found: {title}")

    categories: list[str] = []
    for pid, page_data in pages.items():
        for cat in page_data.get("categories", []):
            cat_title = cat.get("title", "")
            if cat_title.startswith("Category:"):
                categories.append(cat_title[len("Category:"):])
            else:
                categories.append(cat_title)
    return sorted(categories)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    return text.strip()