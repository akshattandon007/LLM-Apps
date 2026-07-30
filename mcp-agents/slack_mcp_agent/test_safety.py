"""Smoke tests for the safety-critical paths.

We don't hit Anthropic or Slack here — these are pure-logic checks of:
  1. Write-guard: the MCP client's `safe_call_from_model` blocks write tools.
  2. 15-min lead: approvals scheduled too soon are pushed out.
  3. Fail-closed: dispatch of an un-approved message expires it, never sends.
  4. ROTA advances correctly.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

# Make imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.approval_queue import ApprovalQueue
from agent.memory import Store
from agent.slack_mcp_client import SlackMCPClient


def test_write_guard() -> None:
    """SlackMCPClient must refuse write-tool names from the model path."""
    client = SlackMCPClient("dummy")
    # We don't actually connect; we just probe the classification.
    assert client._is_write("slack_post_message")
    assert client._is_write("chat_postMessage")
    assert client._is_write("reactions_add_to_message")
    assert not client._is_write("list_channels")
    assert not client._is_write("get_thread_replies")
    assert not client._is_write("search_messages")

    # And safe_call_from_model returns a BLOCKED string for write tools
    async def probe():
        return await client.safe_call_from_model("slack_post_message", {"channel": "C1"})
    result = asyncio.run(probe())
    assert result.startswith("BLOCKED"), f"Expected BLOCKED, got: {result}"
    print("✓ write_guard: write tools are blocked from model path")


def test_lead_time_enforcement() -> None:
    """Approvals scheduled <15 min out get pushed out automatically."""
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "test.sqlite")

        async def noop(*_a, **_k): pass
        aq = ApprovalQueue(
            store=store, lead_minutes=15, owner_slack_id="U_OWNER",
            notify_owner=noop, slack_send=noop,
        )

        # Ask to send in 2 minutes — should be pushed to at least 16 min out.
        too_soon = datetime.now(timezone.utc) + timedelta(minutes=2)
        aid = aq.enqueue(
            channel="C_TEST", draft_text="hi",
            scheduled_send=too_soon, reason="test",
        )
        row = store.get_approval(aid)
        actual = datetime.fromisoformat(row["scheduled_send"])
        min_expected = datetime.now(timezone.utc) + timedelta(minutes=15)
        assert actual > min_expected, f"Send time {actual} not pushed past lead"
        print(f"✓ lead_time: send pushed from +2min to {actual.isoformat()}")


def test_fail_closed_on_unapproved() -> None:
    """Dispatch of a message still in `pending` at send-time expires it."""
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "test.sqlite")
        notify = AsyncMock()
        send = AsyncMock()
        aq = ApprovalQueue(
            store=store, lead_minutes=15, owner_slack_id="U_OWNER",
            notify_owner=notify, slack_send=send,
        )

        aid = aq.enqueue(
            channel="C_TEST", draft_text="should never go",
            scheduled_send=datetime.now(timezone.utc) + timedelta(minutes=20),
            reason="test",
        )
        # Simulate scheduler firing the dispatch without an approval call
        asyncio.run(aq.dispatch_tick(aid))

        row = store.get_approval(aid)
        assert row["status"] == "expired", f"Expected expired, got {row['status']}"
        send.assert_not_called()
        print("✓ fail_closed: un-approved message expired, never sent")


def test_rota_advances() -> None:
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "test.sqlite")
        store.set_rota(name="pulse", members=["U1", "U2", "U3"], channel="C_PULSE")

        seen = []
        for _ in range(7):
            nxt = store.next_rota("pulse")
            assert nxt is not None
            seen.append(nxt[0])
        assert seen == ["U1", "U2", "U3", "U1", "U2", "U3", "U1"], seen
        print(f"✓ rota_advances: {seen}")


def test_approval_lifecycle() -> None:
    """approve → dispatch sends; cancel → dispatch does nothing."""
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "test.sqlite")
        notify = AsyncMock()
        send = AsyncMock()
        aq = ApprovalQueue(
            store=store, lead_minutes=15, owner_slack_id="U",
            notify_owner=notify, slack_send=send,
        )
        aid = aq.enqueue(
            channel="C", draft_text="hello",
            scheduled_send=datetime.now(timezone.utc) + timedelta(minutes=20),
            reason="t",
        )
        msg = aq.approve(aid)
        assert "Approved" in msg
        asyncio.run(aq.dispatch_tick(aid))
        send.assert_called_once()
        assert store.get_approval(aid)["status"] == "sent"
        print("✓ approval_lifecycle: approved → sent")

        # Now test cancel path
        send.reset_mock()
        aid2 = aq.enqueue(
            channel="C", draft_text="bye",
            scheduled_send=datetime.now(timezone.utc) + timedelta(minutes=20),
            reason="t",
        )
        aq.cancel(aid2)
        asyncio.run(aq.dispatch_tick(aid2))
        send.assert_not_called()
        assert store.get_approval(aid2)["status"] == "cancelled"
        print("✓ approval_lifecycle: cancelled → not sent")


if __name__ == "__main__":
    test_write_guard()
    test_lead_time_enforcement()
    test_fail_closed_on_unapproved()
    test_rota_advances()
    test_approval_lifecycle()
    print("\nAll safety invariants hold. ✅")
