"""Data models for TripTome."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    """A chunk of text extracted from a travel document."""
    text: str
    source: str  # filename or URL
    page: Optional[int] = None
    chunk_id: int = 0


@dataclass
class SearchResult:
    """A single search result with relevance info."""
    text: str
    source: str
    page: Optional[int]
    score: float
    chunk_id: int


@dataclass
class Answer:
    """A generated answer with supporting citations."""
    query: str
    answer: str
    citations: list[SearchResult] = field(default_factory=list)
    source_names: list[str] = field(default_factory=list)