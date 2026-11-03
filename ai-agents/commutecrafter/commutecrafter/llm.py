"""Optional LLM layer: a one-line 'why this, why now' per item.

Deliberately optional. CommuteCrafter must be useful with zero API keys, so
every call falls back to a deterministic template written from the numbers we
already have. The LLM only adds colour, never correctness.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from .models import Plan, ScheduledItem
from .timing import format_duration

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("COMMUTECRAFTER_LLM_MODEL", "meta-llama/llama-3.3-70b-instruct")

_PACE = [
    (240, "a quick hit"),
    (600, "a solid short read"),
    (1500, "a proper sit-down"),
    (10**9, "the long haul"),
]


def template_reason(sched: ScheduledItem) -> str:
    """Deterministic, honest reason built from numbers we actually measured."""
    minutes = sched.seconds / 60
    pace = next(label for limit, label in _PACE if sched.seconds < limit)
    bits = [f"{pace} at {minutes:.0f} min"]
    if sched.partial:
        bits.append(f"trimmed to {int(sched.fraction * 100)}% ({sched.item.words} words available)")
    else:
        bits.append(f"{sched.item.words} words from {sched.item.source}")
    if sched.item.category in {"deep", "reflective"}:
        bits.append(f"sits well in the {sched.segment}")
    return " · ".join(bits)


def _api_key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")


def explain(sched: ScheduledItem, plan: Plan, timeout: int = 15) -> str:
    """LLM blurb for one item, falling back to the template on any failure."""
    key = _api_key()
    if not key:
        return template_reason(sched)
    prompt = (
        "You are a commute curator. In ONE sentence (max 22 words), say why this "
        "piece suits this exact moment. Be concrete, no fluff.\n\n"
        f"Commute: {plan.minutes:g} minutes, mode={plan.mode}, transport={plan.transport or 'unknown'}.\n"
        f"Segment: {sched.segment}. Slot length: {format_duration(sched.seconds)}.\n"
        f"Item: {sched.item.title} ({sched.item.source}, {sched.item.words} words).\n"
        f"Excerpt: {sched.item.summary[:400]}"
    )
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/akshattandon007/LLM-Apps",
                "X-Title": "CommuteCrafter",
            },
            data=json.dumps(
                {
                    "model": DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 70,
                    "temperature": 0.6,
                }
            ),
            timeout=timeout,
        )
        if resp.status_code >= 400:
            return template_reason(sched)
        payload: dict[str, Any] = resp.json()
        text = (
            payload.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        ).strip()
        text = " ".join(text.split())
        return text or template_reason(sched)
    except Exception:  # noqa: BLE001 - enrichment is optional by design
        return template_reason(sched)


def enrich_plan(plan: Plan, limit: int = 3) -> int:
    """Attach reasons to up to ``limit`` items. Returns how many were set."""
    count = 0
    for sched in plan.scheduled_items:
        if count >= limit:
            break
        sched.reason = explain(sched, plan)
        count += 1
    return count


def apply_template_reasons(plan: Plan) -> None:
    for sched in plan.scheduled_items:
        if not sched.reason:
            sched.reason = template_reason(sched)
