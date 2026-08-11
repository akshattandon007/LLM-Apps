"""Embedding with sentence-transformers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.models import Chunk


class Embedder:
    """Wraps a sentence-transformers model for code embedding."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name)

    def embed(self, text: str) -> NDArray[np.float32]:
        """Embed a single text string."""
        self._load()
        return self._model.encode(text, normalize_embeddings=True, show_progress_bar=False)

    def embed_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Embed a batch of texts."""
        self._load()
        return self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def embed_chunks(self, chunks: list[Chunk]) -> tuple[list[str], NDArray[np.float32]]:
        """Embed a list of Chunks.

        Returns (texts, embeddings) where texts[i] is the text representation
        that was embedded and embeddings[i] is its vector.
        """
        texts = []
        for c in chunks:
            text_parts = []
            if c.docstring:
                text_parts.append(c.docstring)
            text_parts.append(f"File: {c.file_path}")
            text_parts.append(f"Name: {c.name}")
            text_parts.append(f"Type: {c.chunk_type}")
            text_parts.append(c.content)
            texts.append("\n".join(text_parts))

        embeddings = self.embed_batch(texts)
        return texts, embeddings

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        self._load()
        return self._model.get_sentence_embedding_dimension()
