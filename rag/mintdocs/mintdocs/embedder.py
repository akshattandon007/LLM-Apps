"""Embed filing chunks using sentence-transformers."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from .models import Chunk

# ------------------------------------------------------------------
# Lazy import: sentence-transformers is heavy and only loaded in
# production mode (simulate=False).
# ------------------------------------------------------------------


class Embedder:
    """Generate embeddings for text chunks.

    In production mode, uses sentence-transformers/all-MiniLM-L6-v2.
    In simulate mode, returns dummy embeddings.
    """

    def __init__(self, simulate: bool = False):
        self.simulate = simulate
        self._model = None

    def _load_model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is not None or self.simulate:
            return
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install with: pip install mintdocs[full]  OR  "
                "pip install sentence-transformers"
            )
        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_chunks(self, chunks: list[Chunk]) -> list[tuple[Chunk, list[float]]]:
        """Embed a list of chunks and return (chunk, embedding_vector) pairs."""
        texts = [chunk.section_text for chunk in chunks]
        vectors = self._embed_texts(texts)
        return list(zip(chunks, vectors))

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self._embed_texts([text])[0]

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Core embedding logic."""
        if self.simulate:
            return self._simulate_embed(texts)

        self._load_model()
        assert self._model is not None
        embeddings = self._model.encode(texts, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def _simulate_embed(self, texts: list[str]) -> list[list[float]]:
        """Return deterministic 384-dim dummy embeddings (MiniLM dimension).

        Uses SHA-256 of each text to seed a stable, deterministic vector —
        same text always gets the same embedding.
        """
        dim = 384
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vec = [((digest[i % 32] + digest[(i + 1) % 32]) / 510.0) for i in range(dim)]
            vectors.append(vec)
        return vectors