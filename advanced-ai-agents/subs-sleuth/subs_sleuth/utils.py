"""Shared utilities — LLM helper, web search, IMAP connection helpers."""

from __future__ import annotations

import imaplib
import json
import os
import re
import sqlite3
from email import message_from_bytes
from email.header import decode_header
from typing import Optional
from urllib.parse import quote_plus

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

# ---------------------------------------------------------------------------
# LLM helper — wraps a free-tier API (Groq or OpenAI-compatible)
# ---------------------------------------------------------------------------

_LLM_API_KEY: str | None = None
_LLM_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
_LLM_MODEL: str = "llama-3.3-70b-versatile"


def configure_llm(
    api_key: str | None = None,
    api_url: str | None = None,
    model: str | None = None,
) -> None:
    """Set LLM credentials. Pass None to keep existing value."""
    global _LLM_API_KEY, _LLM_API_URL, _LLM_MODEL
    if api_key:
        _LLM_API_KEY = api_key
    if api_url:
        _LLM_API_URL = api_url
    if model:
        _LLM_MODEL = model


def llm_complete(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
) -> str:
    """Call the LLM and return the text response.

    Falls back to rule-based extraction if no API key is configured.
    """
    if not _LLM_API_KEY:
        return _rule_based_extract(user_prompt)

    if httpx is None:
        return _rule_based_extract(user_prompt)

    try:
        resp = httpx.post(
            _LLM_API_URL,
            headers={
                "Authorization": f"Bearer {_LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": _LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return _rule_based_extract(user_prompt)


def _rule_based_extract(text: str) -> str:
    """Fallback when no LLM key: return raw text summarised via heuristics."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # Return first 5 non-empty lines as a summary
    summary = lines[:5]
    return "\n".join(summary) if summary else "(no content extracted)"


# ---------------------------------------------------------------------------
# Web search helper
# ---------------------------------------------------------------------------

def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using a free search API.

    Uses DuckDuckGo-style instant answer if available, otherwise falls
    back to a simulated result.
    """
    results: list[dict] = []

    # Try DuckDuckGo lite (no API key needed)
    try:
        if httpx:
            url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
            resp = httpx.get(url, headers={"User-Agent": "curl/8.0"}, timeout=10)
            if resp.status_code == 200:
                # Parse minimal HTML for result links
                for match in re.finditer(
                    r'<a[^>]*href="(https?://[^"]+)"[^>]*>([^<]+)</a>',
                    resp.text,
                ):
                    results.append({"url": match.group(1), "title": match.group(2).strip()})
                    if len(results) >= max_results:
                        break
    except Exception:
        pass

    if not results:
        # Simulated fallback
        results = [
            {"url": f"https://example.com/cancel-{query[:30].lower().replace(' ', '-')}",
             "title": f"How to cancel {query} subscription"}
        ]

    return results[:max_results]


# ---------------------------------------------------------------------------
# IMAP helpers
# ---------------------------------------------------------------------------

def connect_imap(
    server: str,
    email: str,
    password: str,
) -> imaplib.IMAP4_SSL | None:
    """Connect to an IMAP server and return the connection."""
    try:
        conn = imaplib.IMAP4_SSL(server)
        conn.login(email, password)
        return conn
    except Exception as exc:
        print(f"IMAP connection failed: {exc}")
        return None


def decode_mime_header(value: str | None) -> str:
    """Decode a MIME-encoded header value to plain text."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    return " ".join(
        part.decode(charset or "utf-8") if isinstance(part, bytes) else part
        for part, charset in decoded_parts
    )


def search_subscription_emails(
    conn: imaplib.IMAP4_SSL,
    search_since: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """Search for subscription-related emails in the INBOX.

    Returns list of dicts with subject, date, sender, body snippet.
    """
    keywords = [
        "subscription", "receipt", "invoice", "renewal", "monthly charge",
        "your order", "payment confirmed", "billing", "auto-renew",
        "trial ending", "your plan", "membership", "your statement",
    ]

    results: list[dict] = []

    try:
        conn.select("INBOX")
        for keyword in keywords:
            if len(results) >= limit:
                break
            search_criteria = f'(SUBJECT "{keyword}")'
            if search_since:
                search_criteria = f'(SINCE {search_since} SUBJECT "{keyword}")'

            _status, msg_ids = conn.search(None, search_criteria)
            ids = msg_ids[0].split() if msg_ids[0] else []

            for msg_id in ids[-20:]:  # max 20 per keyword
                _status, msg_data = conn.fetch(msg_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue
                raw_email = msg_data[0][1]
                msg = message_from_bytes(raw_email)

                subject = decode_mime_header(msg.get("Subject", ""))
                date = msg.get("Date", "")
                sender = decode_mime_header(msg.get("From", ""))
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body_text = part.get_payload(decode=True) or b""
                            body_text = body_text.decode("utf-8", errors="replace")[:500]
                            break
                else:
                    body_text = msg.get_payload(decode=True) or b""
                    body_text = body_text.decode("utf-8", errors="replace")[:500]

                results.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                    "subject": subject,
                    "date": date,
                    "sender": sender,
                    "body_snippet": body_text[:200],
                })

    except Exception as exc:
        print(f"IMAP search error: {exc}")

    return results


# ---------------------------------------------------------------------------
# Simple key-value store for persistence
# ---------------------------------------------------------------------------

class SimpleDB:
    """Lightweight SQLite-backed key-value store for subscription data."""

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.commit()

    def put(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value)
        )
        self._conn.commit()

    def get(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM kv WHERE key = ?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()