"""Data models for parsed email chunks."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailMetadata:
    """Metadata extracted from a single email."""

    message_id: str
    subject: str
    sender: str
    date: str
    to_: str
    cc: str = ""
    labels: list[str] = field(default_factory=list)


@dataclass
class EmailChunk:
    """A chunk of email body text + its metadata."""

    metadata: EmailMetadata
    chunk_index: int
    text: str
    chunk_id: str  # unique ID for ChromaDB


@dataclass
class SearchResult:
    """A single search hit with relevance info."""

    chunk_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    score: float