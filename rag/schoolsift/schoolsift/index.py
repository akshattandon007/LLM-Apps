"""TF-IDF + BM25 document index with JSON persistence.

The index is intentionally dependency-free: a school folder is tens of small
documents, so a pure-Python lexical index is fast, deterministic, and trivially
testable — no torch, no ChromaDB, no API keys.
"""
from __future__ import annotations

import json
import math
import time
from collections import Counter
from pathlib import Path

from .tokenize import terms


class Store:
    """An in-memory index that can be saved to / loaded from one JSON file."""

    def __init__(self) -> None:
        self.docs: list[dict] = []                    # {id, path, title, pages, chunk_count}
        self.chunks: list[dict] = []                  # {id, doc_id, page, text}
        self.vocab: list[str] = []
        self.idf: dict[str, float] = {}
        self.df: dict[str, int] = {}                  # document frequency per term
        self.vectors: list[dict[str, float]] = []     # per-chunk tf-idf vectors
        self.counts: list[dict[str, int]] = []        # per-chunk raw term counts
        self.doc_lens: list[int] = []                 # per-chunk term counts total
        self.avgdl: float = 1.0
        self.built_at: str | None = None

    # -- persistence ---------------------------------------------------------

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "built_at": self.built_at,
            "docs": self.docs,
            "chunks": self.chunks,
            "vocab": self.vocab,
            "idf": self.idf,
            "df": self.df,
            "vectors": self.vectors,
            "counts": self.counts,
            "doc_lens": self.doc_lens,
            "avgdl": self.avgdl,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True)

    @classmethod
    def load(cls, path: str | Path) -> "Store":
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        store = cls()
        store.docs = payload["docs"]
        store.chunks = payload["chunks"]
        store.vocab = payload["vocab"]
        store.idf = {k: float(v) for k, v in payload["idf"].items()}
        store.df = payload.get("df", {})
        store.vectors = payload["vectors"]
        store.counts = payload["counts"]
        store.doc_lens = payload["doc_lens"]
        store.avgdl = float(payload.get("avgdl", 1.0))
        store.built_at = payload.get("built_at")
        return store


def build(docs: list[dict]) -> Store:
    """Build a Store from ingest.ingest_folder() output.

    Chunks are flattened into a single list with globally unique ids; each
    chunk gets a tf-idf vector (for cosine similarity) and raw term counts
    (for BM25).
    """
    store = Store()
    flat: list[dict] = []
    for doc in docs:
        for c in doc.get("chunks", []):
            flat.append({
                "id": len(flat),
                "doc_id": doc["id"],
                "page": c["page"],
                "text": c["text"],
            })
    store.chunks = flat
    store.docs = [
        {
            "id": d["id"],
            "path": d["path"],
            "title": d["title"],
            "pages": d.get("pages", 1),
            "chunk_count": len(d.get("chunks", [])),
        }
        for d in docs
    ]

    n = len(flat)
    df: Counter = Counter()
    chunk_terms: list[list[str]] = []
    for c in flat:
        ts = terms(c["text"])
        chunk_terms.append(ts)
        df.update(set(ts))

    store.vocab = sorted(df)
    store.df = dict(df)
    # Smoothed idf: log(1 + N/(1+df)) keeps rare-but-present terms meaningful
    # and avoids divide-by-zero for terms appearing in every chunk.
    store.idf = {t: math.log(1 + n / (1 + df[t])) for t in store.vocab}

    for ts in chunk_terms:
        cnt = Counter(ts)
        store.counts.append(dict(cnt))
        store.doc_lens.append(len(ts))
        store.vectors.append({
            t: (1 + math.log(cnt[t])) * store.idf[t] for t in cnt
        })
    store.avgdl = (sum(store.doc_lens) / n) if n else 1.0
    store.built_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return store