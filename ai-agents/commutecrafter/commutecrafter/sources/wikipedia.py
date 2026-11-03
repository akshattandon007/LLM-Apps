"""Wikipedia source.

Two-stage on purpose: search returns candidate titles *and* a short intro for
display, then one cheap per-title call fetches the full plaintext so the word
count — and therefore the reading time — is real rather than guessed from a
byte length.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..models import ContentItem
from .base import BaseSource, SourceError

API = "https://en.wikipedia.org/w/api.php"


def parse_wikipedia(payload: dict[str, Any], category: str = "culture") -> list[ContentItem]:
    """Turn a MediaWiki ``query.pages`` payload into content items."""
    pages = (((payload or {}).get("query") or {}).get("pages") or {})
    if not isinstance(pages, dict):
        raise SourceError("wikipedia: unexpected payload shape")

    items: list[ContentItem] = []
    for page in pages.values():
        if not isinstance(page, dict):
            continue
        title = (page.get("title") or "").strip()
        extract = " ".join((page.get("extract") or "").split())
        words = len(extract.split())
        if not title or words < 40:
            continue
        items.append(
            ContentItem(
                title=title,
                source="wikipedia",
                url="https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
                words=words,
                summary=extract[:280],
                category=category,
            )
        )
    return items


def parse_full_extract(payload: dict[str, Any]) -> tuple[int, str]:
    """Return ``(word_count, excerpt)`` for a single-page full extract."""
    pages = (((payload or {}).get("query") or {}).get("pages") or {})
    for page in pages.values():
        if isinstance(page, dict):
            text = " ".join((page.get("extract") or "").split())
            return len(text.split()), text[:280]
    return 0, ""


class WikipediaSource(BaseSource):
    name = "wikipedia"
    category = "culture"

    def __init__(self, *args, full_text: bool = True, workers: int = 4, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.full_text = full_text
        self.workers = workers

    def _search(self, topic: str, limit: int, sentences: int) -> list[ContentItem]:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": topic or "main page",
            "gsrlimit": str(max(1, min(20, limit))),
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "exsentences": str(max(1, sentences)),
            "redirects": "1",
        }
        resp = self._get(API, params=params)
        try:
            payload = resp.json()
        except ValueError as exc:
            raise SourceError(f"wikipedia: bad JSON ({exc})") from exc
        return parse_wikipedia(payload)

    def _full(self, title: str) -> tuple[int, str]:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "explaintext": "1",
            "exlimit": "1",
            "titles": title,
            "redirects": "1",
        }
        try:
            resp = self._get(API, params=params)
            return parse_full_extract(resp.json())
        except Exception:  # noqa: BLE001 - intro length is an acceptable fallback
            return 0, ""

    def fetch(self, topic: str, limit: int = 6, sentences: int = 4) -> list[ContentItem]:
        items = self._search(topic, limit, sentences)[:limit]
        if not self.full_text or not items:
            return items

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            results = list(pool.map(self._full, [i.title for i in items]))

        for item, (words, excerpt) in zip(items, results):
            if words > item.words:
                item.words = words
                if excerpt:
                    item.summary = excerpt
        return items
