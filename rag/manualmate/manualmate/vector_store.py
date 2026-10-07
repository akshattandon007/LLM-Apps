"""Numpy-based vector store for ManualMate.

Stores embeddings as .npy arrays and chunk metadata as JSON.
Follows the same pattern as GardenGuide for consistency.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from manualmate.models import Chunk, SearchResult

# Default store directory
STORE_DIR = Path.home() / ".manualmate"
CHUNKS_FILE = "chunks.json"
EMBEDDINGS_FILE = "embeddings.npy"
DOCS_FILE = "docs.json"


class VectorStore:
    """Persistent vector store using numpy arrays + JSON metadata."""

    def __init__(self, store_dir: Optional[str] = None):
        self.store_dir = Path(store_dir) if store_dir else STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.chunks: List[Chunk] = []
        self.embeddings: Optional[np.ndarray] = None  # shape: (n_chunks, dim)
        self.documents: Dict[str, str] = {}  # doc_id → full text

        self._load()

    # ─── Persistence ──────────────────────────────────────────────────────

    def _path(self, name: str) -> Path:
        return self.store_dir / name

    def _save(self) -> None:
        """Persist all data to disk."""
        # Chunks metadata → JSON
        chunks_data = [
            {
                "text": c.text,
                "source": c.source,
                "doc_id": c.doc_id,
                "index": c.index,
                "char_start": c.char_start,
                "char_end": c.char_end,
            }
            for c in self.chunks
        ]
        self._path(CHUNKS_FILE).write_text(
            json.dumps(chunks_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Embeddings → .npy
        if self.embeddings is not None and len(self.embeddings) > 0:
            np.save(str(self._path(EMBEDDINGS_FILE)), self.embeddings)

        # Document texts → JSON
        self._path(DOCS_FILE).write_text(
            json.dumps(self.documents, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load(self) -> None:
        """Load all data from disk."""
        # Chunks
        cp = self._path(CHUNKS_FILE)
        if cp.exists():
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
                self.chunks = [Chunk(**d) for d in data]
            except (json.JSONDecodeError, KeyError):
                self.chunks = []

        # Embeddings
        ep = self._path(EMBEDDINGS_FILE)
        if ep.exists():
            try:
                self.embeddings = np.load(str(ep))
            except Exception:
                self.embeddings = None

        # Documents
        dp = self._path(DOCS_FILE)
        if dp.exists():
            try:
                self.documents = json.loads(dp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                self.documents = {}

    # ─── Mutation ─────────────────────────────────────────────────────────

    def add_chunks(self, chunks: List[Chunk], embeddings: np.ndarray) -> None:
        """Add chunks and their embeddings to the store."""
        n = len(chunks)
        if n == 0:
            return
        assert embeddings.shape[0] == n, f"Expected {n} embeddings, got {embeddings.shape[0]}"

        self.chunks.extend(chunks)

        if self.embeddings is None or len(self.embeddings) == 0:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

        self._save()

    def store_doc_text(self, doc_id: str, text: str) -> None:
        """Store the full document text for later reference."""
        self.documents[doc_id] = text
        dp = self._path(DOCS_FILE)
        dp.write_text(
            json.dumps(self.documents, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def remove_doc(self, doc_id: str) -> bool:
        """Remove all chunks belonging to a document. Returns True if removed."""
        initial_count = len(self.chunks)

        # Find indices to remove
        indices_to_keep = [
            i for i, c in enumerate(self.chunks) if c.doc_id != doc_id
        ]
        self.chunks = [c for c in self.chunks if c.doc_id != doc_id]
        self.documents.pop(doc_id, None)

        if len(indices_to_keep) < initial_count:
            if self.embeddings is not None and len(self.embeddings) > 0:
                self.embeddings = self.embeddings[indices_to_keep]
            self._save()
            return True

        return False

    def list_docs(self) -> Dict[str, int]:
        """Return {doc_id: chunk_count} for all stored documents."""
        counts: Dict[str, int] = {}
        for c in self.chunks:
            counts[c.doc_id] = counts.get(c.doc_id, 0) + 1
        return counts

    def clear(self) -> None:
        """Delete all stored data."""
        self.chunks = []
        self.embeddings = None
        self.documents = {}
        self._save()
        # Also remove the files to start fresh
        for name in [CHUNKS_FILE, EMBEDDINGS_FILE, DOCS_FILE]:
            p = self._path(name)
            if p.exists():
                p.unlink()

    # ─── Search ───────────────────────────────────────────────────────────

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[SearchResult]:
        """Search for top-k most similar chunks by cosine similarity.

        Args:
            query_embedding: (dim,) embedding vector.
            top_k: Number of results to return.

        Returns:
            List of SearchResult sorted by score descending.
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        # Normalize query
        q_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-12)

        # Normalize stored embeddings row-wise
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
        stored_normed = self.embeddings / norms

        # Cosine similarity = dot product of normalized vectors
        scores = stored_normed @ q_norm  # shape: (n_chunks,)

        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            results.append(SearchResult(
                chunk=self.chunks[idx],
                score=score,
            ))

        return results