"""Data models for PaperPilot."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ArxivPaper:
    """A paper from arXiv."""
    arxiv_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    categories: list[str] = field(default_factory=list)
    published: str = ""
    updated: str = ""
    pdf_url: str = ""
    abs_url: str = ""

    @property
    def short_id(self) -> str:
        return self.arxiv_id.replace("arxiv:", "").replace("arXiv:", "")


@dataclass
class Chunk:
    """A text chunk from a paper."""
    text: str
    paper_id: str
    title: str
    chunk_index: int = 0


@dataclass
class SearchHit:
    """A search result hit."""
    chunk: Chunk
    score: float