"""Pydantic models for Code Compass API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A code chunk extracted from a source file."""

    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str  # "function", "class", "module"
    name: str
    content: str
    docstring: str = ""


class IngestRequest(BaseModel):
    """Request to ingest a codebase directory."""

    directory_path: str
    extensions: list[str] = Field(
        default_factory=lambda: [".py", ".js", ".ts", ".jsx", ".tsx"]
    )
    chunk_size: int = 500
    chunk_overlap: int = 50


class IngestResponse(BaseModel):
    """Response after ingesting a codebase."""

    files_ingested: int
    chunks_created: int
    index_size: int
    message: str


class QueryRequest(BaseModel):
    """Search query against the ingested codebase."""

    query: str
    top_k: int = 5


class SourceReference(BaseModel):
    """A source code reference in the answer."""

    file_path: str
    start_line: int
    end_line: int
    snippet: str
    relevance_score: float = 0.0


class QueryResponse(BaseModel):
    """Answer with source references."""

    answer: str
    sources: list[SourceReference]


class StatusResponse(BaseModel):
    """Server status."""

    status: str
    indexed_files: int
    indexed_chunks: int
    has_index: bool
