"""
Vector Store — FAISS-based vector index for storing and searching embeddings.

Stores:
  - FAISS index (flat L2 + inner product via IndexIDMap)
  - Metadata JSON (maps faiss_id → document dict)
"""

import json
import os
import numpy as np
import faiss
from typing import Any


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _index_path():
    return os.path.join(DATA_DIR, "faiss_index.bin")


def _metadata_path():
    return os.path.join(DATA_DIR, "metadata.json")


class VectorStore:
    """FAISS-based vector store with metadata."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index: faiss.Index | None = None
        self.metadata: dict[int, dict[str, Any]] = {}
        self._next_id = 0

    def _ensure_data_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def add(self, embeddings: np.ndarray, documents: list[dict[str, Any]]):
        """Add embeddings and their metadata to the store."""
        if self.index is None:
            # Use IndexFlatIP (inner product = cosine similarity on normalized vectors)
            self.index = faiss.IndexFlatIP(self.dim)
            self.index = faiss.IndexIDMap(self.index)

        n = embeddings.shape[0]
        ids = np.arange(self._next_id, self._next_id + n, dtype=np.int64)
        self.index.add_with_ids(embeddings, ids)

        for i, doc in enumerate(documents):
            self.metadata[int(ids[i])] = doc

        self._next_id += n

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[float, dict[str, Any]]]:
        """Search for top-k similar documents. Returns [(score, metadata), ...]."""
        if self.index is None or self.index.ntotal == 0:
            return []

        # query_embedding is (384,) — reshape to (1, 384)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        scores, ids = self.index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            meta = self.metadata.get(int(idx), {})
            results.append((float(score), meta))

        return results

    def save(self):
        """Save index and metadata to disk."""
        self._ensure_data_dir()
        if self.index is not None:
            faiss.write_index(self.index, _index_path())
        with open(_metadata_path(), "w") as f:
            json.dump(self.metadata, f, indent=2)

    def load(self) -> bool:
        """Load index and metadata from disk. Returns True if loaded."""
        if os.path.exists(_index_path()) and os.path.exists(_metadata_path()):
            self.index = faiss.read_index(_index_path())
            with open(_metadata_path()) as f:
                self.metadata = {int(k): v for k, v in json.load(f).items()}
            if self.index is not None:
                self._next_id = self.index.ntotal
            return True
        return False

    @property
    def size(self) -> int:
        if self.index is not None:
            return self.index.ntotal
        return 0
