"""FAISS-based vector store with domain-scoped retrieval.

Indexes chunks by embedding and supports retrieval filtered by legal domain.
The index is persisted to disk so it survives a server restart.
"""

import json
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from src.embedder import embed_texts, embed_query
from src.models import Chunk
from src.chunker import chunk_and_tag
from src.document_loader import load_lease

# Default paths — relative to the project root.
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INDEX_PATH = DEFAULT_DATA_DIR / "lease_index.faiss"
META_PATH = DEFAULT_DATA_DIR / "lease_meta.json"


class LeaseVectorStore:
    """Domain-aware FAISS index for lease chunks."""

    def __init__(self, data_dir: str | Path = DEFAULT_DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.data_dir / "lease_index.faiss"
        self.meta_path = self.data_dir / "lease_meta.json"

        self.index: Optional[faiss.Index] = None
        self.chunks: list[Chunk] = []
        self._domain_map: dict[str, list[int]] = {}  # domain -> chunk indices

    def ingest_pdf(self, pdf_path: str | Path) -> int:
        """Load a PDF, chunk it, embed, and build the FAISS index."""
        pages = load_lease(str(pdf_path))
        self.chunks = chunk_and_tag(pages)

        if not self.chunks:
            raise ValueError("No chunks extracted from the PDF.")

        texts = [c.text for c in self.chunks]
        embeddings = embed_texts(texts)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        # Build domain map
        self._domain_map.clear()
        for i, chunk in enumerate(self.chunks):
            self._domain_map.setdefault(chunk.domain, []).append(i)

        self._persist()
        return len(self.chunks)

    def search(self, query: str, domain: str = "GENERAL", top_k: int = 5) -> list[Chunk]:
        """Retrieve top-k chunks for a query, filtered by legal domain."""
        if self.index is None or not self.chunks:
            return []

        # Get candidate indices for this domain
        domain_indices = self._domain_map.get(domain, [])
        if not domain_indices:
            # Fallback to GENERAL or all chunks
            domain_indices = self._domain_map.get("GENERAL", list(range(len(self.chunks))))
        if not domain_indices:
            return []

        # Build a sub-index for the domain
        domain_vecs = np.array([self.index.reconstruct(int(i)) for i in domain_indices])
        sub_index = faiss.IndexFlatIP(self.index.d)
        sub_index.add(domain_vecs)

        query_vec = embed_query(query)
        distances, idxs = sub_index.search(query_vec, min(top_k, len(domain_indices)))

        results = []
        for idx in idxs[0]:
            if idx == -1:
                continue
            actual_idx = domain_indices[int(idx)]
            results.append(self.chunks[actual_idx])
        return results

    def get_domains(self) -> list[str]:
        """Return the legal domains present in the index."""
        return list(self._domain_map.keys())

    def _persist(self) -> None:
        """Write index and metadata to disk."""
        if self.index is None:
            return
        faiss.write_index(self.index, str(self.index_path))
        meta = [
            {
                "text": c.text,
                "domain": c.domain,
                "clause_ref": c.clause_ref,
                "page_number": c.page_number,
            }
            for c in self.chunks
        ]
        with open(self.meta_path, "w") as f:
            json.dump(meta, f)

    def load(self) -> bool:
        """Load a previously persisted index from disk. Returns True on success."""
        if not self.index_path.exists() or not self.meta_path.exists():
            return False
        self.index = faiss.read_index(str(self.index_path))
        with open(self.meta_path) as f:
            meta = json.load(f)
        self.chunks = [Chunk(**m) for m in meta]
        self._domain_map.clear()
        for i, chunk in enumerate(self.chunks):
            self._domain_map.setdefault(chunk.domain, []).append(i)
        return True


# Module-level singleton for convenience
_store: Optional[LeaseVectorStore] = None


def get_store() -> LeaseVectorStore:
    global _store
    if _store is None:
        _store = LeaseVectorStore()
        _store.load()
    return _store