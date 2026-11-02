"""LLM query interface — turns retrieved chunks into grounded answers."""

from __future__ import annotations

import os
from typing import Any

import httpx
from openai import OpenAI

from .models import SearchHit

DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
OPENROUTER_BASE = "https://nexos.ai"


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    base_url = os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE)
    return OpenAI(api_key=api_key, base_url=base_url)


def query_papers(
    question: str,
    hits: list[SearchHit],
    model: str = DEFAULT_MODEL,
) -> str:
    """Ask a question with retrieved context chunks and get a grounded answer.

    Args:
        question: User's natural language question.
        hits: Retrieved context chunks from the index.
        model: Model to use via OpenRouter.

    Returns:
        Generated answer text.
    """
    if not hits:
        return "No relevant papers found. Try indexing more papers first."

    # Build context block
    context_parts: list[str] = []
    for i, hit in enumerate(hits, 1):
        context_parts.append(
            f"[{i}] From: \"{hit.chunk.title}\" (arXiv:{hit.chunk.paper_id})\n{hit.chunk.text}"
        )

    context = "\n\n".join(context_parts)

    system_prompt = (
        "You are a research assistant helping a user understand academic papers. "
        "Answer the user's question based ONLY on the provided context. "
        "Cite the source papers by their [N] numbers. "
        "If the context doesn't contain enough information, say so clearly."
    )

    user_prompt = f"""Context from research papers:
{context}

---

Question: {question}

Answer the question using the context above. Cite sources as [1], [2], etc."""

    client = _get_client()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"Error querying LLM: {e}"


def summarize_papers(
    papers: list[Any],
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a summary of a list of papers.

    Args:
        papers: List of ArxivPaper objects (or dicts with title/abstract).
        model: Model to use.

    Returns:
        Summary text.
    """
    if not papers:
        return "No papers to summarize."

    paper_texts: list[str] = []
    for i, p in enumerate(papers, 1):
        title = getattr(p, "title", p.get("title", "Untitled"))
        abstract = getattr(p, "abstract", p.get("abstract", ""))
        paper_texts.append(f"[{i}] {title}\n{abstract}")

    context = "\n\n".join(paper_texts)

    system_prompt = (
        "You are a research assistant. Summarize the following papers "
        "in a clear, structured way. Group related work and note unique contributions."
    )

    client = _get_client()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Papers:\n\n{context}\n\nProvide a structured summary of these papers."},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        return f"Error summarizing: {e}"