"""ClipRef — data models and type definitions."""

from __future__ import annotations

import dataclasses
import datetime


@dataclasses.dataclass(frozen=True)
class ChunkMetadata:
    """Metadata for a single text chunk stored in the vector index."""

    chunk_id: str
    """Unique SHA-256 hash identifying this chunk."""

    text: str
    """The chunk text content."""

    source_file: str
    """Filename of the source document."""

    source_path: str
    """Relative or absolute path to the source document."""

    file_hash: str
    """SHA-256 of the source file content at index time."""

    chunk_index: int
    """Zero-based index of this chunk within the source file."""

    indexed_at: str
    """ISO-8601 timestamp when this chunk was indexed."""


@dataclasses.dataclass(frozen=True)
class SearchResult:
    """A single search result from the vector index."""

    chunk_id: str
    """Unique chunk identifier."""

    text: str
    """The chunk text content."""

    source_file: str
    """Filename of the source document."""

    source_path: str
    """Path to the source document."""

    score: float
    """Cosine similarity score (0-1, higher = more relevant)."""

    def __str__(self) -> str:
        return (
            f"[{self.score:.3f}] {self.source_path}\n"
            f"  {self.text[:200]}" + ("..." if len(self.text) > 200 else "")
        )


@dataclasses.dataclass(frozen=True)
class Answer:
    """An LLM-generated answer with source citations."""

    text: str
    """The generated answer text."""

    sources: list[SearchResult]
    """Source documents that grounded the answer."""

    model: str
    """The LLM model used to generate the answer."""

    def __str__(self) -> str:
        lines = [self.text, "", "--- Sources ---"]
        for i, src in enumerate(self.sources, 1):
            lines.append(f"{i}. {src.source_path} (score: {src.score:.3f})")
        return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class IndexStats:
    """Index statistics."""

    chunk_count: int
    """Total chunks in the index."""

    source_files: int
    """Number of unique source files."""

    database_size_bytes: int
    """Total size of the database directory on disk."""

    @property
    def database_size_kb(self) -> float:
        return self.database_size_bytes / 1024.0


_DEFAULT_CHUNK_SIZE = 512
_DEFAULT_CHUNK_OVERLAP = 64
_DEFAULT_TOP_K = 5
_DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_LLM_MODEL = "google/gemini-2.0-flash-exp:free"
_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_COLLECTION_NAME = "clipref"