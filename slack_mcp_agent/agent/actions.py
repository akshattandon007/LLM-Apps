"""Cadence action handlers.

These are the functions scheduled jobs invoke. Each one produces a message
for the principal (digest, ROTA assignment, stale-DM nudge) and either:
- DMs the principal directly (digests/nudges are FOR the principal), or
- Queues a message for approval (operational posts TO channels).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Awaitable

from .approval_queue import ApprovalQueue
from .memory import Store
from .slack_mcp_client import SlackMCPClient


log = logging.getLogger(__name__)


class Actions:
    """Holds action handlers keyed by name. Wired into Scheduler."""

    def __init__(
        self,
        store: Store,
        mcp: SlackMCPClient,
        approvals: ApprovalQueue,
        owner_slack_id: str,
        notify_owner: Callable[[str], Awaitable[None]],
        summariser: Callable[[str], Awaitable[str]],
    ):
        self.store = store
        self.mcp = mcp
        self.approvals = approvals
        self.owner = owner_slack_id
        self._notify_owner = notify_owner
        self._summarise = summariser  # calls PMAgent.chat under the hood

    def as_map(self) -> dict[str, Callable[[dict[str, Any]], Awaitable[None]]]:
        return {
            "daily_digest": self.daily_digest,
            "rota_reminder": self.rota_reminder,
            "stale_dm_scan": self.stale_dm_scan,
            "custom_draft": self.custom_draft,
        }

    # -------------------------------------------------------- daily digest
    async def daily_digest(self, payload: dict[str, Any]) -> None:
        """P1 DMs > P2 mentions > P3 channel msgs. Delivered as DM to principal."""
        log.info("Running daily digest")
        prompt = (
            "It is time for the principal's daily morning digest. Use your MCP "
            "read tools to: (1) pull unread direct messages, (2) pull mentions "
            "of the principal across channels, (3) list notable recent messages "
            "in key channels they follow. Produce a concise digest prioritising "
            "P1 DMs, then P2 mentions, then P3 channel msgs. Include sender, "
            "channel, 1-line summary, and a suggested action per item. Do NOT "
            "queue any messages — just produce the digest as your reply."
        )
        digest = await self._summarise(prompt)
        await self._notify_owner(f":sun_with_face: *Morning digest*\n\n{digest}")

    # -------------------------------------------------------- rota reminder
    async def rota_reminder(self, payload: dict[str, Any]) -> None:
        """Draft a channel mention for the next person in the ROTA."""
        rota_name = payload.get("rota_name")
        template = payload.get("template",
            "Reminder: please update the pre-pulse by end of day. You're up this week, <@{user}>. :pray:")
        if not rota_name:
            log.warning("rota_reminder missing rota_name")
            return

        nxt = self.store.next_rota(rota_name)
        if not nxt:
            await self._notify_owner(f":warning: ROTA `{rota_name}` not found or empty.")
            return
        user, channel = nxt
        draft = template.format(user=user)

        send_at = datetime.now(timezone.utc) + timedelta(minutes=16)
        approval_id = self.approvals.enqueue(
            channel=channel,
            draft_text=draft,
            scheduled_send=send_at,
            reason=f"Weekly ROTA `{rota_name}` reminder",
        )
        # Schedule the notify/dispatch timers (re-use sched via caller? —
        # the approval queue already persisted; main.py's restart-safe
        # reloader will pick it up, but we also want the timers NOW for
        # this session, so callers inject that. Keeping this simple:
        # we add a helper hook below.)
        if self._schedule_timers:
            self._schedule_timers(approval_id)
        log.info("Rota reminder queued as approval #%d", approval_id)

    # -------------------------------------------------------- stale DM scan
    async def stale_dm_scan(self, payload: dict[str, Any]) -> None:
        """Find DMs >24h old with no reply from the principal and nudge."""
        hours = payload.get("hours", 24)
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        stale = self.store.stale_dms(cutoff)
        if not stale:
            return
        lines = [
            f"• from <@{d['sender']}> in DM `{d['dm_channel']}` "
            f"(seen {d['first_seen']})"
            for d in stale[:20]
        ]
        msg = (
            f":mailbox_with_mail: *{len(stale)} DM(s) unanswered for >{hours}h*\n"
            + "\n".join(lines)
            + "\n\nTell me if you want me to draft replies."
        )
        await self._notify_owner(msg)
        for d in stale:
            self.store.mark_dm_nudged(d["dm_channel"], d["message_ts"])

    # -------------------------------------------------------- custom draft
    async def custom_draft(self, payload: dict[str, Any]) -> None:
        """Generic: use Claude to draft text based on a prompt, then queue for approval."""
        prompt = payload.get("prompt")
        channel = payload.get("channel")
        if not (prompt and channel):
            log.warning("custom_draft missing prompt/channel")
            return
        drafted = await self._summarise(
            f"Draft a Slack message for channel {channel}. {prompt}. "
            f"Output only the message body — no preamble."
        )
        send_at = datetime.now(timezone.utc) + timedelta(minutes=16)
        approval_id = self.approvals.enqueue(
            channel=channel,
            draft_text=drafted,
            scheduled_send=send_at,
            reason=payload.get("reason", "Scheduled custom draft"),
        )
        if self._schedule_timers:
            self._schedule_timers(approval_id)

    # Injected by main.py so actions can wire approval timers in the live sched
    _schedule_timers: Callable[[int], None] | None = None
