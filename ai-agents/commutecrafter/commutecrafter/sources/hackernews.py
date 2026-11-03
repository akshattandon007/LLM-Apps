"""Hacker News source — Ask HN threads are real long-form prose with a known
word count, which makes them honest 'core' reading material.

Keyless via the Algolia HN Search API.
"""

from __future__ import annotations

import html
import re
from typing import Any

from ..models import ContentItem
from .base import BaseSource, SourceError

API = "https://hn.algolia.com/api/v1/search"
TAG_RE = re.compile(r"<[^>]+>")


def clean_html(text: str) -> str:
    """Strip tags and unescape entities from Algolia's HTML snippets."""
    if not text:
        return ""
    text = re.sub(r"<p>", " ", text, flags=re.IGNORECASE)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return " ".join(text.split())


def parse_hackernews(payload: dict[str, Any], min_words: int = 120) -> list[ContentItem]:
    """Turn an Algolia search payload into content items (text posts only)."""
    hits = (payload or {}).get("hits")
    if not isinstance(hits, list):
        raise SourceError("hackernews: unexpected payload shape")

    items: list[ContentItem] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        title = clean_html(hit.get("title") or "")
        body = clean_html(hit.get("story_text") or hit.get("comment_text") or "")
        words = len(body.split())
        object_id = str(hit.get("objectID") or "").strip()
        if not title or not object_id or words < min_words:
            continue
        items.append(
            ContentItem(
                title=title,
                source="hackernews",
                url=f"https://news.ycombinator.com/item?id={object_id}",
                words=words,
                summary=body[:280],
                category="news",
                published=(hit.get("created_at") or "")[:10] or None,
            )
        )
    return items


class HackerNewsSource(BaseSource):
    name = "hackernews"
    category = "news"

    def fetch(self, topic: str, limit: int = 5) -> list[ContentItem]:
        # Ask HN threads carry story_text; plain link posts do not, and a link
        # post's reading time is unknowable without fetching a third-party page.
        params = {
            "query": topic or "ask hn",
            "tags": "ask_hn",
            "hitsPerPage": str(max(5, min(30, limit * 5))),
        }
        resp = self._get(API, params=params)
        try:
            payload = resp.json()
        except ValueError as exc:
            raise SourceError(f"hackernews: bad JSON ({exc})") from exc
        return parse_hackernews(payload)[:limit]
