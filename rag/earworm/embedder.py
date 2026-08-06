"""Earworm — embedding generation and FAISS index management."""

import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from models import DB_DIR

INDEX_DIR = os.path.join(DB_DIR, "index")
os.makedirs(INDEX_DIR, exist_ok=True)

INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")
ID_MAP_PATH = os.path.join(INDEX_DIR, "id_map.pkl")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 produces 384-dim vectors


def load_model() -> SentenceTransformer:
    """Load the sentence-transformers model (singleton for reuse)."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(
    texts: list[str], model: SentenceTransformer | None = None
) -> np.ndarray:
    """Embed a list of text strings. Returns (N, 384) float32 array."""
    if model is None:
        model = load_model()
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, EMBEDDING_DIM)
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.astype(np.float32)


def create_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Create a FAISS inner-product index (cosine similarity with normalized vectors)."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    if embeddings.shape[0] > 0:
        index.add(embeddings)
    return index


def load_index() -> faiss.IndexFlatIP | None:
    """Load the FAISS index from disk, or None if not yet built."""
    if os.path.exists(INDEX_PATH):
        return faiss.read_index(INDEX_PATH)
    return None


def save_index(index: faiss.IndexFlatIP):
    """Save the FAISS index to disk."""
    faiss.write_index(index, INDEX_PATH)


def load_id_map() -> dict[int, int]:
    """Load the mapping: FAISS index position -> chunk DB id."""
    if os.path.exists(ID_MAP_PATH):
        with open(ID_MAP_PATH, "rb") as f:
            return pickle.load(f)
    return {}


def save_id_map(id_map: dict[int, int]):
    """Save the FAISS position -> chunk ID mapping."""
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(id_map, f)


def search(
    query: str,
    model: SentenceTransformer,
    index: faiss.IndexFlatIP,
    id_map: dict[int, int],
    top_k: int = 10,
) -> list[tuple[int, float]]:
    """Search the index. Returns list of (chunk_db_id, similarity_score)."""
    if index is None or index.ntotal == 0:
        return []
    query_vec = embed_texts([query], model=model)
    scores, positions = index.search(query_vec, min(top_k, index.ntotal))
    results = []
    for pos, score in zip(positions[0], scores[0]):
        if pos < 0 or score < 0:
            continue
        chunk_id = id_map.get(int(pos))
        if chunk_id is not None:
            results.append((chunk_id, float(score)))
    return results


def rebuild_index_from_db(conn, model: SentenceTransformer | None = None):
    """Rebuild the entire FAISS index from all chunks in the database.

    Returns (index, id_map).
    """
    from models import get_chunks_by_ids

    if model is None:
        model = load_model()

    # Get all chunk IDs
    cur = conn.execute("SELECT id, text FROM chunks")
    rows = cur.fetchall()

    if not rows:
        index = create_index(np.array([], dtype=np.float32).reshape(0, EMBEDDING_DIM))
        id_map = {}
        save_index(index)
        save_id_map(id_map)
        return index, id_map

    chunk_ids = [r["id"] for r in rows]
    texts = [r["text"] for r in rows]

    # Embed in batches to avoid memory issues
    batch_size = 256
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        emb = embed_texts(batch, model=model)
        all_embeddings.append(emb)

    embeddings = np.vstack(all_embeddings)
    index = create_index(embeddings)
    id_map = {i: cid for i, cid in enumerate(chunk_ids)}

    save_index(index)
    save_id_map(id_map)

    return index, id_map