"""Generate plain-language answers from retrieved drug label chunks.

Supports multiple backends:
  1. HuggingFace Inference API (free, limited rate)
  2. Local transformers pipeline (requires model download)
  3. Fallback: formatted retrieval output without an LLM
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional

# Default free model on HuggingFace Inference API
HF_DEFAULT_MODEL = "microsoft/Phi-3-mini-4k-instruct"
HF_API_URL = "https://api-inference.huggingface.co/models/{model}"


def _format_context(results: list[dict]) -> str:
    """Format retrieval results into a context string for the LLM."""
    sections = []
    for i, r in enumerate(results, 1):
        sections.append(
            f"[{i}] {r['source']}\n"
            f"   {r['text'][:800]}"
        )
    return "\n\n".join(sections)


def _build_prompt(query: str, context: str) -> str:
    """Build an instruction-tuned prompt for medication information."""
    return (
        "<|system|>\n"
        "You are PillWise, a helpful medication information assistant. "
        "Answer the user's question based ONLY on the provided FDA drug label "
        "information. Be clear, accurate, and mention the drug name. "
        "If the information doesn't answer the question, say so. "
        "Include citations like [1], [2] referencing the sources.\n"
        "<|user|>\n"
        "Context from FDA drug labels:\n\n"
        f"{context}\n\n"
        f"Question: {query}\n"
        "<|assistant|>\n"
    )


def generate_with_huggingface(
    query: str,
    results: list[dict],
    model: str = HF_DEFAULT_MODEL,
    hf_token: Optional[str] = None,
    max_new_tokens: int = 512,
) -> str:
    """Generate answer using HuggingFace Inference API (free tier)."""
    context = _format_context(results)
    prompt = _build_prompt(query, context)

    headers = {"Content-Type": "application/json"}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": 0.3,
            "do_sample": True,
            "return_full_text": False,
        },
    }

    url = HF_API_URL.format(model=model)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("generated_text", "").strip()
            elif isinstance(data, dict) and "error" in data:
                return f"[API Error: {data['error']}]"
            return str(data).strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"[HTTP {e.code}: {body[:200]}]"
    except Exception as e:
        return f"[Generation Error: {e}]"


def generate_retrieval_only(query: str, results: list[dict]) -> str:
    """Fallback: format retrieval results directly without an LLM."""
    lines = [
        f"📋 **PillWise — Medication Information for: {query}**\n",
        f"Found {len(results)} relevant sections from FDA drug labels:\n",
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"\n--- [{i}] {r['source']} (relevance: {r['score']:.3f}) ---")
        lines.append(r["text"][:1000])
    lines.append(
        "\n\n⚠️ *To get an AI-generated summary in plain language, "
        "set the HUGGINGFACE_TOKEN environment variable or configure "
        "a different LLM backend.*"
    )
    return "\n".join(lines)


def generate(
    query: str,
    results: list[dict],
    hf_token: Optional[str] = None,
    use_local: bool = False,
) -> str:
    """Generate a plain-language answer from retrieved drug label chunks.

    Priority:
    1. If HF token available: use HuggingFace Inference API
    2. If use_local=True: attempt local transformers pipeline
    3. Fallback: formatted retrieval output
    """
    token = hf_token or os.environ.get("HUGGINGFACE_TOKEN")

    if token:
        return generate_with_huggingface(query, results, hf_token=token)
    elif use_local:
        return "[Local model generation not available in this build. Install transformers and use `pillwise --local`]"
    else:
        return generate_retrieval_only(query, results)
