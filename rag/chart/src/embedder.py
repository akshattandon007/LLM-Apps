"""Embedding with sentence-transformers (all-MiniLM-L6-v2)."""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# Global lazy-loaded model
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        cache = os.environ.get("HF_HOME", "/tmp/chart-hf-cache")
        os.makedirs(cache, exist_ok=True)
        _model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=cache)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of texts, returning a numpy array of shape (n, 384)."""
    model = _get_model()
    return model.encode(texts, show_progress_bar=False, normalize_embeddings=True)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string, returning shape (1, 384)."""
    model = _get_model()
    return model.encode([query], show_progress_bar=False, normalize_embeddings=True)