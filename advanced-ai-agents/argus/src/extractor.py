"""Content extractor — crawl and extract full text from sources."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from src.models import ExtractedContent, SearchResult, SourceType

logger = logging.getLogger(__name__)

_extractor_client = None


def set_extractor_client(client):
    global _extractor_client
    _extractor_client = client


def _get_extractor_client():
    return _extractor_client


def extract_content(url: str, source_type: SourceType) -> ExtractedContent | None:
    """Extract full text content from a single URL.

    Uses BeautifulSoup to parse HTML and extract readable text.
    """
    client = _get_extractor_client()
    if client is not None:
        return client.extract(url, source_type)

    try:
        import httpx
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ARGUS/1.0; ResearchBot; +https://github.com/)"
        }
        resp = httpx.get(url, headers=headers, timeout=20.0, follow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script/style/nav elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        text = soup.get_text(separator="\n", strip=True)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Handle arXiv abstract pages differently — better text in <blockquote>
        if source_type == SourceType.ARXIV:
            abstract_block = soup.find("blockquote", class_="abstract")
            if abstract_block:
                text = abstract_block.get_text(strip=True)

        word_count = len(text.split())

        return ExtractedContent(
            url=url,
            title=title,
            content=text[:10000],  # Cap at ~10K chars
            source=source_type,
            word_count=word_count,
        )
    except Exception as e:
        logger.warning("Failed to extract %s: %s", url, e)
        return None


def extract_all(
    results: dict[SourceType, list[SearchResult]], max_per_type: int = 3
) -> list[ExtractedContent]:
    """Extract content from all search results in parallel."""
    urls_to_fetch: list[tuple[str, SourceType]] = []
    seen = set()
    for source_type, items in results.items():
        for item in items[:max_per_type]:
            if item.url not in seen:
                seen.add(item.url)
                urls_to_fetch.append((item.url, source_type))

    extracted: list[ExtractedContent] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {
            executor.submit(extract_content, url, st): url
            for url, st in urls_to_fetch
        }
        for future in as_completed(future_map):
            try:
                result = future.result()
                if result is not None:
                    extracted.append(result)
            except Exception as e:
                logger.error("Extraction failed: %s", e)

    return extracted