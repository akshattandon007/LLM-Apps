"""Local vector index over Notion page chunks.

Uses:
- `sentence-transformers` (all-MiniLM-L6-v2) for cheap CPU embeddings.
- `numpy` for the similarity search (cosine via normalised inner product).
- `pickle` + `.npy` for persistence.

We deliberately *don't* pull in FAISS here. For the ≤100k-chunk scale a
single user's Notion workspace will ever hit, numpy's brute-force search
is fast enough (tens of milliseconds) and removes a heavyweight native
dependency that's annoying to install on macOS/Windows.

If a user's workspace ever grows past ~500k chunks, swapping the search
function for `faiss.IndexFlatIP` is a dozen-line change.
"""
from __future__ import annotations

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A single retrievable chunk of text, with page provenance."""

    chunk_id: str
    page_id: str
    page_title: str
    page_url: str
    text: str
    # Position in the page (0-indexed) — helps with citation clarity.
    position: int


def chunk_text(
    text: str,
    chunk_size: int = 1800,
    overlap: int = 300,
) -> list[str]:
    """Split `text` into overlapping character-windowed chunks.

    We split on paragraph boundaries where possible to avoid cutting
    mid-sentence. Character-based sizing is a decent proxy for token count
    (~4 chars/token for English) and avoids dragging in a tokenizer.
    """
    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [text]

    paragraphs = [p for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # If adding this paragraph keeps us under the limit, do it.
        candidate = f"{current}\n{para}" if current else para
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        # Otherwise flush the current chunk.
        if current:
            chunks.append(current)
        # A single paragraph longer than chunk_size gets hard-sliced.
        if len(para) > chunk_size:
            start = 0
            while start < len(para):
                chunks.append(para[start : start + chunk_size])
                start += chunk_size - overlap
            current = ""
        else:
            current = para

    if current:
        chunks.append(current)

    # Add overlap by prefixing each chunk with a tail of the previous one.
    if overlap > 0 and len(chunks) > 1:
        with_overlap = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:]
            with_overlap.append(f"{tail}\n{chunks[i]}")
        chunks = with_overlap

    return chunks


class VectorStore:
    """Persistent local vector index over page chunks."""

    _EMBEDDINGS_FILE = "embeddings.npy"
    _METADATA_FILE = "chunks.pkl"
    _MANIFEST_FILE = "manifest.json"

    def __init__(self, index_dir: Path, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self._model = None  # Lazy-loaded — avoids a 2s import on CLI commands that don't need it.
        self._embeddings: np.ndarray | None = None
        self._chunks: list[Chunk] = []

    # --------------------------------------------------------------- lifecycle

    @property
    def model(self):
        """Lazily import and instantiate the embedding model."""
        if self._model is None:
            # Local import so we don't pay the ~1-2s torch import cost
            # unless the user actually runs a command that needs embeddings.
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def load(self) -> bool:
        """Load a persisted index from disk. Returns False if none exists."""
        emb_path = self.index_dir / self._EMBEDDINGS_FILE
        meta_path = self.index_dir / self._METADATA_FILE
        if not (emb_path.exists() and meta_path.exists()):
            return False
        self._embeddings = np.load(emb_path)
        with open(meta_path, "rb") as f:
            self._chunks = pickle.load(f)
        logger.info("Loaded %d chunks from %s", len(self._chunks), self.index_dir)
        return True

    def save(self) -> None:
        """Persist the index to disk."""
        if self._embeddings is None:
            raise RuntimeError("Nothing to save — call build() first.")
        np.save(self.index_dir / self._EMBEDDINGS_FILE, self._embeddings)
        with open(self.index_dir / self._METADATA_FILE, "wb") as f:
            pickle.dump(self._chunks, f)
        manifest = {
            "model_name": self.model_name,
            "num_chunks": len(self._chunks),
            "num_pages": len({c.page_id for c in self._chunks}),
            "dimension": int(self._embeddings.shape[1]),
        }
        with open(self.index_dir / self._MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info("Saved index: %s", manifest)

    # --------------------------------------------------------------- building

    def build(self, chunks: list[Chunk], batch_size: int = 64) -> None:
        """Embed every chunk and replace the current index."""
        if not chunks:
            logger.warning("No chunks to index.")
            self._chunks = []
            self._embeddings = np.zeros((0, 384), dtype=np.float32)
            return

        texts = [c.text for c in chunks]
        logger.info("Embedding %d chunks...", len(texts))
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,  # Lets us use inner product = cosine similarity.
        )
        self._embeddings = vectors.astype(np.float32)
        self._chunks = chunks

    # ---------------------------------------------------------------- search

    def search(self, query: str, top_k: int = 8) -> list[tuple[Chunk, float]]:
        """Return the top-k most similar chunks with their cosine scores."""
        if self._embeddings is None or len(self._chunks) == 0:
            return []
        query_vec = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)
        # Since both sides are L2-normalised, inner product == cosine similarity.
        scores = (self._embeddings @ query_vec.T).squeeze(axis=1)
        top_k = min(top_k, len(scores))
        top_idx = np.argpartition(-scores, top_k - 1)[:top_k]
        # Sort the top_k by score for nicer output.
        top_idx = top_idx[np.argsort(-scores[top_idx])]
        return [(self._chunks[i], float(scores[i])) for i in top_idx]

    # ------------------------------------------------------------- introspect

    def stats(self) -> dict:
        manifest_path = self.index_dir / self._MANIFEST_FILE
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return {"num_chunks": len(self._chunks), "num_pages": len({c.page_id for c in self._chunks})}

    def to_jsonable(self, chunks: list[tuple[Chunk, float]]) -> list[dict]:
        """Convenience: turn search results into JSON-safe dicts for tool outputs."""
        return [{**asdict(c), "score": round(s, 4)} for c, s in chunks]
