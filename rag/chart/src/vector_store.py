"""FAISS vector store — build, save, load, search."""
from __future__ import annotations

import os
import pickle
from typing import Any

import faiss
import numpy as np

from src.models import Chunk

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class VectorStore:
    """Persistent FAISS index with chunk metadata."""

    def __init__(self, index_path: str = ""):
        self.index: faiss.Index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.chunks: list[Chunk] = []
        self.index_path = index_path or "/tmp/chart-faiss.index"

    def add(self, embeddings: np.ndarray, chunks: list[Chunk]) -> None:
        """Add embeddings and their corresponding chunks."""
        assert embeddings.shape[0] == len(chunks), "Mismatch between embeddings and chunks"
        assert embeddings.shape[1] == EMBEDDING_DIM, f"Expected dim {EMBEDDING_DIM}, got {embeddings.shape[1]}"
        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(self, query_emb: np.ndarray, top_k: int = 5) -> list[tuple[Chunk, float]]:
        """Search for top-k nearest neighbors, returns (chunk, score) pairs."""
        assert query_emb.shape[0] == 1, "Expected single query embedding"
        scores, indices = self.index.search(query_emb, min(top_k, len(self.chunks)))
        results: list[tuple[Chunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            results.append((self.chunks[idx], float(score)))
        return results

    def save(self) -> None:
        """Persist index and chunks to disk."""
        faiss.write_index(self.index, self.index_path)
        meta_path = self.index_path + ".meta"
        with open(meta_path, "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self) -> bool:
        """Load index and chunks from disk. Returns True if loaded."""
        if not os.path.exists(self.index_path):
            return False
        meta_path = self.index_path + ".meta"
        if not os.path.exists(meta_path):
            return False
        self.index = faiss.read_index(self.index_path)
        with open(meta_path, "rb") as f:
            self.chunks = pickle.load(f)
        return True

    def clear(self) -> None:
        """Reset the index."""
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.chunks = []

    @property
    def count(self) -> int:
        return len(self.chunks)