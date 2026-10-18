"""Answer generation for TripTome.

Retrieves relevant chunks and either generates an answer via an LLM
or returns the raw context when no API key is available.
"""

import os
from typing import Optional

import httpx

from triptome.embedder import search
from triptome.models import Answer, SearchResult


def _build_context(results: list[SearchResult]) -> str:
    """Build a prompt context string from search results."""
    sections = []
    for i, r in enumerate(results, 1):
        page_info = f" (page {r.page})" if r.page else ""
        sections.append(
            f"[Source {i}: {r.source}{page_info}]\n{r.text}\n")
    return "\n\n".join(sections)


def _generate_with_openai(context: str, query: str,
                          api_key: str, model: str,
                          base_url: str) -> Optional[str]:
    """Call an OpenAI-compatible API to generate an answer."""
    system_prompt = (
        "You are TripTome, a knowledgeable travel assistant. "
        "Answer the user's travel question using ONLY the provided context "
        "from travel guides and documents. If the context doesn't contain "
        "enough information to answer, say so honestly. "
        "Always cite which source(s) you used by referencing [Source N]. "
        "Keep answers concise, practical, and helpful for travelers."
    )

    user_prompt = (
        f"Context from travel documents:\n\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer based on the context above, citing sources:"
    )

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return None


def answer_query(query: str, n_results: int = 5,
                 db_dir: Optional[str] = None) -> Answer:
    """Answer a travel question using the indexed document collection.

    Searches the vector store, retrieves relevant chunks, and
    optionally generates an LLM response if an API key is configured.
    """
    results = search(query, n_results, db_dir)
    if not results:
        return Answer(
            query=query,
            answer=("I don't have any travel documents indexed yet. "
                    "Use 'triptome ingest <path>' to add travel guides first."),
            citations=[],
        )

    source_names = list(dict.fromkeys(r.source for r in results))
    context = _build_context(results)

    # Try to generate an LLM answer
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("TRIPTOME_API_KEY")
    model = os.environ.get("TRIPTOME_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("TRIPTOME_BASE_URL", "https://api.openai.com/v1")

    generated = None
    if api_key:
        generated = _generate_with_openai(context, query, api_key, model, base_url)

    if generated:
        return Answer(
            query=query,
            answer=generated,
            citations=results,
            source_names=source_names,
        )

    # Fallback: show the raw context
    source_list = "\n".join(f"  📖 {s}" for s in source_names)
    return Answer(
        query=query,
        answer=(
            f"I found relevant information in {len(source_names)} travel "
            f"guide(s). Here's what I know:\n\n"
            f"{_build_context(results[:3])}\n\n"
            f"To get AI-generated answers with citations, set the "
            f"OPENAI_API_KEY environment variable (or TRIPTOME_API_KEY)."
        ),
        citations=results,
        source_names=source_names,
    )