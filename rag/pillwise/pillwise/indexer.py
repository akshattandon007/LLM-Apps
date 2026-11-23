"""Build and query a FAISS index over drug label chunks using sentence-transformers."""

import pickle
import numpy as np
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_embedder(model_name: str = "all-MiniLM-L6-v2"):
    """Load a sentence-transformers model lazily."""
    from sentence_transformers import SentenceTransformer
    print(f"Loading embedding model: {model_name} ...")
    return SentenceTransformer(model_name)


def build_index(
    chunks: list[dict],
    model_name: str = "all-MiniLM-L6-v2",
    save: bool = True,
    force_rebuild: bool = False,
) -> tuple:
    """Build a FAISS index over chunk texts.

    Returns:
        (index, chunk_texts, metadata_list)
    """
    import faiss

    index_path = DATA_DIR / "faiss_index.bin"
    meta_path = DATA_DIR / "index_meta.pkl"

    if not force_rebuild and index_path.exists() and meta_path.exists():
        print("Loading existing index from disk...")
        index = faiss.read_index(str(index_path))
        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
        return index, meta["texts"], meta["metadata"]

    print(f"Building index over {len(chunks)} chunks...")
    model = get_embedder(model_name)
    texts = [c["text"] for c in chunks]
    metadata = [{"drug_id": c["drug_id"], "drug_name": c["drug_name"],
                  "field": c["field"], "field_label": c["field_label"],
                  "source": c["source"]} for c in chunks]

    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity (normalized)
    index.add(np.array(embeddings, dtype=np.float32))
    print(f"Index built: {index.ntotal} vectors, dim={dim}")

    if save:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(index_path))
        with open(meta_path, "wb") as f:
            pickle.dump({"texts": texts, "metadata": metadata}, f)
        print(f"Saved index to {index_path}")

    return index, texts, metadata


def search(index, texts, metadata, query: str, k: int = 5,
           model_name: str = "all-MiniLM-L6-v2") -> list[dict]:
    """Search the index for chunks relevant to the query.

    Returns list of dicts with text, metadata, and relevance score.
    """
    model = get_embedder(model_name)
    query_vec = model.encode([query], normalize_embeddings=True)
    scores, indices = index.search(np.array(query_vec, dtype=np.float32), k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(texts):
            continue
        results.append({
            "text": texts[idx],
            "score": float(score),
            **metadata[idx],
        })
    return results
