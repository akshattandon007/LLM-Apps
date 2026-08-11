"""FAISS vector store for code chunk search."""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from src.models import Chunk, SourceReference


class VectorStore:
    """FAISS-based vector store for code chunk embeddings."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._index = None
        self.chunks: list[Chunk] = []
        self.texts: list[str] = []

    def _ensure_index(self):
        if self._index is not None:
            return
        import faiss

        self._index = faiss.IndexFlatIP(self.dimension)

    def add(self, chunks: list[Chunk], texts: list[str], embeddings: NDArray[np.float32]):
        """Add chunks and their embeddings to the store."""
        self._ensure_index()
        self.chunks.extend(chunks)
        self.texts.extend(texts)
        self._index.add(embeddings.astype(np.float32))

    def search(
        self,
        query_embedding: NDArray[np.float32],
        top_k: int = 5,
    ) -> list[SourceReference]:
        """Search for the top-k most relevant chunks."""
        self._ensure_index()
        if self._index.ntotal == 0:
            return []

        actual_k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(
            query_embedding.reshape(1, -1).astype(np.float32), actual_k
        )

        results: list[SourceReference] = []
        for i, idx in enumerate(indices[0]):
            chunk = self.chunks[idx]
            results.append(
                SourceReference(
                    file_path=chunk.file_path,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    snippet=chunk.content[:2000],
                    relevance_score=float(scores[0][i]),
                )
            )
        return results

    @property
    def size(self) -> int:
        """Number of indexed chunks."""
        if self._index is None:
            return 0
        return self._index.ntotal

    def save(self, directory: str):
        """Persist the index and metadata to disk."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        if self._index is not None:
            import faiss

            faiss.write_index(self._index, str(path / "index.faiss"))

        # Save chunks and texts
        with open(path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        with open(path / "texts.pkl", "wb") as f:
            pickle.dump(self.texts, f)

        meta = {
            "dimension": self.dimension,
            "num_chunks": len(self.chunks),
        }
        with open(path / "meta.json", "w") as f:
            json.dump(meta, f)

    def load(self, directory: str) -> bool:
        """Load a previously saved index. Returns True if successful."""
        path = Path(directory)
        if not (path / "index.faiss").exists():
            return False

        import faiss

        self._index = faiss.read_index(str(path / "index.faiss"))
        self.dimension = self._index.d

        # Load metadata
        with open(path / "chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)
        with open(path / "texts.pkl", "rb") as f:
            self.texts = pickle.load(f)

        return True

    def clear(self):
        """Clear the index."""
        self._index = None
        self.chunks = []
        self.texts = []
