"""arXiv source — abstracts make the 'deep dive' segment.

Keyless, Atom XML over https. Parsed with the stdlib so there is no feedparser
dependency.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..models import ContentItem
from .base import BaseSource, SourceError

API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"


def parse_arxiv(xml_text: str, category: str = "deep") -> list[ContentItem]:
    """Parse an arXiv Atom feed into content items."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise SourceError(f"arxiv: invalid XML ({exc})") from exc

    items: list[ContentItem] = []
    for entry in root.findall(f"{ATOM}entry"):
        title = " ".join((entry.findtext(f"{ATOM}title") or "").split())
        summary = " ".join((entry.findtext(f"{ATOM}summary") or "").split())
        link = (entry.findtext(f"{ATOM}id") or "").strip()
        published = (entry.findtext(f"{ATOM}published") or "").strip()[:10] or None
        words = len(summary.split())
        if not title or not link or words < 30:
            continue
        items.append(
            ContentItem(
                title=title,
                source="arxiv",
                url=link.replace("http://", "https://"),
                words=words,
                summary=summary[:280],
                category=category,
                published=published,
            )
        )
    return items


class ArxivSource(BaseSource):
    name = "arxiv"
    category = "deep"

    def fetch(self, topic: str, limit: int = 5) -> list[ContentItem]:
        params = {
            "search_query": f"all:{topic}" if topic else "all:artificial intelligence",
            "start": "0",
            "max_results": str(max(1, min(20, limit))),
            "sortBy": "relevance",
        }
        resp = self._get(API, params=params)
        items = parse_arxiv(resp.text)
        return items[:limit]
