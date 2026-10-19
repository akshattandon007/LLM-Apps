"""Optional LLM voice layer for ThenPaper, with a template fallback.

If ``ANTHROPIC_API_KEY`` or ``OPENAI_API_KEY`` is present in the environment,
ThenPaper asks a model to write the front-page headline, dek, and
"birthday twins" intro. Without a key — or when the call fails — it falls back
to hand-written templates so the paper always prints, including in tests.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .api import DayFacts

PROMPT_TEMPLATE = """You are the editor of THE THEN PAPER, a playful front page about {month}/{day} in history.
Below are real facts from Wikipedia's On This Day feed for that date.

Write three short pieces of newspaper copy:
1. headline — a punchy front-page headline (max 9 words) about the single most striking fact.
2. dek — one sentence teasing the day.
3. twin_intro — one sentence introducing the "Born This Day" section; call the famous people born that day "birthday twins".

Return ONLY JSON, no commentary:
{{"headline": "...", "dek": "...", "twin_intro": "..."}}

FACTS:
{digest}
"""

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


@dataclass
class Enhancement:
    """LLM-written (or template) front-page copy."""

    headline: str
    dek: str
    twin_intro: str
    used_llm: bool = False


#: Injection point for tests.
_post_json: Optional[Callable[[str, dict, dict], str]] = None


def set_poster(fn: Optional[Callable[[str, dict, dict], str]]) -> None:
    """Override the LLM HTTP layer (tests use this to stay offline)."""
    global _post_json
    _post_json = fn


def _default_post_json(url: str, headers: dict, payload: dict) -> str:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _post(url: str, headers: dict, payload: dict) -> str:
    if _post_json is not None:
        return _post_json(url, headers, payload)
    return _default_post_json(url, headers, payload)


def _has_key() -> Optional[tuple[str, str]]:
    """Return (env_var, provider) when an LLM key exists, else None."""
    for var, provider in (("ANTHROPIC_API_KEY", "anthropic"), ("OPENAI_API_KEY", "openai")):
        if os.environ.get(var):
            return var, provider
    return None


def _digest(facts: DayFacts) -> str:
    lines: list[str] = []
    sections = (
        ("EVENTS", facts.events[:8]),
        ("BIRTHS", facts.births[:6]),
        ("DEATHS", facts.deaths[:3]),
    )
    for label, items in sections:
        if not items:
            continue
        lines.append(f"{label}:")
        for item in items:
            lines.append(f"- {item.year}: {item.text[:140]}")
    holidays = [h.text.replace("\n", " — ")[:80] for h in facts.holidays[:4]]
    if holidays:
        lines.append("HOLIDAYS: " + "; ".join(holidays))
    return "\n".join(lines) or "No facts available."


def _parse_llm_json(text: str) -> dict:
    """Parse the model's reply, tolerating code fences and stray prose."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except ValueError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except ValueError:
            return {}
    return {}


def _ask_llm(facts: DayFacts, month: int, day: int, env_var: str, provider: str) -> Enhancement:
    model = os.environ.get("THENPAPER_MODEL" if provider == "anthropic" else "THENPAPER_OPENAI_MODEL")
    prompt = PROMPT_TEMPLATE.format(month=month, day=day, digest=_digest(facts))
    if provider == "anthropic":
        model = model or "claude-sonnet-4-5"
        headers = {
            "x-api-key": os.environ[env_var],
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }
        raw = _post(ANTHROPIC_URL, headers, payload)
        data = json.loads(raw)
        text = (data.get("content") or [{}])[0].get("text", "")
    else:
        model = model or "gpt-4o-mini"
        headers = {
            "Authorization": f"Bearer {os.environ[env_var]}",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }
        raw = _post(OPENAI_URL, headers, payload)
        data = json.loads(raw)
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    parsed = _parse_llm_json(text)
    headline = str(parsed.get("headline", "")).strip()[:90]
    dek = str(parsed.get("dek", "")).strip()[:240]
    twin_intro = str(parsed.get("twin_intro", "")).strip()[:240]
    if not headline or not dek or not twin_intro:
        raise ValueError("LLM reply missing required fields")
    return Enhancement(headline=headline, dek=dek, twin_intro=twin_intro, used_llm=True)


def enhance(facts: DayFacts, month: int, day: int, allow_llm: bool = True) -> Enhancement:
    """Return front-page copy: LLM voice when possible, templates otherwise."""
    if allow_llm:
        key_info = _has_key()
        if key_info:
            try:
                return _ask_llm(facts, month, day, key_info[0], key_info[1])
            except Exception:
                # Any failure (bad key, unknown model, network) -> templates.
                pass
    return _templates(facts, month, day)


def _templates(facts: DayFacts, month: int, day: int) -> Enhancement:
    selected = facts.selected or []
    events = facts.events or []
    lead = selected[0] if selected else (events[0] if events else None)

    if lead is None:
        headline = f"THE DAY THAT WAS: {month}/{day}"
        dek = "Nothing on file. Even history takes a day off."
        twin_intro = "The archives are quiet on births today."
    else:
        snippet = lead.text[:52].rstrip().upper()
        headline = f"{lead.year}: {snippet}" if lead.year else snippet
        dek = (
            f"A front page for {month}/{day} — straight from the archive of "
            "everything that ever happened."
        )
        births = sorted(facts.births, key=lambda b: b.year, reverse=True)
        if births:
            twin_intro = f"Your birthday twins include {births[0].text[:70]}."
        else:
            twin_intro = "The archives are quiet on births today."
    return Enhancement(headline=headline, dek=dek, twin_intro=twin_intro, used_llm=False)