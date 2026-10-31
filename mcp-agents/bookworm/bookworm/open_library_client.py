"""Open Library API client — free, zero-auth book metadata."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

BASE_URL = "https://openlibrary.org"
COVERS_URL = "https://covers.openlibrary.org"

USER_AGENT = "BookWormMCP/1.0 (bookworm-mcp; mailto:akshattandon4@gmail.com)"


@dataclass
class RateLimiter:
    """Simple rate limiter — 1 req/sec for non-identified, 3/sec for identified."""

    max_per_second: float = 3.0
    _last_call: float = field(default=0.0)

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        min_interval = 1.0 / self.max_per_second
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_call = time.monotonic()


class OpenLibraryClient:
    """HTTP client for Open Library's free REST API (no auth needed)."""

    def __init__(self, user_agent: str = USER_AGENT) -> None:
        self.client = httpx.Client(headers={"User-Agent": user_agent}, timeout=15.0)
        self.rate_limiter = RateLimiter()

    def _get_json(self, url: str, params: dict | None = None) -> dict[str, Any]:
        self.rate_limiter.wait()
        resp = self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _get_list_json(self, url: str, params: dict | None = None) -> list[Any]:
        self.rate_limiter.wait()
        resp = self.client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        raise ValueError(f"Expected list response, got {type(data).__name__}")

    def search_books(
        self, query: str, limit: int = 10, page: int = 1
    ) -> dict[str, Any]:
        """Search books by title, author, or free-text query."""
        params = {"q": query, "limit": min(limit, 50), "page": page, "fields": "*"}
        return self._get_json(f"{BASE_URL}/search.json", params)

    def get_book_by_isbn(self, isbn: str) -> dict[str, Any]:
        """Get book details by ISBN (10 or 13)."""
        return self._get_json(f"{BASE_URL}/api/books", {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"})

    def get_book_by_olid(self, olid: str) -> dict[str, Any]:
        """Get edition details by Open Library ID (e.g. OL123M)."""
        return self._get_json(f"{BASE_URL}/books/{olid}.json")

    def get_work(self, work_id: str) -> dict[str, Any]:
        """Get work details by Open Library Work ID (e.g. OL123W)."""
        return self._get_json(f"{BASE_URL}/works/{work_id}.json")

    def get_author(self, author_id: str) -> dict[str, Any]:
        """Get author details by Open Library Author ID (e.g. OL123A)."""
        return self._get_json(f"{BASE_URL}/authors/{author_id}.json")

    def get_author_works(self, author_id: str, limit: int = 20) -> dict[str, Any]:
        """Get works by an author."""
        params = {"limit": min(limit, 50)}
        return self._get_json(f"{BASE_URL}/authors/{author_id}/works.json", params)

    def search_subject(self, subject: str, limit: int = 10, page: int = 1) -> dict[str, Any]:
        """Get books by subject/topic."""
        params = {"limit": min(limit, 50), "offset": (page - 1) * limit}
        return self._get_json(f"{BASE_URL}/subjects/{subject.lower().replace(' ', '_')}.json", params)

    def get_book_cover_url(self, olid: str, size: str = "M") -> str:
        """Get cover image URL for a book edition.

        Size: S (small), M (medium), L (large).
        """
        return f"{COVERS_URL}/b/olid/{olid}-{size}.jpg"

    def get_author_photo_url(self, author_id: str, size: str = "M") -> str:
        """Get author photo URL."""
        return f"{COVERS_URL}/a/olid/{author_id}-{size}.jpg"

    def search_authors(self, query: str, limit: int = 10) -> dict[str, Any]:
        """Search authors by name."""
        params = {"q": query, "limit": min(limit, 50)}
        return self._get_json(f"{BASE_URL}/search/authors.json", params)

    def get_trending(self, limit: int = 10) -> dict[str, Any]:
        """Get trending/recently popular books via recently changed works."""
        params = {"limit": min(limit, 50), "sort": "latest_revision"}
        return self._get_json(f"{BASE_URL}/search.json?q=*&sort=latest_revision&limit={min(limit, 50)}")

    def close(self) -> None:
        self.client.close()