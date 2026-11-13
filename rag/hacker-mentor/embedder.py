"""
Embedder — wrapper around sentence-transformers for generating embeddings.

Uses the lightweight all-MiniLM-L6-v2 model (~80MB, 384-dim embeddings).
"""

from sentence_transformers import SentenceTransformer
from typing import Any
import numpy as np


class Embedder:
    """Text embedding service using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Any = None

    def _load_model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string. Returns 384-dim numpy array."""
        self._load_model()
        return self._model.encode(text, normalize_embeddings=True)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts. Returns (N, 384) numpy array."""
        self._load_model()
        return self._model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
