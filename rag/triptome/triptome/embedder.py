"""Vector store management for TripTome using FAISS + fastembed.

FAISS handles vector search with HNSW index for approximate nearest neighbor.
fastembed provides lightweight ONNX-based embeddings (all-MiniLM-L6-v2).
No GPU or external API needed.
"""

import os
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import faiss
from fastembed import TextEmbedding

from triptome.models import Document, SearchResult


# Default persist directory — user can override with TRIPTOME_DB_DIR
DEFAULT_DB_DIR = os.path.expanduser("~/.triptome")


def _get_db_dir() -> Path:
    """Get the database directory."""
    return Path(os.environ.get("TRIPTOME_DB_DIR", DEFAULT_DB_DIR))


def _get_embedder():
    """Get or create the embedding model (cached by fastembed internally)."""
    return TextEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        providers=["CPUExecutionProvider"],
    )


def _get_index_path() -> Path:
    return _get_db_dir() / "triptome.index"


def _get_meta_path() -> Path:
    return _get_db_dir() / "triptome.meta"


def _ensure_db_dir():
    _get_db_dir().mkdir(parents=True, exist_ok=True)


def _embed_texts(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts using fastembed.

    Returns a float32 numpy array of shape (len(texts), 384).
    """
    embedder = _get_embedder()
    # fastembed returns iterable of numpy arrays
    embeddings = list(embedder.embed(texts))
    return np.array(embeddings, dtype=np.float32)


def _build_index(dimension: int = 384) -> faiss.Index:
    """Build a new HNSW index for cosine similarity via normalized L2."""
    index = faiss.IndexHNSWFlat(dimension, 32)  # 32 neighbors
    index.hnsw.efConstruction = 200
    index.hnsw.efSearch = 64
    # HNSWFlat uses L2 distance. We normalize vectors so L2 = cosine.
    return index


def _normalize(embeddings: np.ndarray) -> np.ndarray:
    """L2-normalize embeddings so L2 distance maps to cosine similarity."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return embeddings / norms


def index_documents(documents: list[Document],
                    db_dir: Optional[str] = None) -> int:
    """Index a list of documents into the FAISS vector store.

    Returns the number of documents indexed.
    Append-only: loads existing index, adds new docs, saves.
    """
    if not documents:
        return 0

    if db_dir:
        os.environ["TRIPTOME_DB_DIR"] = db_dir

    _ensure_db_dir()
    index_path = _get_index_path()
    meta_path = _get_meta_path()

    # Load existing index/meta if present
    if index_path.exists() and meta_path.exists():
        index = faiss.read_index(str(index_path))
        with open(meta_path, "rb") as f:
            metadata: list[dict] = pickle.load(f)
    else:
        index = _build_index()
        metadata = []

    # Prepare texts and metadata
    texts = [d.text for d in documents]
    for d in documents:
        metadata.append({
            "text": d.text,
            "source": d.source,
            "page": d.page,
            "chunk_id": d.chunk_id,
        })

    # Embed and normalize
    embeddings = _embed_texts(texts)
    normalized = _normalize(embeddings)

    # Add to index (sequential IDs auto-assigned by FAISS)
    index.add(normalized)

    # Save
    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    return len(documents)


def search(query: str, n_results: int = 5,
           db_dir: Optional[str] = None) -> list[SearchResult]:
    """Search the vector store for the query.

    Returns the top-N most relevant results with similarity scores.
    """
    if db_dir:
        os.environ["TRIPTOME_DB_DIR"] = db_dir

    index_path = _get_index_path()
    meta_path = _get_meta_path()

    if not index_path.exists() or not meta_path.exists():
        return []

    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        metadata: list[dict] = pickle.load(f)

    if index.ntotal == 0:
        return []

    # Embed query
    query_emb = _embed_texts([query])
    query_norm = _normalize(query_emb)

    # Search (returns L2 distances on normalized vectors)
    n_search = min(n_results, index.ntotal)
    distances, indices = index.search(query_norm, n_search)

    output: list[SearchResult] = []
    for i in range(n_search):
        idx = indices[0][i]
        if idx < 0:
            continue
        # FAISS L2 distance on L2-normalized vectors:
        #   ||a - b||^2 = 2 - 2*cos(a,b)
        #   cos(a,b) = 1 - (||a - b||^2 / 2)
        l2_dist = distances[0][i]
        cosine_sim = max(0.0, 1.0 - (l2_dist * l2_dist) / 2.0)

        meta = metadata[idx]
        output.append(SearchResult(
            text=meta["text"],
            source=meta["source"],
            page=meta.get("page"),
            score=round(cosine_sim, 4),
            chunk_id=meta.get("chunk_id", 0),
        ))

    # Sort by score descending
    output.sort(key=lambda r: r.score, reverse=True)
    return output


def get_stats(db_dir: Optional[str] = None) -> dict:
    """Get statistics about the indexed collection."""
    if db_dir:
        os.environ["TRIPTOME_DB_DIR"] = db_dir

    index_path = _get_index_path()
    meta_path = _get_meta_path()

    if not index_path.exists() or not meta_path.exists():
        return {"total_chunks": 0, "sources": [], "source_count": 0}

    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        metadata: list[dict] = pickle.load(f)

    sources = sorted(set(m["source"] for m in metadata if "source" in m))
    return {
        "total_chunks": index.ntotal,
        "sources": sources,
        "source_count": len(sources),
    }


def reset(db_dir: Optional[str] = None):
    """Delete the index and start fresh."""
    if db_dir:
        os.environ["TRIPTOME_DB_DIR"] = db_dir

    index_path = _get_index_path()
    meta_path = _get_meta_path()

    for p in [index_path, meta_path]:
        if p.exists():
            p.unlink()