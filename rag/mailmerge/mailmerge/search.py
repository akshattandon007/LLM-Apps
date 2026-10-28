"""Search the ChromaDB index — embed query, retrieve, rank, display."""

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .models import SearchResult

# ── Config ──────────────────────────────────────────────────────────────────

DEFAULT_DB_DIR = os.path.expanduser("~/.mailmerge/chroma")
DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 10

_client: Optional[chromadb.ClientAPI] = None
_encoder: Optional[SentenceTransformer] = None


def _get_client(db_dir: str = DEFAULT_DB_DIR) -> chromadb.ClientAPI:
    global _client
    if _client is None:
        Path(db_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=db_dir,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _get_encoder(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformer(model_name)
    return _encoder


def get_or_create_collection(name: str = "mailmerge", db_dir: str = DEFAULT_DB_DIR):
    """Get or create a ChromaDB collection."""
    client = _get_client(db_dir)
    try:
        return client.get_collection(name)
    except ValueError:
        return client.create_collection(name)


def add_chunks(
    chunks: list[dict],
    collection_name: str = "mailmerge",
    db_dir: str = DEFAULT_DB_DIR,
    batch_size: int = 100,
):
    """Add email chunks to the vector store.

    chunks: list of dicts with keys: id, text, subject, sender, date, labels
    """
    collection = get_or_create_collection(collection_name, db_dir)
    encoder = _get_encoder()

    total = len(chunks)
    for start in range(0, total, batch_size):
        batch = chunks[start : start + batch_size]
        ids = [c["id"] for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [
            {
                "subject": c.get("subject", "")[:500],
                "sender": c.get("sender", "")[:200],
                "date": c.get("date", "")[:100],
                "labels": c.get("labels", ""),
            }
            for c in batch
        ]

        embeddings = encoder.encode(texts, show_progress_bar=False).tolist()
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)


def search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    collection_name: str = "mailmerge",
    db_dir: str = DEFAULT_DB_DIR,
    metadata_filter: Optional[dict] = None,
) -> list[SearchResult]:
    """Query the vector store and return ranked results."""
    collection = get_or_create_collection(collection_name, db_dir)
    encoder = _get_encoder()

    query_emb = encoder.encode([query], show_progress_bar=False).tolist()

    where = None
    if metadata_filter:
        where = {}
        for k, v in metadata_filter.items():
            where[k] = v

    results = collection.query(
        query_embeddings=query_emb,
        n_results=min(top_k, 50),
        where=where,
    )

    hits: list[SearchResult] = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            meta = (results["metadatas"][0][i]) if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0.0
            doc_text = (results["documents"][0][i]) if results["documents"] else ""
            score = 1.0 / (1.0 + dist)  # convert L2 distance to similarity score
            hits.append(
                SearchResult(
                    chunk_id=doc_id,
                    subject=meta.get("subject", "(no subject)"),
                    sender=meta.get("sender", "(unknown)"),
                    date=meta.get("date", "(no date)"),
                    snippet=doc_text[:300].replace("\n", " "),
                    score=score,
                )
            )

    return hits