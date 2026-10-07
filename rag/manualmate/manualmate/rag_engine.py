"""RAG engine for ManualMate — ingest docs, ask questions."""

import os
import time
from typing import List, Optional

import openai
from dotenv import load_dotenv

from manualmate.models import Chunk, IngestResult, QueryResult, SearchResult
from manualmate.doc_loader import load_document, chunk_document
from manualmate.vector_store import VectorStore

# Load .env from multiple locations
load_dotenv()
load_dotenv(dotenv_path=".env")
load_dotenv(dotenv_path=os.path.expanduser("~/.manualmate/.env"))


class ManualMateRAG:
    """RAG engine for appliance manual Q&A."""

    DEFAULT_EMBED_MODEL = "text-embedding-3-small"
    DEFAULT_CHAT_MODEL = "gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0.3

    def __init__(
        self,
        store_dir: Optional[str] = None,
        embed_model: str = DEFAULT_EMBED_MODEL,
        chat_model: str = DEFAULT_CHAT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        self.store = VectorStore(store_dir)
        self.embed_model = embed_model
        self.chat_model = chat_model
        self.temperature = temperature

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it in your environment or .env file."
            )
        self.client = openai.OpenAI(api_key=api_key)

    # ─── Embedding ───────────────────────────────────────────────────────

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts via OpenAI API."""
        # Batch in groups of 20
        all_embeddings = []
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self.client.embeddings.create(
                model=self.embed_model,
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in resp.data])
        return all_embeddings

    def _embed_single(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        return self._embed([text])[0]

    # ─── Ingestion ───────────────────────────────────────────────────────

    def ingest(self, filepath: str) -> IngestResult:
        """Load a document, chunk it, embed it, and add to the store."""
        t0 = time.time()

        text, source = load_document(filepath)
        doc_id = f"{source}"

        # Create overlapping chunks
        chunks = chunk_document(text, source=source, doc_id=doc_id)

        if not chunks:
            raise ValueError(f"No chunks could be created from {filepath}")

        # Embed all chunk texts
        chunk_texts = [c.text for c in chunks]
        embeddings = self._embed(chunk_texts)

        import numpy as np
        emb_array = np.array(embeddings, dtype=np.float32)

        # Store
        self.store.add_chunks(chunks, emb_array)
        self.store.store_doc_text(doc_id, text)

        elapsed = time.time() - t0
        return IngestResult(
            filepath=filepath,
            chunks=len(chunks),
            characters=len(text),
            elapsed_seconds=round(elapsed, 2),
        )

    # ─── Query ───────────────────────────────────────────────────────────

    def query(self, question: str, top_k: int = 5) -> List[SearchResult]:
        """Search for the most relevant chunks for a question."""
        if not self.store.chunks:
            return []
        q_emb = self._embed_single(question)
        import numpy as np
        results = self.store.search(np.array(q_emb, dtype=np.float32), top_k=top_k)
        return results

    def ask(self, question: str, top_k: int = 5) -> QueryResult:
        """Ask a question and get a grounded answer with sources."""
        t0 = time.time()

        # Quick empty-check before hitting the API
        if not self.store.chunks:
            return QueryResult(
                answer="No relevant documents found. Please ingest a manual first with: manualmate ingest <file>",
                sources=[],
                chunks=[],
                scores=[],
            )

        # Retrieve relevant chunks
        results = self.query(question, top_k=top_k)
        if not results:
            return QueryResult(
                answer="No relevant documents found. Please ingest a manual first with: manualmate ingest <file>",
                sources=[],
                chunks=[],
                scores=[],
            )

        # Build context from retrieved chunks
        context_parts = []
        source_files = set()
        chunk_texts = []
        scores = []
        for r in results:
            context_parts.append(f"[Source: {r.chunk.source}]\n{r.chunk.text}")
            source_files.add(r.chunk.source)
            chunk_texts.append(r.chunk.text)
            scores.append(round(r.score, 4))

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = (
            "You are a home appliance and device manual assistant. "
            "Answer the user's question based ONLY on the provided document excerpts. "
            "If the answer is not in the provided context, say 'I cannot find this information "
            "in your manuals.' Provide specific details like model numbers, error codes, "
            "and part numbers when available. Keep answers practical and actionable."
        )

        user_prompt = f"""Context from appliance manuals:
---
{context}
---

Question: {question}

Answer based only on the context above:"""

        # Generate answer
        resp = self.client.chat.completions.create(
            model=self.chat_model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        answer = resp.choices[0].message.content.strip()

        return QueryResult(
            answer=answer,
            sources=sorted(list(source_files)),
            chunks=chunk_texts,
            scores=scores,
        )

    # ─── Management ───────────────────────────────────────────────────────

    def list_docs(self) -> List[tuple]:
        """List ingested documents with chunk counts."""
        docs = self.store.list_docs()
        return sorted(docs.items(), key=lambda x: x[1], reverse=True)

    def remove_doc(self, doc_name: str) -> bool:
        """Remove a document by name. Returns True if found and removed."""
        return self.store.remove_doc(doc_name)

    def clear(self) -> None:
        """Remove all stored data."""
        self.store.clear()