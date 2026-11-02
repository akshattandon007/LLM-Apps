"""Local embedding index for paper chunks."""

from __future__ import annotations

import json
import os
import pickle
import re
from pathlib import Path
from typing import Any

import numpy as np

from .models import ArxivPaper, Chunk, SearchHit

# Where the index state lives
INDEX_DIR = Path(os.path.expanduser("~")) / ".paperpilot"


def _ensure_index_dir() -> Path:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return INDEX_DIR


class PaperIndex:
    """A local embedding index over paper chunks.

    Uses sentence-transformers for embeddings and numpy for similarity search.
    Persisted to ~/.paperpilot/ between sessions.
    """

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.embeddings: np.ndarray | None = None  # shape (N, D)
        self._encoder: Any = None  # lazy loaded
        self._loaded = False

    # ── persistence ──────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist index to disk."""
        index_dir = _ensure_index_dir()
        data = {
            "chunks": [
                {
                    "text": c.text,
                    "paper_id": c.paper_id,
                    "title": c.title,
                    "chunk_index": c.chunk_index,
                }
                for c in self.chunks
            ],
        }
        with open(index_dir / "index.json", "w") as f:
            json.dump(data, f, indent=2)

        if self.embeddings is not None:
            np.save(index_dir / "embeddings.npy", self.embeddings)

    def load(self) -> bool:
        """Load index from disk. Returns True if loaded successfully."""
        index_dir = _ensure_index_dir()
        json_path = index_dir / "index.json"
        npy_path = index_dir / "embeddings.npy"

        if not json_path.exists():
            return False

        with open(json_path) as f:
            data = json.load(f)

        self.chunks = [
            Chunk(**c) for c in data["chunks"]
        ]

        if npy_path.exists():
            self.embeddings = np.load(npy_path)

        self._loaded = True
        return True

    # ── index building ───────────────────────────────────────────────────

    def add_papers(self, papers: list[ArxivPaper]) -> int:
        """Add papers to the index. Returns number of chunks created."""
        new_chunks: list[Chunk] = []
        for paper in papers:
            chunks = self._chunk_paper(paper)
            new_chunks.extend(chunks)

        if not new_chunks:
            return 0

        self.chunks.extend(new_chunks)

        # Encode new chunks
        texts = [c.text for c in new_chunks]
        encoder = self._get_encoder()
        new_embeddings = encoder.encode(texts, show_progress_bar=False)  # type: ignore

        if self.embeddings is None:
            self.embeddings = np.array(new_embeddings)
        else:
            self.embeddings = np.vstack([self.embeddings, np.array(new_embeddings)])

        return len(new_chunks)

    def list_papers(self) -> list[dict]:
        """List unique papers in the index."""
        seen: dict[str, str] = {}
        for c in self.chunks:
            if c.paper_id not in seen:
                seen[c.paper_id] = c.title
        return [
            {"id": pid, "title": title}
            for pid, title in seen.items()
        ]

    @property
    def paper_count(self) -> int:
        return len(self.list_papers())

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    # ── search ───────────────────────────────────────────────────────────

    def search(self, query: str, k: int = 5) -> list[SearchHit]:
        """Search index for chunks relevant to query.

        Returns top-k SearchHit objects.
        """
        if not self.chunks or self.embeddings is None:
            return []

        encoder = self._get_encoder()
        query_emb = encoder.encode([query], show_progress_bar=False)  # type: ignore
        query_emb = np.array(query_emb)

        # Cosine similarity
        scores = np.dot(self.embeddings, query_emb.T).flatten()
        top_k = min(k, len(scores))
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results: list[SearchHit] = []
        for idx in top_indices:
            results.append(SearchHit(
                chunk=self.chunks[idx],
                score=float(scores[idx]),
            ))

        return results

    # ── internals ────────────────────────────────────────────────────────

    def _chunk_paper(self, paper: ArxivPaper) -> list[Chunk]:
        """Split a paper's abstract into chunks."""
        chunks: list[Chunk] = []

        # Use abstract as the primary text
        text = paper.abstract.strip()
        if not text:
            return chunks

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        # Group into chunks of 3-4 sentences
        chunk_size = 3
        for i in range(0, len(sentences), chunk_size):
            group = sentences[i:i + chunk_size]
            chunk_text = " ".join(group)
            if len(chunk_text) > 30:
                chunks.append(Chunk(
                    text=chunk_text,
                    paper_id=paper.arxiv_id,
                    title=paper.title,
                    chunk_index=len(chunks),
                ))

        # If abstract is very short, use it as one chunk
        if not chunks and paper.abstract.strip():
            chunks.append(Chunk(
                text=paper.abstract.strip(),
                paper_id=paper.arxiv_id,
                title=paper.title,
                chunk_index=0,
            ))

        return chunks

    def _get_encoder(self) -> Any:
        """Lazy-load the sentence transformer model."""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
        return self._encoder