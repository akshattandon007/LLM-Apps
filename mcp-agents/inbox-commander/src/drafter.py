"""Tone-aware reply drafting with Claude (with deterministic fallback).

Supported tones: professional (default), friendly, concise, assertive.
With ANTHROPIC_API_KEY set, Claude writes the reply. Without a key, a
tone-aware template keeps the tool functional for tests and demo mode.
"""

from __future__ import annotations

import os
from email.utils import parseaddr
from typing import Any, Dict

TONES: Dict[str, str] = {
    "professional": "professional, courteous, and direct; business-appropriate language.",
    "friendly": "warm and personable but still clear; conversational without being sloppy.",
    "concise": "minimal words; get to the point in 1-3 short sentences.",
    "assertive": "confident and firm; sets boundaries clearly without being rude.",
}

DRAFT_SYSTEM = (
    "You draft email replies in the user's voice: clear, direct, and human. "
    "Reply only to what the thread requires. Never invent facts, numbers, or "
    "commitments. Do not include a subject line. End with a sign-off such as "
    "'Best regards' followed by the placeholder [Your Name]."
)

MAX_MESSAGE_CHARS = 1500

FALLBACK_OPENERS = {
    "professional": 'Hi {name},\n\nThanks for your email regarding "{subject}".\n\n',
    "friendly": 'Hi {name},\n\nThanks for reaching out about "{subject}"!\n\n',
    "concise": 'Hi {name}, re: "{subject}" —\n\n',
    "assertive": 'Hi {name},\n\nRegarding "{subject}":\n\n',
}

FALLBACK_CLOSERS = {
    "professional": "Best regards,\n[Your Name]",
    "friendly": "Cheers,\n[Your Name]",
    "concise": "— [Your Name]",
    "assertive": "Best,\n[Your Name]",
}


def _get_llm():
    """Return a ChatAnthropic instance, or None when not configured/available."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            temperature=0.4,
            api_key=api_key,
        )
    except Exception:
        return None


def _build_prompt(thread: Dict[str, Any], tone: str) -> str:
    lines = [f"Thread subject: {thread.get('subject', '(no subject)')}", ""]
    for msg in thread.get("messages", []):
        body = (msg.get("body") or "").strip()[:MAX_MESSAGE_CHARS]
        lines.append(
            f"--- Message from {msg.get('sender', '?')} on {msg.get('date', '?')} ---\n"
            f"{body or msg.get('snippet', '')}"
        )
    lines.append("")
    lines.append(
        f"Draft a reply to this thread with tone: {TONES.get(tone, TONES['professional'])}"
    )
    lines.append("Draft the reply now.")
    return "\n".join(lines)


def draft_reply(thread: Dict[str, Any], tone: str = "professional") -> str:
    """Draft a reply to the thread in the requested tone."""
    tone = tone.lower() if tone else "professional"
    if tone not in TONES:
        tone = "professional"

    llm = _get_llm()
    if llm is None:
        return _fallback_draft(thread, tone)

    try:
        response = llm.invoke(
            [
                {"role": "system", "content": DRAFT_SYSTEM},
                {"role": "user", "content": _build_prompt(thread, tone)},
            ]
        )
        return str(response.content).strip()
    except Exception as exc:  # never fail a draft because the LLM is down
        return (
            f"{_fallback_draft(thread, tone)}\n\n"
            f"[AI draft unavailable: {exc}]"
        )


def _fallback_draft(thread: Dict[str, Any], tone: str) -> str:
    messages = thread.get("messages", [])
    first = messages[0] if messages else {}
    sender = first.get("sender", "")
    _, addr = parseaddr(sender)
    name = addr.split("@")[0] if addr else "there"
    subject = thread.get("subject") or first.get("subject") or "your email"

    opener = FALLBACK_OPENERS.get(tone, FALLBACK_OPENERS["professional"]).format(
        name=name, subject=subject
    )
    closer = FALLBACK_CLOSERS.get(tone, FALLBACK_CLOSERS["professional"])
    return (
        opener
        + "[Reply drafted by Inbox Commander's fallback template — set "
        "ANTHROPIC_API_KEY for AI-written drafts.]\n\n"
        + closer
    )
