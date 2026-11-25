"""LLM helper — single interface for calling any OpenAI-compatible API."""

import os
import json
import sys

OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("ABACUS_MODEL", "gpt-4o-mini")


def llm_call(system_prompt: str, user_prompt: str, temperature: float = 0.3,
             max_tokens: int = 1024, json_mode: bool = False) -> str:
    """Make an LLM API call returning the text content."""
    if not OPENAI_KEY:
        # No key configured — return a structured fallback for demo/testing
        return _fallback_response(system_prompt, user_prompt)

    import urllib.request

    url = f"{OPENAI_BASE}/chat/completions"
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read().decode())
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [LLM call failed: {e}]", file=sys.stderr)
        return _fallback_response(system_prompt, user_prompt)


def _fallback_response(system_prompt: str, user_prompt: str) -> str:
    """Deterministic fallback when no LLM API key is available."""
    if "categorize" in system_prompt.lower():
        return json.dumps({"category": "other", "confidence": "medium",
                           "reasoning": "Fallback — no LLM key configured"})
    if "analyze" in system_prompt.lower() and "spend" in user_prompt.lower():
        return json.dumps({
            "potential_savings_monthly": 0.0,
            "top_saving_opportunity": "Review discretionary subscriptions",
            "suggestions": ["Track spending for 30 days", "Cut non-essential subscriptions"],
            "essential_total": 0.0,
            "discretionary_total": 0.0,
        })
    if "summary" in system_prompt.lower():
        return ("Summary generated in fallback mode (no API key). "
                "Run with OPENAI_API_KEY set for LLM-powered insights.")
    if "refine" in system_prompt.lower():
        return "Scenario refined in fallback mode. Provide OPENAI_API_KEY for deeper analysis."
    return ("Analysis completed in fallback mode. "
            "Set OPENAI_API_KEY for LLM-powered financial insights.")