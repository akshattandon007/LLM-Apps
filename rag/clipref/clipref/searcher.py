"""ClipRef — searcher: query embedding, retrieval, and optional LLM answer generation."""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from clipref import utils
from clipref.models import SearchResult, Answer


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def search(
    query: str,
    db_path: Path,
    model,
    top_k: int = 5,
) -> list[SearchResult]:
    """Search the indexed clips and return ranked results.

    Args:
        query: Natural language query string.
        db_path: Path to the ChromaDB database directory.
        model: SentenceTransformer model for embedding the query.
        top_k: Number of results to return.

    Returns:
        List of SearchResult objects, sorted by relevance (highest first).
    """
    if not db_path.exists():
        return []

    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    try:
        collection = client.get_collection(utils.collection_name())
    except (ValueError, chromadb.errors.NotFoundError):
        print("No index found. Run 'clipref index <directory>' first.")
        return []

    # Embed the query
    query_vector = model.encode([query]).tolist()

    # Query ChromaDB
    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Parse results
    search_results: list[SearchResult] = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return search_results

    for i in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][i]
        doc = (results["documents"][0][i] if results.get("documents") else "")
        meta = (results["metadatas"][0][i] if results.get("metadatas") else {})
        distance = (results["distances"][0][i] if results.get("distances") else 0.0)
        # ChromaDB returns L2 distance by default; convert to similarity score
        score = max(0.0, 1.0 - distance / 2.0)

        search_results.append(SearchResult(
            chunk_id=chunk_id,
            text=doc,
            source_file=meta.get("source_file", "unknown"),
            source_path=meta.get("source_path", "unknown"),
            score=score,
        ))

    return search_results


# ---------------------------------------------------------------------------
# LLM answer generation
# ---------------------------------------------------------------------------


def generate_answer(
    question: str,
    search_results: list[SearchResult],
    llm_model: str | None = None,
    system_prompt: str | None = None,
) -> Answer | None:
    """Generate an AI answer grounded in search results.

    Args:
        question: The user's original question.
        search_results: Results from ``search()``.
        llm_model: Model name for the LLM API.
        system_prompt: Custom system prompt. A sensible default is used if None.

    Returns:
        Answer object, or None if the API key is missing or the call fails.
    """
    if not search_results:
        return None

    api_key = utils.llm_api_key()
    if not api_key:
        print("No API key found. Use search mode or set OPENAI_API_KEY.")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI library not available. Install with: pip install openai")
        return None

    # Prepare context from search results
    context_parts = []
    for i, r in enumerate(search_results, 1):
        context_parts.append(f"[Source {i}] {r.source_path}\n{r.text}")
    context = "\n\n".join(context_parts)

    # Build messages
    if system_prompt is None:
        system_prompt = (
            "You are a helpful research assistant. Answer the user's question "
            "based ONLY on the provided context (sources). If the context doesn't "
            "contain enough information to answer, say so. Always cite the source "
            "number(s) you used, like [Source 1]."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    model = llm_model or utils.llm_model()
    base_url = utils.llm_base_url()

    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        answer_text = response.choices[0].message.content
    except Exception as e:
        return Answer(
            text=f"Failed to generate answer: {e}",
            sources=search_results,
            model=model,
        )

    return Answer(
        text=answer_text,
        sources=search_results,
        model=model,
    )