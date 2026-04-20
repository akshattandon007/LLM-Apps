"""The approval queue — the teeth behind Rules 1 and 2.

Workflow for every outbound message:

    T_queued          agent drafts, stores with status=pending, scheduled_send=T_send
    T_send - 15min    scheduler fires "notify" job — DMs the principal the draft + id
    T_send            scheduler fires "dispatch" job — if status=approved → send,
                                                       otherwise → expire (fail-closed)

The principal responds to the notify DM with:
    ok <id>               → status = approved, will send at T_send
    cancel <id>           → status = cancelled
    edit <id> <new text>  → update draft, still approved
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable

from .memory import Store


log = logging.getLogger(__name__)


class ApprovalQueue:
    def __init__(
        self,
        store: Store,
        lead_minutes: int,
        owner_slack_id: str,
        notify_owner: Callable[[str], Awaitable[None]],
        slack_send: Callable[[str, str, str | None], Awaitable[None]],
    ):
        """
        Args:
            notify_owner: async fn that DMs the principal (text) — used for
                          the 15-min pre-notice
            slack_send:   async fn (channel, text, thread_ts) that actually
                          posts to Slack. This is the ONLY place we call a
                          write tool.
        """
        self.store = store
        self.lead = timedelta(minutes=lead_minutes)
        self.owner = owner_slack_id
        self._notify_owner = notify_owner
        self._slack_send = slack_send

    # -------------------------------------------------------------- enqueue
    def enqueue(
        self,
        *,
        channel: str,
        draft_text: str,
        scheduled_send: datetime,
        reason: str | None = None,
        thread_ts: str | None = None,
    ) -> int:
        """Called by the agent's `queue_message_for_approval` tool.

        Enforces: scheduled_send must be at least `lead` minutes from now,
        so we always have time to give the 15-min pre-notice.
        """
        now = datetime.now(timezone.utc)
        if scheduled_send.tzinfo is None:
            scheduled_send = scheduled_send.replace(tzinfo=timezone.utc)

        min_send = now + self.lead + timedelta(minutes=1)
        if scheduled_send < min_send:
            scheduled_send = min_send
            log.info("Scheduled send pushed to %s to respect 15-min lead", scheduled_send)

        approval_id = self.store.create_approval(
            channel=channel,
            draft_text=draft_text,
            scheduled_send=scheduled_send,
            reason=reason,
            thread_ts=thread_ts,
        )
        log.info("Queued approval #%d for %s at %s", approval_id, channel, scheduled_send)
        return approval_id

    # -------------------------------------------------------------- tick actions
    async def notify_tick(self, approval_id: int) -> None:
        """Fires at T_send - 15min. DM the principal with the draft."""
        row = self.store.get_approval(approval_id)
        if not row or row["status"] != "pending":
            return
        msg = (
            f":alarm_clock: *Scheduled send in 15 minutes* (approval #{approval_id})\n"
            f"*To channel:* `{row['channel']}`"
            + (f"  (thread `{row['thread_ts']}`)" if row["thread_ts"] else "")
            + f"\n*Reason:* {row['reason'] or '—'}\n"
            f"*Draft:*\n> " + row["draft_text"].replace("\n", "\n> ") + "\n\n"
            f"Reply `ok {approval_id}` to approve · "
            f"`cancel {approval_id}` to abort · "
            f"`edit {approval_id} <new text>` to revise."
        )
        await self._notify_owner(msg)
        self.store.update_approval(approval_id, notified_at=datetime.utcnow().isoformat())

    async def dispatch_tick(self, approval_id: int) -> None:
        """Fires at T_send. Sends if approved, otherwise expires (fail-closed)."""
        row = self.store.get_approval(approval_id)
        if not row:
            return
        if row["status"] == "approved":
            try:
                await self._slack_send(row["channel"], row["draft_text"], row["thread_ts"])
                self.store.update_approval(approval_id, status="sent")
                await self._notify_owner(
                    f":white_check_mark: Sent #{approval_id} to `{row['channel']}`."
                )
            except Exception as e:
                log.exception("Failed to send approval %d", approval_id)
                self.store.update_approval(approval_id, status="failed")
                await self._notify_owner(f":x: Send failed for #{approval_id}: {e}")
        elif row["status"] == "pending":
            # Principal didn't approve in the 15-min window → fail closed.
            self.store.update_approval(approval_id, status="expired")
            await self._notify_owner(
                f":no_entry_sign: Approval #{approval_id} expired unsent "
                f"(no approval received in the 15-min window)."
            )

    # -------------------------------------------------------------- principal commands
    def approve(self, approval_id: int) -> str:
        row = self.store.get_approval(approval_id)
        if not row:
            return f"No such approval #{approval_id}."
        if row["status"] != "pending":
            return f"Approval #{approval_id} is `{row['status']}`, cannot approve."
        self.store.update_approval(approval_id, status="approved")
        return f"Approved #{approval_id}. Will send at {row['scheduled_send']}."

    def cancel(self, approval_id: int) -> str:
        row = self.store.get_approval(approval_id)
        if not row:
            return f"No such approval #{approval_id}."
        if row["status"] not in ("pending", "approved"):
            return f"Approval #{approval_id} is `{row['status']}`, cannot cancel."
        self.store.update_approval(approval_id, status="cancelled")
        return f"Cancelled #{approval_id}."

    def edit(self, approval_id: int, new_text: str) -> str:
        row = self.store.get_approval(approval_id)
        if not row:
            return f"No such approval #{approval_id}."
        if row["status"] not in ("pending", "approved"):
            return f"Approval #{approval_id} is `{row['status']}`, cannot edit."
        self.store.update_approval(approval_id, draft_text=new_text, status="approved")
        return f"Edited and approved #{approval_id}."
