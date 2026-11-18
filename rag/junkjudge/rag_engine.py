"""
rag_engine.py — Embed documents, search by similarity, and answer via LLM.

Architecture:
    1. On startup, load a sentence-transformer model for embeddings.
    2. Build a FAISS index from document chunks.
    3. On query, embed the question, retrieve top-k chunks.
    4. Send context + question to a free LLM (HuggingFace Inference API)
       and return a plain-English answer.

Public API:
    RAGEngine(chunks: list[dict], model_name: str = ...)
        .query(question: str, top_k: int = 5) -> dict
            Returns {"answer": str, "sources": [{"text": str, "source": str, "page": int}, ...]}
"""

import os
import json
import urllib.request
import urllib.error
from typing import Any

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore


HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_MODEL = os.environ.get(
    "HF_QA_MODEL",
    "mistralai/Mistral-7B-Instruct-v0.3",
)

QA_SYSTEM_PROMPT = (
    "You are JunkJudge, a recycling rules assistant. "
    "Answer the user's question ONLY based on the provided context. "
    "If the context does not contain the answer, say 'I could not find that in your guidelines.' "
    "Be specific — quote the relevant rule if possible. "
    "Keep answers concise (2-4 sentences)."
)


class RAGEngine:
    """Retrieval-Augmented Generation engine for JunkJudge."""

    def __init__(
        self,
        chunks: list[dict],
        model_name: str = "all-MiniLM-L6-v2",
    ):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required")
        if faiss is None:
            raise ImportError("faiss is required")

        self.chunks = chunks
        self.model = SentenceTransformer(model_name)
        self._build_index()

    # ── Index building ──────────────────────────────────────────────

    def _build_index(self) -> None:
        """Embed all chunks and build a FAISS index."""
        if not self.chunks:
            self.index = faiss.IndexFlatL2(0)
            return

        texts = [c["text"] for c in self.chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)

    # ── Retrieval ───────────────────────────────────────────────────

    def retrieve(self, question: str, top_k: int = 5) -> list[dict]:
        """Return top-k chunks relevant to *question*."""
        if not self.chunks or self.index.ntotal == 0:
            return []

        q_emb = self.model.encode([question], show_progress_bar=False)
        q_emb = np.array(q_emb).astype("float32")

        distances, indices = self.index.search(q_emb, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            results.append({
                "text": self.chunks[idx]["text"],
                "source": self.chunks[idx]["source"],
                "page": self.chunks[idx]["page"],
                "score": float(dist),
            })
        return results

    # ── Answer generation ───────────────────────────────────────────

    def _build_prompt(self, question: str, context: list[dict]) -> str:
        ctx_text = "\n\n".join(
            f"[From {c['source']}, page {c['page']}]:\n{c['text']}"
            for c in context
        )
        prompt = (
            f"{QA_SYSTEM_PROMPT}\n\n"
            f"--- CONTEXT ---\n{ctx_text}\n\n"
            f"--- QUESTION ---\n{question}\n\n"
            f"--- ANSWER ---"
        )
        return prompt

    def _call_hf_inference(self, prompt: str) -> str:
        """Call HuggingFace free Inference API."""
        api_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        headers = {"Content-Type": "application/json"}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.2,
                "do_sample": True,
            },
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            return f"[API error {e.code}] {body[:300]}"
        except Exception as e:
            return f"[Error] {e}"

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", str(result))
        return str(result)

    def query(self, question: str, top_k: int = 5) -> dict[str, Any]:
        """Full RAG pipeline: retrieve → generate → return."""
        retrieved = self.retrieve(question, top_k=top_k)

        if not retrieved:
            return {
                "answer": "No documents loaded. Upload your municipal recycling guidelines first.",
                "sources": [],
            }

        prompt = self._build_prompt(question, retrieved)
        answer = self._call_hf_inference(prompt)

        # The API returns the full prompt + answer; strip the prompt part
        if "--- ANSWER ---" in answer:
            answer = answer.split("--- ANSWER ---", 1)[-1].strip()

        return {
            "answer": answer,
            "sources": [
                {"text": c["text"], "source": c["source"], "page": c["page"]}
                for c in retrieved
            ],
        }