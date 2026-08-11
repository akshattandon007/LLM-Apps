"""RAG chain: retrieval + LLM generation with code citations."""

from __future__ import annotations

import os

from src.embedder import Embedder
from src.models import QueryResponse, SourceReference
from src.vector_store import VectorStore

SYSTEM_PROMPT = """You are Code Compass, an expert code analysis assistant. Your job is to answer
questions about a codebase by reading the retrieved code context and providing
accurate, grounded answers.

For each answer:
1. Explain in plain English what the relevant code does
2. Cite exact file paths and line numbers
3. Include relevant code snippets
4. Be specific about function names, class names, and relationships

If the retrieved context doesn't contain enough information to answer the
question, say so honestly. Do not make up code or file references."""


def build_context(sources: list[SourceReference]) -> str:
    """Build a context string from retrieved source references."""
    parts = []
    for i, src in enumerate(sources, 1):
        parts.append(
            f"[Source {i}] {src.file_path} (lines {src.start_line}-{src.end_line}) "
            f"[relevance: {src.relevance_score:.3f}]\n"
            f"```\n{src.snippet}\n```"
        )
    return "\n\n".join(parts)


def generate_answer(
    query: str,
    sources: list[SourceReference],
    model: str | None = None,
) -> str:
    """Generate a grounded answer using Claude via langchain-anthropic."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_answer(query, sources)

    context = build_context(sources)
    prompt = f"Context from the codebase:\n\n{context}\n\n---\n\nQuestion: {query}"

    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(
            model=model or "claude-sonnet-4-20250514",
            temperature=0.1,
            anthropic_api_key=api_key,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"[LLM error: {e}]\n\n{_fallback_answer(query, sources)}"


def _fallback_answer(query: str, sources: list[SourceReference]) -> str:
    """Generate a structured answer without an LLM."""
    if not sources:
        return "No matching code found for your query."

    parts = [f"Found {len(sources)} relevant code sections for: {query}\n"]
    for i, src in enumerate(sources, 1):
        parts.append(
            f"--- Match {i} (relevance: {src.relevance_score:.3f}) ---\n"
            f"File: {src.file_path}\n"
            f"Lines: {src.start_line}-{src.end_line}\n"
            f"```\n{src.snippet[:500]}"
            f"{'...' if len(src.snippet) > 500 else ''}\n```"
        )
    return "\n\n".join(parts)


class RAGChain:
    """End-to-end RAG pipeline: embed query → search → generate answer."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
    ):
        self.embedder = embedder
        self.vector_store = vector_store

    def query(self, query_text: str, top_k: int = 5) -> QueryResponse:
        """Run the full RAG pipeline."""
        query_embedding = self.embedder.embed(query_text)
        sources = self.vector_store.search(query_embedding, top_k=top_k)
        answer = generate_answer(query_text, sources)
        return QueryResponse(answer=answer, sources=sources)
