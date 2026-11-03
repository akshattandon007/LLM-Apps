"""Project Gutenberg source — public-domain long reads for the wind-down.

Gutendex is flaky from some networks, so this source talks to
``gutenberg.org`` directly: a small curated catalogue (``data/classics.json``)
supplies stable ebook IDs, and the first N words of each text are streamed so
we never download a 1.2 MB file to count 4,000 words.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import ContentItem
from .base import BaseSource, SourceError

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "classics.json"
TEXT_URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"

_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE | re.DOTALL)
_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE | re.DOTALL)


def load_catalog(path: Path | None = None) -> list[dict]:
    """Load the curated public-domain catalogue."""
    target = path or CATALOG_PATH
    with open(target, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise SourceError("gutenberg: catalogue must be a list")
    return data


def strip_boilerplate(text: str) -> str:
    """Remove the Project Gutenberg licence header and footer."""
    start = _START.search(text)
    if start:
        text = text[start.end():]
    end = _END.search(text)
    if end:
        text = text[: end.start()]
    return text


def parse_gutenberg_text(text: str, limit_words: int = 5000) -> tuple[int, str]:
    """Return ``(consumable_word_count, excerpt)`` for the first chunk of a book.

    ``consumable_word_count`` is capped at ``limit_words`` because the plan
    particle is "a 15 minute slice of Meditations", not "all of Meditations".
    """
    body = strip_boilerplate(text)
    words = body.split()
    if not words:
        return 0, ""
    take = words[: max(1, limit_words)]
    return len(take), " ".join(take[:60])


def rank_catalog(catalog: list[dict], topic: str) -> list[dict]:
    """Order catalogue entries by keyword overlap with ``topic``.

    Ties keep catalogue order, so behaviour is deterministic.
    """
    terms = {t for t in re.split(r"[^a-z0-9]+", (topic or "").lower()) if len(t) > 2}

    def score(entry: dict) -> int:
        tags = {str(t).lower() for t in entry.get("tags", [])}
        title_words = {w for w in re.split(r"[^a-z0-9]+", entry.get("title", "").lower()) if len(w) > 2}
        return 2 * len(terms & tags) + len(terms & title_words)

    ranked = sorted(catalog, key=lambda e: -score(e))
    return ranked


class GutenbergSource(BaseSource):
    name = "gutenberg"
    category = "reflective"

    def __init__(self, *args, words_limit: int = 6000, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.words_limit = words_limit

    def _stream_prefix(self, book_id: int, max_bytes: int = 250_000) -> str:
        url = TEXT_URL.format(id=book_id)
        chunks: list[bytes] = []
        size = 0
        with self.session.get(url, timeout=self.timeout, stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=16384):
                if not chunk:
                    continue
                chunks.append(chunk)
                size += len(chunk)
                if size >= max_bytes:
                    break
        return b"".join(chunks).decode("utf-8", errors="ignore")

    def fetch(self, topic: str, limit: int = 2, book_ids: list[int] | None = None) -> list[ContentItem]:
        catalog = load_catalog()
        if book_ids:
            catalog = [e for e in catalog if int(e["id"]) in set(book_ids)] or catalog

        items: list[ContentItem] = []
        for entry in rank_catalog(catalog, topic):
            if len(items) >= limit:
                break
            try:
                raw = self._stream_prefix(int(entry["id"]))
            except Exception:  # noqa: BLE001 - one bad book must not kill the plan
                continue
            words, excerpt = parse_gutenberg_text(raw, self.words_limit)
            if words < 200:
                continue
            items.append(
                ContentItem(
                    title=f"{entry['title']} — {entry.get('author', 'Unknown')}",
                    source="gutenberg",
                    url=f"https://www.gutenberg.org/ebooks/{entry['id']}",
                    words=words,
                    summary=excerpt,
                    category="reflective",
                )
            )
        return items
