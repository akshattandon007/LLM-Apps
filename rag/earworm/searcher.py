"""Earworm — search and LLM-powered answer synthesis."""

import os
import requests
from sentence_transformers import SentenceTransformer
from models import get_db, get_chunks_by_ids


OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYNTHESIS_PROMPT = """You are Earworm, a helpful podcast search assistant. Based on the following podcast transcript excerpts, answer the user's question with citations.

Rules:
- Synthesize a concise, direct answer using information from the excerpts.
- For each claim, cite which show, episode, and position in the transcript it comes from (use the [Show: ..., Episode: ..., Position: char ~N] notation from each excerpt).
- If the excerpts do not contain enough information to answer, say so honestly.
- Do not make up information that is not in the excerpts.

Podcast excerpts:
{excerpts}

User question: {question}

Answer:"""


def format_excerpt(chunk_row) -> str:
    """Format a chunk DB row into a readable excerpt block."""
    show = chunk_row["show_name"]
    episode = chunk_row["episode_title"]
    date = chunk_row["pub_date"] or "unknown date"
    start = chunk_row["start_char"] or 0
    text = chunk_row["text"]
    return (
        f"[Show: {show} | Episode: {episode} | Date: {date} | Position: char ~{start}]\n"
        f"{text}\n"
    )


def search_chunks(
    query: str,
    model: SentenceTransformer,
    index,
    id_map: dict,
    top_k: int = 10,
) -> list:
    """Search and return full chunk rows with metadata."""
    from embedder import search as faiss_search

    results = faiss_search(query, model, index, id_map, top_k=top_k)
    if not results:
        return []

    chunk_ids = [cid for cid, _ in results]
    conn = get_db()
    rows = get_chunks_by_ids(conn, chunk_ids)

    # Preserve FAISS ranking order
    score_map = dict(results)
    rows_dict = {row["id"]: row for row in rows}
    ordered = []
    for cid in chunk_ids:
        if cid in rows_dict:
            ordered.append((rows_dict[cid], score_map[cid]))

    return ordered


def synthesize_answer(
    query: str,
    chunks: list,
    model_name: str = "openai/gpt-4o-mini",
) -> str | None:
    """Use an LLM via OpenRouter to synthesize an answer from retrieved chunks.

    Returns the answer string, or None if no API key is configured.
    """
    if not OPENROUTER_API_KEY:
        return None

    excerpts = "\n---\n".join(format_excerpt(chunk_row) for chunk_row, _ in chunks)
    prompt = SYNTHESIS_PROMPT.format(excerpts=excerpts, question=query)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"(LLM synthesis failed: {e})"