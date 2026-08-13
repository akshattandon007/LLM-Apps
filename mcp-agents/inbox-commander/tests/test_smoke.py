"""Smoke tests for Inbox Commander.

Mocks the Gmail API client and the LLM — no real credentials, no network.
Run with:  python tests/test_smoke.py   (also pytest-compatible)
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import drafter, summarizer, tools  # noqa: E402

CANONICAL_THREAD = {
    "thread_id": "thread-1",
    "subject": "Vendor renewal for Q1",
    "messages": [
        {
            "id": "m1",
            "thread_id": "thread-1",
            "sender": "Vendor Sales <sales@vendor.example>",
            "recipient": "me@example.com",
            "subject": "Vendor renewal for Q1",
            "date": "Mon, 10 Aug 2026 09:00:00 +0000",
            "snippet": "Your annual renewal is due...",
            "body": "Your annual renewal is due. Please renew by Friday.",
        },
        {
            "id": "m2",
            "thread_id": "thread-1",
            "sender": "me@example.com",
            "recipient": "Vendor Sales <sales@vendor.example>",
            "subject": "Re: Vendor renewal for Q1",
            "date": "Mon, 11 Aug 2026 10:00:00 +0000",
            "snippet": "Can we discuss pricing?",
            "body": "Can we discuss pricing before we commit?",
        },
    ],
}


class FakeGmailClient:
    """In-memory stand-in for src.gmail_client.GmailClient."""

    def __init__(self):
        self.threads = {"thread-1": CANONICAL_THREAD}
        self.sent = []
        self.labeled = []
        self.archived = []

    def search_threads(self, query, max_results=10):
        results = [
            {
                "thread_id": t["thread_id"],
                "subject": t["subject"],
                "sender": t["messages"][0]["sender"],
                "date": t["messages"][0]["date"],
                "snippet": t["messages"][0]["snippet"],
                "message_count": len(t["messages"]),
            }
            for t in self.threads.values()
        ]
        return results[:max_results]

    def read_thread(self, thread_id):
        return self.threads[thread_id]

    def send_message(self, thread_id, body, subject, to):
        self.sent.append(
            {"thread_id": thread_id, "body": body, "subject": subject, "to": to}
        )
        return {"message_id": f"sent-{len(self.sent)}", "thread_id": thread_id}

    def label_thread(self, thread_id, label):
        self.labeled.append((thread_id, label))
        return {"status": "labeled", "thread_id": thread_id, "label": label}

    def archive_thread(self, thread_id):
        self.archived.append(thread_id)
        return {"status": "archived", "thread_id": thread_id}


class FakeLLM:
    """Minimal stand-in for a langchain chat model."""

    def __init__(self, content="Drafted by fake LLM."):
        self.content = content

    def invoke(self, messages):
        return SimpleNamespace(content=self.content)


def setup():
    tools._client = FakeGmailClient()
    tools._APPROVALS.clear()


# ------------------------------------------------------------------ tests


def test_search_threads_returns_summaries():
    results = tools.search_threads("from:vendor.example")
    assert len(results) == 1
    assert results[0]["thread_id"] == "thread-1"
    assert results[0]["subject"] == "Vendor renewal for Q1"
    assert results[0]["message_count"] == 2


def test_read_thread_full():
    thread = tools.read_thread("thread-1")
    assert thread["subject"] == "Vendor renewal for Q1"
    assert len(thread["messages"]) == 2
    assert thread["messages"][0]["sender"] == "Vendor Sales <sales@vendor.example>"
    assert "renewal" in thread["messages"][0]["body"]


def test_summarize_thread_fallback_without_llm():
    with patch.object(summarizer, "_get_llm", return_value=None):
        summary = tools.summarize_thread("thread-1")
    assert "Subject:" in summary
    assert "Vendor renewal for Q1" in summary
    assert "Messages: 2" in summary


def test_summarize_thread_uses_llm_when_configured():
    fake = FakeLLM(content="Vendor wants to renew. Action: decide by Friday.")
    with patch.object(summarizer, "_get_llm", return_value=fake):
        summary = tools.summarize_thread("thread-1")
    assert summary == "Vendor wants to renew. Action: decide by Friday."


def test_draft_reply_default_tone_is_professional():
    with patch.object(drafter, "_get_llm", return_value=None):
        draft = tools.draft_reply("thread-1")
    assert draft["thread_id"] == "thread-1"
    assert draft["tone"] == "professional"
    assert draft["body"].startswith("Hi sales")
    assert "Best regards" in draft["body"]


def test_draft_reply_tone_variants_differ():
    with patch.object(drafter, "_get_llm", return_value=None):
        prof = tools.draft_reply("thread-1", tone="professional")["body"]
        friendly = tools.draft_reply("thread-1", tone="friendly")["body"]
        concise = tools.draft_reply("thread-1", tone="concise")["body"]
    assert friendly != prof
    assert concise != prof
    assert "Cheers" in friendly


def test_draft_reply_uses_llm_when_configured():
    fake = FakeLLM(content="Hi, happy to revisit pricing next quarter.")
    with patch.object(drafter, "_get_llm", return_value=fake):
        draft = tools.draft_reply("thread-1", tone="concise")
    assert draft["body"] == "Hi, happy to revisit pricing next quarter."


def test_send_draft_gated_without_approval():
    try:
        tools.send_draft("thread-1", "Hi, no renewal this quarter.", approval_token="")
        raise AssertionError("expected ValueError for missing approval")
    except ValueError as exc:
        assert "SEND GATED" in str(exc)
    # nothing reached the mail client
    assert tools.get_client().sent == []


def test_send_draft_rejects_body_mismatch():
    token = tools.approve_send("thread-1", "Approved body")["approval_token"]
    try:
        tools.send_draft("thread-1", "Different body", approval_token=token)
        raise AssertionError("expected ValueError for body mismatch")
    except ValueError as exc:
        assert "SEND GATED" in str(exc)
    assert tools.get_client().sent == []


def test_send_draft_after_approval_sends():
    body = "Hi, we will decline the renewal but can reconnect in Q1."
    token = tools.approve_send("thread-1", body)["approval_token"]
    result = tools.send_draft("thread-1", body, approval_token=token)

    assert result["status"] == "sent"
    assert result["thread_id"] == "thread-1"
    assert result["message_id"].startswith("sent-")

    sent = tools.get_client().sent
    assert len(sent) == 1
    assert sent[0]["to"] == "sales@vendor.example"
    assert sent[0]["subject"] == "Re: Vendor renewal for Q1"
    assert sent[0]["body"] == body


def test_approval_token_is_single_use():
    body = "One-time send."
    token = tools.approve_send("thread-1", body)["approval_token"]
    tools.send_draft("thread-1", body, approval_token=token)
    try:
        tools.send_draft("thread-1", body, approval_token=token)
        raise AssertionError("expected ValueError on token reuse")
    except ValueError as exc:
        assert "SEND GATED" in str(exc)
    assert len(tools.get_client().sent) == 1


def test_label_thread():
    result = tools.label_thread("thread-1", "Vendors")
    assert result["status"] == "labeled"
    assert tools.get_client().labeled == [("thread-1", "Vendors")]


def test_archive_thread():
    result = tools.archive_thread("thread-1")
    assert result["status"] == "archived"
    assert tools.get_client().archived == ["thread-1"]


# ------------------------------------------------------------------ runner

TESTS = [
    test_search_threads_returns_summaries,
    test_read_thread_full,
    test_summarize_thread_fallback_without_llm,
    test_summarize_thread_uses_llm_when_configured,
    test_draft_reply_default_tone_is_professional,
    test_draft_reply_tone_variants_differ,
    test_draft_reply_uses_llm_when_configured,
    test_send_draft_gated_without_approval,
    test_send_draft_rejects_body_mismatch,
    test_send_draft_after_approval_sends,
    test_approval_token_is_single_use,
    test_label_thread,
    test_archive_thread,
]


def main() -> int:
    failed = 0
    for fn in TESTS:
        setup()
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {fn.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} smoke tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
