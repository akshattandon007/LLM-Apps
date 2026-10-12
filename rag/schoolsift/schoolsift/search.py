"""Retrieval: rank indexed chunks against a plain-language question.

A 0.65/0.35 blend of cosine similarity over tf-idf vectors and BM25.
Cosine prefers whole-phrase topical match; BM25 counters the length bias of
raw tf-idf (short permission slips don't get drowned out).
"""
from __future__ import annotations

import math

from .tokenize import terms

COSINE_WEIGHT = 0.65
BM25_WEIGHT = 0.35
BM25_K1 = 1.5
BM25_B = 0.75


def _cosine(qvec: dict[str, float], cvec: dict[str, float]) -> float:
    dot = sum(w * cvec.get(t, 0.0) for t, w in qvec.items())
    qnorm = math.sqrt(sum(w * w for w in qvec.values())) or 1.0
    cnorm = math.sqrt(sum(w * w for w in cvec.values())) or 1.0
    return dot / (qnorm * cnorm)


def _bm25(qterms: set[str], counts: dict[str, int], doc_len: int,
          avgdl: float, n: int, df: dict[str, int]) -> float:
    score = 0.0
    for t in qterms:
        tf = counts.get(t, 0)
        if not tf:
            continue
        df_t = df.get(t, 1)
        idf_b = math.log(1 + (n - df_t + 0.5) / (df_t + 0.5))
        denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / max(avgdl, 1.0))
        score += idf_b * (tf * (BM25_K1 + 1)) / denom
    return score


def search(store, question: str, k: int = 5) -> list[dict]:
    """Return the top-k most relevant chunks as [{score, chunk, doc}, ...].

    An empty result means no indexed chunk shares any meaningful term with
    the question.
    """
    qterms = set(terms(question))
    if not qterms:
        return []

    qvec = {t: w for t in qterms if (w := store.idf.get(t, 0.0)) > 0}
    if not qvec:
        return []

    n = len(store.chunks)
    if n == 0:
        return []

    cosine_scores = [
        _cosine(qvec, store.vectors[i]) for i in range(n)
    ]
    bm25_scores = [
        _bm25(qterms, store.counts[i], store.doc_lens[i], store.avgdl, n, store.df)
        for i in range(n)
    ]
    max_bm25 = max(bm25_scores) if bm25_scores else 0.0
    if max_bm25 <= 0:
        bm25_norm = [0.0] * n
    else:
        bm25_norm = [s / max_bm25 for s in bm25_scores]

    ranked = [
        (COSINE_WEIGHT * cosine_scores[i] + BM25_WEIGHT * bm25_norm[i], i)
        for i in range(n)
    ]
    ranked.sort(key=lambda x: x[0], reverse=True)

    hits = []
    for blend, i in ranked[:k]:
        if blend <= 0.0:
            continue
        chunk = store.chunks[i]
        hits.append({
            "score": round(blend, 4),
            "chunk": chunk,
            "doc": store.docs[chunk["doc_id"]],
        })
    return hits