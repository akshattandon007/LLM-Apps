"""FAISS vector store with metadata support.

Stores embeddings + metadata so we can filter by intent or speaker before
semantic search.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from src.chunker import Chunk


class VectorStore:
    """FAISS-based vector store with flat (brute-force) index and metadata."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index: Optional[faiss.IndexFlatL2] = None
        self.chunks: list[Chunk] = []  # alignment: position in index == position in list
        self._initialized = False

    def _ensure_index(self):
        if not self._initialized:
            self.index = faiss.IndexFlatL2(self.dim)
            self._initialized = True

    def add_chunks(self, chunks: list[Chunk], embeddings: np.ndarray):
        """Add chunks with their pre-computed embeddings."""
        self._ensure_index()
        if self.index is None:
            raise RuntimeError("FAISS index not initialized")
        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        metadata_filter: Optional[dict] = None,
    ) -> list[tuple[Chunk, float]]:
        """Search the index.

        Args:
            query_embedding: (1, dim) array.
            top_k: Number of results to return.
            metadata_filter: If provided, only chunks matching all key-value pairs
                             are considered. Applied as a post-filter.

        Returns:
            List of (Chunk, L2 distance) tuples, sorted by distance (ascending).
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        results: list[tuple[Chunk, float]] = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            chunk = self.chunks[int(idx)]
            if metadata_filter:
                if not all(chunk.metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue
            results.append((chunk, float(dist)))

        return results

    def save(self, directory: str | Path):
        """Persist the index and chunks to disk."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        if self.index is not None:
            faiss.write_index(self.index, str(directory / "index.faiss"))

        # Save chunks as JSON lines
        chunks_data = []
        for chunk in self.chunks:
            chunks_data.append({
                "id": chunk.id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            })
        with open(directory / "chunks.jsonl", "w") as f:
            for cd in chunks_data:
                f.write(json.dumps(cd) + "\n")

        # Save state info
        with open(directory / "state.pkl", "wb") as f:
            pickle.dump({"dim": self.dim, "initialized": self._initialized}, f)

    @classmethod
    def load(cls, directory: str | Path) -> "VectorStore":
        """Load a persisted VectorStore."""
        directory = Path(directory)

        with open(directory / "state.pkl", "rb") as f:
            state = pickle.load(f)

        store = cls(dim=state.get("dim", 384))

        index_path = directory / "index.faiss"
        if index_path.exists():
            store.index = faiss.read_index(str(index_path))
            store._initialized = True

        chunks_path = directory / "chunks.jsonl"
        if chunks_path.exists():
            store.chunks = []
            with open(chunks_path) as f:
                for line in f:
                    cd = json.loads(line)
                    chunk = Chunk(
                        id=cd["id"],
                        text=cd["text"],
                        metadata=cd["metadata"],
                    )
                    store.chunks.append(chunk)

        return store

    @property
    def size(self) -> int:
        return self.index.ntotal if self.index is not None else 0