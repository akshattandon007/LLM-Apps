"""MCP tool surface for Inbox Commander.

Tools are plain functions (easy to unit-test) that get registered on a FastMCP
server by `register()`. The Gmail client is a module-level singleton that tests
can replace with a fake.

SEND GATE: send_draft is a no-go without a one-time approval token produced by
approve_send for the exact thread_id + body. Nothing is ever sent on a bare
send_draft call — the user must have approved first.
"""

from __future__ import annotations

import secrets
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

from . import drafter, gmail_client, summarizer
from .models import Approval, SendResult

GATE_ERROR = (
    "SEND GATED: no valid approval for this email. Call approve_send(thread_id, "
    "body) with the exact body first, then pass the returned approval_token to "
    "send_draft. Nothing was sent."
)

# token -> {"thread_id": str, "body": str}
_APPROVALS: Dict[str, Dict[str, str]] = {}

_client: Optional[gmail_client.GmailClient] = None


def get_client() -> gmail_client.GmailClient:
    """Lazily build (or reuse) the Gmail client. Tests replace `tools._client`."""
    global _client
    if _client is None:
        _client = gmail_client.GmailClient()
    return _client


# ------------------------------------------------------------------ tools


def search_threads(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search Gmail threads by query and return lightweight summaries.

    query: Gmail search syntax (e.g. 'from:vendor from:example.com is:unread').
    """
    return get_client().search_threads(query, max_results)


def read_thread(thread_id: str) -> Dict[str, Any]:
    """Return the full thread with all messages (sender, recipient, subject,
    date, snippet, and extracted body)."""
    return get_client().read_thread(thread_id)


def summarize_thread(thread_id: str) -> str:
    """Return an AI summary of the thread: what it is about, decisions, action
    items. Falls back to an extractive summary when no LLM key is configured."""
    thread = get_client().read_thread(thread_id)
    return summarizer.summarize_thread(thread)


def draft_reply(thread_id: str, tone: str = "professional") -> Dict[str, Any]:
    """Draft a reply to the thread in the user's voice.

    tone: professional (default), friendly, concise, or assertive.
    Returns {"thread_id", "tone", "body"}. The body is a draft — nothing is
    sent until the user approves and send_draft is called.
    """
    thread = get_client().read_thread(thread_id)
    body = drafter.draft_reply(thread, tone=tone)
    return {"thread_id": thread_id, "tone": tone, "body": body}


def approve_send(thread_id: str, body: str) -> Dict[str, Any]:
    """Explicitly approve sending `body` on `thread_id`.

    Returns a one-time approval_token. Call this only after the user has seen
    and approved the exact draft. Pass the token to send_draft to send.
    """
    token = secrets.token_urlsafe(16)
    _APPROVALS[token] = {"thread_id": thread_id, "body": body}
    return Approval(
        thread_id=thread_id, approval_token=token
    ).model_dump()


def send_draft(thread_id: str, body: str, approval_token: str) -> Dict[str, Any]:
    """SEND the drafted email. GATED: requires an approval_token from
    approve_send that matches thread_id AND body. The token is single-use.

    Raises ValueError when there is no matching approval — nothing is sent.
    """
    record = _APPROVALS.pop(approval_token, None)
    if (
        record is None
        or record["thread_id"] != thread_id
        or record["body"] != body
    ):
        raise ValueError(GATE_ERROR)

    thread = get_client().read_thread(thread_id)
    subject = thread.get("subject", "")
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    messages = thread.get("messages", [])
    sender = messages[0].get("sender", "") if messages else ""
    to = parseaddr(sender)[1] or sender

    result = get_client().send_message(
        thread_id=thread_id, body=body, subject=subject, to=to
    )
    return SendResult(
        status="sent",
        message_id=result.get("message_id", ""),
        thread_id=thread_id,
    ).model_dump()


def label_thread(thread_id: str, label: str) -> Dict[str, Any]:
    """Apply a Gmail label to the thread (creates the label if it is missing)."""
    return get_client().label_thread(thread_id, label)


def archive_thread(thread_id: str) -> Dict[str, Any]:
    """Archive the thread (remove it from INBOX) to move toward inbox zero."""
    return get_client().archive_thread(thread_id)


# ------------------------------------------------------------------ wiring


def register(mcp) -> None:
    """Register every tool on a FastMCP server instance."""
    mcp.tool()(search_threads)
    mcp.tool()(read_thread)
    mcp.tool()(summarize_thread)
    mcp.tool()(draft_reply)
    mcp.tool()(approve_send)
    mcp.tool()(send_draft)
    mcp.tool()(label_thread)
    mcp.tool()(archive_thread)
