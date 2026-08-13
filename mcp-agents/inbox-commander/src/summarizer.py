"""Thread summarization with Claude (with deterministic fallback).

When ANTHROPIC_API_KEY is set, threads are summarized by Claude via
langchain-anthropic. Without a key (or if the call fails), a deterministic
extractive fallback keeps the tools usable for tests and demo mode.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

SUMMARY_SYSTEM = (
    "You are an executive assistant summarizing email threads. Be concise: "
    "3-5 short bullets max. Cover: what the thread is about, any decisions made, "
    "and action items with owners. Never invent facts not present in the thread."
)

MAX_MESSAGE_CHARS = 1500


def _get_llm():
    """Return a ChatAnthropic instance, or None when not configured/available."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            temperature=0.2,
            api_key=api_key,
        )
    except Exception:
        return None


def _build_prompt(thread: Dict[str, Any]) -> str:
    lines = [f"Thread subject: {thread.get('subject', '(no subject)')}", ""]
    for msg in thread.get("messages", []):
        body = (msg.get("body") or "").strip()[:MAX_MESSAGE_CHARS]
        lines.append(
            f"--- Message from {msg.get('sender', '?')} on {msg.get('date', '?')} ---\n"
            f"{body or msg.get('snippet', '')}"
        )
    lines.append("")
    lines.append("Summarize this thread.")
    return "\n".join(lines)


def summarize_thread(thread: Dict[str, Any]) -> str:
    """Return a concise summary of a thread dict (from GmailClient.read_thread)."""
    llm = _get_llm()
    if llm is None:
        return _fallback_summary(thread)
    try:
        response = llm.invoke(
            [
                {"role": "system", "content": SUMMARY_SYSTEM},
                {"role": "user", "content": _build_prompt(thread)},
            ]
        )
        return str(response.content).strip()
    except Exception as exc:  # never fail a read because the LLM is down
        return f"{_fallback_summary(thread)}\n\n[AI summary unavailable: {exc}]"


def _fallback_summary(thread: Dict[str, Any]) -> str:
    messages = thread.get("messages", [])
    first = messages[0] if messages else {}
    latest = messages[-1] if messages else {}
    return "\n".join(
        [
            f"Subject: {thread.get('subject') or first.get('subject') or '(no subject)'}",
            f"From: {first.get('sender', '')}",
            f"Messages: {len(messages)}",
            f"Latest snippet: {latest.get('snippet', '') if messages else ''}",
        ]
    )
