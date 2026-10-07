"""Data models for ManualMate."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    text: str
    source: str          # filename or doc title
    doc_id: str          # unique document identifier
    index: int           # position within the document
    char_start: int = 0  # character offset in original document
    char_end: int = 0


@dataclass
class SearchResult:
    """Result of a vector search."""
    chunk: Chunk
    score: float


@dataclass
class QueryResult:
    """Result of querying the RAG engine."""
    answer: str
    sources: List[str]       # source document filenames
    chunks: List[str]        # retrieved chunk texts
    scores: List[float]      # similarity scores


@dataclass
class IngestResult:
    """Result of ingesting a document."""
    filepath: str
    chunks: int
    characters: int
    elapsed_seconds: float