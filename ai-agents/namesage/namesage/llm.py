"""LLM module — synthesizes a name profile via OpenRouter."""

import json
import os
from typing import Any

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "gryphe/mythomax-l2-13b"
TIMEOUT = 30.0


def _build_prompt(
    name: str,
    age_data: dict[str, Any],
    gender_data: dict[str, Any],
    nationality_data: dict[str, Any],
    rhymes: list[dict[str, Any]],
) -> str:
    """Build the system + user prompt for the LLM."""
    age_str = json.dumps(age_data, indent=2)
    gender_str = json.dumps(gender_data, indent=2)
    nat_str = json.dumps(nationality_data, indent=2)
    rhyme_words = [r.get("word", "") for r in rhymes if "word" in r]
    rhymes_str = ", ".join(rhyme_words[:10]) if rhyme_words else "(none found)"

    return f"""You are a name-analytics expert. Given data about the name "{name}", write a concise,
engaging profile (3-5 paragraphs) covering:

1. **Era vibes** — what decade(s) the name feels like and why
2. **Famous namesakes** — 2-3 well-known people who share this name
3. **Cultural associations** — any cultural, literary, or historical associations
4. **Sibling-name suggestions** — 3-5 names that share a similar vibe
5. **Wordplay** — a short pun or phrase using one of the rhyming words: {rhymes_str}

**Data:**
- Age prediction: {age_str}
- Gender probability: {gender_str}
- Country probabilities: {nat_str}

Keep the tone warm, clever, and informative. Use markdown for section headings.
"""


async def generate_profile(
    name: str,
    age_data: dict[str, Any],
    gender_data: dict[str, Any],
    nationality_data: dict[str, Any],
    rhymes: list[dict[str, Any]],
) -> str:
    """Generate a name profile via OpenRouter.

    Returns the LLM response text, or an error message if the call fails.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return (
            "⚠️  No OPENROUTER_API_KEY set. Set it in your environment to get "
            "LLM-generated profiles. Falling back to raw data display."
        )

    prompt = _build_prompt(name, age_data, gender_data, nationality_data, rhymes)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return "⚠️  LLM returned no content."
    except httpx.HTTPError as exc:
        return f"⚠️  LLM request failed: {exc}"