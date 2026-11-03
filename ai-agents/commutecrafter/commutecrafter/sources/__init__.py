"""Source registry."""

from __future__ import annotations

from .arxiv import ArxivSource
from .base import BaseSource, SourceError, dedupe
from .gutenberg import GutenbergSource
from .hackernews import HackerNewsSource
from .wikipedia import WikipediaSource

SOURCE_CLASSES: dict[str, type[BaseSource]] = {
    "wikipedia": WikipediaSource,
    "arxiv": ArxivSource,
    "hackernews": HackerNewsSource,
    "gutenberg": GutenbergSource,
}

SOURCE_NAMES = tuple(SOURCE_CLASSES)


def build_sources(names: list[str] | None = None, timeout: int = 15) -> list[BaseSource]:
    """Instantiate the requested sources (all of them by default)."""
    chosen = names or list(SOURCE_NAMES)
    unknown = [n for n in chosen if n not in SOURCE_CLASSES]
    if unknown:
        raise ValueError(f"unknown source(s): {', '.join(unknown)}")
    return [SOURCE_CLASSES[n](timeout=timeout) for n in chosen]


__all__ = [
    "BaseSource",
    "SourceError",
    "SOURCE_CLASSES",
    "SOURCE_NAMES",
    "build_sources",
    "dedupe",
]
