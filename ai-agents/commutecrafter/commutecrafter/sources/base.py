"""Content sources.

Each module exposes a pure ``parse_*`` function (unit-testable, no network)
plus a thin ``fetch`` wrapper that hits a keyless public API.
"""

from __future__ import annotations

import time
from typing import Iterable

import requests

from ..models import ContentItem

USER_AGENT = "CommuteCrafter/1.0 (+https://github.com/akshattandon007/LLM-Apps)"
DEFAULT_TIMEOUT = 15


class SourceError(RuntimeError):
    """Raised when a source cannot be reached or returns garbage."""


class BaseSource:
    """Shared HTTP plumbing for keyless sources."""

    name: str = "base"
    category: str = "general"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, retries: int = 2) -> None:
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    # -- HTTP ---------------------------------------------------------------
    def _get(self, url: str, params: dict | None = None) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise SourceError(f"{self.name}: HTTP {resp.status_code}")
                resp.raise_for_status()
                return resp
            except Exception as exc:  # noqa: BLE001 - retried then surfaced
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.6 * (attempt + 1))
        raise SourceError(f"{self.name}: {last_error}")

    # -- API ----------------------------------------------------------------
    def fetch(self, topic: str, limit: int = 6) -> list[ContentItem]:  # pragma: no cover
        raise NotImplementedError


def dedupe(items: Iterable[ContentItem]) -> list[ContentItem]:
    """Drop duplicate URLs and duplicate titles, keeping first occurrence."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    out: list[ContentItem] = []
    for item in items:
        url = item.url.strip().lower()
        title = item.title.strip().lower()
        if not url or not title or url in seen_urls or title in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title)
        out.append(item)
    return out
