"""Thin Gmail API wrapper: search, read, send, label, archive.

All methods return plain dicts so the MCP layer stays free of googleapiclient
types and tests can swap in a fake client.
"""

from __future__ import annotations

import base64
import html as html_lib
import re
from email.message import EmailMessage
from typing import Any, Dict, List

from googleapiclient.discovery import build

from . import auth


def _headers_of(message: Dict[str, Any]) -> Dict[str, str]:
    payload = message.get("payload", {})
    return {h.get("name", ""): h.get("value", "") for h in payload.get("headers", [])}


def _decode(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode("utf-8", "replace")


def _strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    return html_lib.unescape(re.sub(r"\s+", " ", text)).strip()


def _extract_body(payload: Dict[str, Any]) -> str:
    """Best-effort body extraction: prefer text/plain, fall back to stripped HTML."""
    body = payload.get("body", {})
    if payload.get("mimeType") == "text/plain" and body.get("data"):
        return _decode(body["data"])
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            return _strip_html(_decode(part["body"]["data"]))
    return ""


class GmailClient:
    """Wraps the Gmail API v1 service."""

    def __init__(self, credentials=None):
        self.credentials = credentials or auth.get_credentials()
        self.service = build("gmail", "v1", credentials=self.credentials)

    # ------------------------------------------------------------------ read

    def search_threads(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        resp = (
            self.service.users()
            .threads()
            .list(userId="me", q=query or "", maxResults=max_results)
            .execute()
        )
        results: List[Dict[str, Any]] = []
        for t in resp.get("threads", []):
            detail = (
                self.service.users()
                .threads()
                .get(
                    id=t["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            messages = detail.get("messages", [])
            headers = _headers_of(messages[0]) if messages else {}
            results.append(
                {
                    "thread_id": detail["id"],
                    "subject": headers.get("Subject", ""),
                    "sender": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": detail.get("snippet", ""),
                    "message_count": len(messages),
                }
            )
        return results

    def read_thread(self, thread_id: str) -> Dict[str, Any]:
        detail = (
            self.service.users().threads().get(id=thread_id, format="full").execute()
        )
        messages: List[Dict[str, Any]] = []
        subject = ""
        for m in detail.get("messages", []):
            headers = _headers_of(m)
            msg_subject = headers.get("Subject", "")
            if not subject and msg_subject:
                subject = msg_subject
            messages.append(
                {
                    "id": m["id"],
                    "thread_id": detail["id"],
                    "sender": headers.get("From", ""),
                    "recipient": headers.get("To", ""),
                    "subject": msg_subject,
                    "date": headers.get("Date", ""),
                    "snippet": m.get("snippet", ""),
                    "body": _extract_body(m.get("payload", {})),
                }
            )
        return {"thread_id": detail["id"], "subject": subject, "messages": messages}

    # ------------------------------------------------------------------ send

    def send_message(
        self, thread_id: str, body: str, subject: str, to: str
    ) -> Dict[str, Any]:
        """Send a reply on an existing thread (keeps threading intact)."""
        detail = (
            self.service.users()
            .threads()
            .get(
                id=thread_id,
                format="metadata",
                metadataHeaders=["Message-ID", "References"],
            )
            .execute()
        )
        first = detail.get("messages", [{}])[0]
        headers = _headers_of(first)
        message_id = headers.get("Message-ID", "")

        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        if message_id:
            msg["In-Reply-To"] = message_id
            msg["References"] = (headers.get("References", "") or message_id) + (
                f" {message_id}" if headers.get("References") else ""
            )
        msg.set_content(body)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        res = (
            self.service.users()
            .messages()
            .send(userId="me", body={"raw": raw, "threadId": thread_id})
            .execute()
        )
        return {"message_id": res.get("id", ""), "thread_id": thread_id}

    # ----------------------------------------------------------- label/archive

    def label_thread(self, thread_id: str, label: str) -> Dict[str, Any]:
        label_id = self._resolve_label(label)
        self.service.users().threads().modify(
            id=thread_id, body={"addLabelIds": [label_id]}
        ).execute()
        return {"status": "labeled", "thread_id": thread_id, "label": label}

    def archive_thread(self, thread_id: str) -> Dict[str, Any]:
        self.service.users().threads().modify(
            id=thread_id, body={"removeLabelIds": ["INBOX"]}
        ).execute()
        return {"status": "archived", "thread_id": thread_id}

    def _resolve_label(self, label: str) -> str:
        labels = (
            self.service.users().labels().list(userId="me").execute().get("labels", [])
        )
        for existing in labels:
            if existing["name"].lower() == label.lower():
                return existing["id"]
        created = (
            self.service.users()
            .labels()
            .create(
                userId="me",
                body={
                    "name": label,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            .execute()
        )
        return created["id"]
