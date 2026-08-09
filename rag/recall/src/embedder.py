"""Embedding interface using sentence-transformers.

Wraps the all-MiniLM-L6-v2 model with lazy loading so the model is only
loaded once, on first use.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Get or load the sentence-transformers model (cached)."""
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str | list[str]) -> np.ndarray:
    """Embed a single string or list of strings.

    Returns a numpy array of shape (n_texts, embedding_dim).
    """
    model = _get_model()
    if isinstance(text, str):
        text = [text]
    embeddings = model.encode(text, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)


def embed_chunks(texts: list[str]) -> np.ndarray:
    """Embed a list of chunk texts.

    Returns a numpy array of shape (len(texts), 384) — the embedding dimension
    for all-MiniLM-L6-v2.
    """
    return embed_text(texts)