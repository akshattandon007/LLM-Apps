"""RAG engine for GardenGuide — chunk, embed, retrieve, and generate answers."""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .doc_loader import load_document, chunk_text

# ── Helpers ──────────────────────────────────────────────────────────────


def _get_openai_client():
    """Lazy-import openai and return a client configured from env."""
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"),
        base_url=os.environ.get(
            "OPENAI_BASE_URL",
            os.environ.get("OPENROUTER_BASE_URL", "https://api.openai.com/v1"),
        ),
    )


# ── Defaults ────────────────────────────────────────────────────────────

DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_GEN_MODEL = "gpt-4o-mini"
DEFAULT_TOP_K = 3

# ── Vector Store ────────────────────────────────────────────────────────


class VectorStore:
    """Persistent vector store for document chunks and their embeddings."""

    def __init__(self, store_dir: str = "~/.gardenguide"):
        self.store_dir = Path(store_dir).expanduser()
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.chunks_file = self.store_dir / "chunks.json"
        self.embeddings_file = self.store_dir / "embeddings.npy"
        self.docs_file = self.store_dir / "docs.json"

        self.chunks: List[str] = []
        self.doc_sources: List[str] = []  # source file per chunk
        self.embeddings: Optional[np.ndarray] = None
        self._documents: Dict[str, str] = {}  # filepath -> original text

        self._load()

    def _load(self):
        if self.chunks_file.exists():
            data = json.loads(self.chunks_file.read_text())
            self.chunks = data.get("chunks", [])
            self.doc_sources = data.get("sources", [])
        if self.embeddings_file.exists():
            self.embeddings = np.load(str(self.embeddings_file))
        else:
            self.embeddings = None
        if self.docs_file.exists():
            self._documents = json.loads(self.docs_file.read_text())

    def _save(self):
        self.chunks_file.write_text(
            json.dumps({"chunks": self.chunks, "sources": self.doc_sources})
        )
        if self.embeddings is not None:
            np.save(str(self.embeddings_file), self.embeddings)
        self.docs_file.write_text(json.dumps(self._documents))

    @property
    def doc_count(self) -> int:
        return len(self._documents)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def list_docs(self) -> List[str]:
        return list(self._documents.keys())

    def add_chunks(
        self, new_chunks: List[str], source: str, new_embeddings: np.ndarray
    ):
        """Add chunks and their embeddings to the store."""
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        self.chunks.extend(new_chunks)
        self.doc_sources.extend([source] * len(new_chunks))
        self._save()

    def remove_doc(self, filepath: str) -> bool:
        """Remove all chunks from a given document. Returns True if found."""
        # Normalize: check both raw and abspath forms
        abs_path = os.path.abspath(filepath)

        # Find which chunk indices belong to this doc
        indices = [i for i, s in enumerate(self.doc_sources) if s == filepath or s == abs_path]
        has_doc_entry = filepath in self._documents or abs_path in self._documents

        if not indices and not has_doc_entry:
            return False

        # Rebuild without those indices
        if indices:
            keep = [i for i in range(len(self.chunks)) if i not in set(indices)]
            if keep:
                self.chunks = [self.chunks[i] for i in keep]
                self.doc_sources = [self.doc_sources[i] for i in keep]
                self.embeddings = self.embeddings[keep, :]
            else:
                self.chunks = []
                self.doc_sources = []
                self.embeddings = None

        # Remove from doc text store
        for key in (filepath, abs_path):
            if key in self._documents:
                del self._documents[key]

        self._save()
        return True

    def search(self, query_embedding: np.ndarray, top_k: int = DEFAULT_TOP_K) -> List[Tuple[str, float, int]]:
        """Return top-k (chunk_text, score, index) by cosine similarity."""
        if self.embeddings is None or self.embeddings.shape[0] == 0:
            return []

        # Normalize query embedding
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-12)

        # Normalize stored embeddings along rows
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-12
        stored_normed = self.embeddings / norms

        # Cosine similarity
        scores = query_norm @ stored_normed.T

        # Get top-k indices
        k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[-k:][::-1]

        return [
            (self.chunks[i], float(scores[i]), int(i))
            for i in top_indices
        ]

    def store_doc_text(self, filepath: str, text: str):
        self._documents[filepath] = text
        self.docs_file.write_text(json.dumps(self._documents))

    def get_doc_text(self, filepath: str) -> Optional[str]:
        return self._documents.get(filepath)


# ── RAG Engine ──────────────────────────────────────────────────────────


class GardenRAG:
    """Main RAG engine: ingest documents, query, and generate grounded answers."""

    def __init__(
        self,
        store_dir: str = "~/.gardenguide",
        embed_model: str = DEFAULT_EMBED_MODEL,
        gen_model: str = DEFAULT_GEN_MODEL,
    ):
        self.store = VectorStore(store_dir=store_dir)
        self.embed_model = embed_model
        self.gen_model = gen_model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = _get_openai_client()
        return self._client

    def ingest(self, filepath: str) -> Dict:
        """Load, chunk, embed, and store a document.

        Returns metadata dict with counts and duration.
        """
        import time

        t0 = time.time()

        # Load
        text = load_document(filepath)
        source = os.path.abspath(filepath)

        # Remove existing if re-ingesting
        self.store.remove_doc(source)

        # Chunk
        chunks = chunk_text(text)

        # Embed in batches
        all_embeddings = []
        batch_size = 20

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            resp = self.client.embeddings.create(
                model=self.embed_model, input=batch
            )
            batch_embs = np.array([d.embedding for d in resp.data])
            all_embeddings.append(batch_embs)

        embeddings = np.vstack(all_embeddings) if all_embeddings else np.array([])

        # Store
        self.store.add_chunks(chunks, source, embeddings)
        self.store.store_doc_text(source, text)

        elapsed = time.time() - t0

        return {
            "filepath": source,
            "chunks": len(chunks),
            "characters": len(text),
            "elapsed_seconds": round(elapsed, 2),
        }

    def query(self, question: str, top_k: int = DEFAULT_TOP_K) -> List[Tuple[str, float]]:
        """Search for the most relevant chunks for a question.

        Returns list of (chunk_text, similarity_score).
        """
        # Embed the question
        resp = self.client.embeddings.create(
            model=self.embed_model, input=[question]
        )
        q_emb = np.array(resp.data[0].embedding)

        # Search
        results = self.store.search(q_emb, top_k=top_k)
        return [(text, score) for text, score, _ in results]
    
    def list_docs(self) -> List[str]:
        """List ingested documents."""
        return self.store.list_docs()

    def remove_doc(self, filepath: str) -> bool:
        """Remove an ingested document."""
        source = os.path.abspath(filepath)
        return self.store.remove_doc(source)

    def ask(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict:
        """Ask a question and get a RAG-grounded answer.

        Returns dict with answer, sources, and retrieved chunks.
        """
        # Retrieve
        results = self.query(question, top_k=top_k)

        if not results:
            return {
                "answer": "No documents have been ingested yet. "
                         "Use `gardenguide ingest <file>` to add gardening guides first.",
                "sources": [],
                "chunks": [],
            }

        chunks_text = "\n\n".join(
            f"[SOURCE {i+1}] {text}" for i, (text, _) in enumerate(results)
        )
        sources = list(
            dict.fromkeys(
                self.store.doc_sources[self.store.chunks.index(text)]
                if text in self.store.chunks
                else ""
                for text, _ in results
            )
        )
        sources = [s for s in sources if s]

        # Prepare system prompt
        system = system_prompt or (
            "You are a gardening expert assistant. Answer the user's question "
            "based ONLY on the provided context chunks from their own gardening "
            "documents (seed packets, planting guides, garden journals, etc.).\n\n"
            "RULES:\n"
            "- If the context doesn't contain enough information to answer fully, "
            "say so and explain what additional information the user should add.\n"
            "- Cite specific details from the context (dates, temperatures, "
            "variety names, spacing, etc.).\n"
            "- Be practical and actionable — gardeners want to know what to DO.\n"
            "- Keep answers concise but complete."
        )

        user_prompt = (
            f"Using the following context from my gardening documents, "
            f"answer my question.\n\n"
            f"--- CONTEXT ---\n{chunks_text}\n"
            f"--- END CONTEXT ---\n\n"
            f"Question: {question}"
        )

        # Generate
        gen_model = model or self.gen_model
        resp = self.client.chat.completions.create(
            model=gen_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )

        answer = resp.choices[0].message.content

        return {
            "answer": answer,
            "sources": sources,
            "chunks": [text for text, _ in results],
        }

    def clear(self):
        """Remove all ingested documents and data."""
        import shutil

        shutil.rmtree(self.store.store_dir, ignore_errors=True)
        self.store = VectorStore(store_dir=str(self.store.store_dir))