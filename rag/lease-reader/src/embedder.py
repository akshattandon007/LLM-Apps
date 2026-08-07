"""Embedding pipeline using sentence-transformers.

Wraps the all-MiniLM-L6-v2 model — lightweight (~80 MB) and fast on CPU,
which is appropriate for a VPS deployment.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

# Singleton model — loaded once, reused across requests.
_EMBEDDER: SentenceTransformer | None = None


def _get_embedder() -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDER


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of strings into a 2-D numpy array of shape (N, 384)."""
    model = _get_embedder()
    return model.encode(texts, show_progress_bar=False, normalize_embeddings=True)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string into a 1-D numpy array of shape (384,)."""
    model = _get_embedder()
    vec = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
    return vec.reshape(1, -1)