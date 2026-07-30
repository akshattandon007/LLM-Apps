"""Cadence engine built on APScheduler (async).

Handles:
- Per-approval `notify` and `dispatch` one-shot jobs
- Recurring cadences (daily digest, Friday ROTA, stale-DM scan)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .approval_queue import ApprovalQueue
from .memory import Store


log = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        store: Store,
        approvals: ApprovalQueue,
        timezone_name: str,
        # Action handlers — injected so the scheduler stays pure
        actions: dict[str, Callable[[dict[str, Any]], Awaitable[None]]],
    ):
        self.store = store
        self.approvals = approvals
        self.tz = timezone_name
        self.actions = actions
        self._sched = AsyncIOScheduler(timezone=self.tz)

    def start(self) -> None:
        self._sched.start()
        self._reload_cadences()
        self._reload_pending_approvals()
        log.info("Scheduler started (tz=%s)", self.tz)

    def shutdown(self) -> None:
        self._sched.shutdown(wait=False)

    # ------------------------------------------------------------ approvals
    def schedule_approval_jobs(self, approval_id: int, scheduled_send_iso: str) -> None:
        send_at = datetime.fromisoformat(scheduled_send_iso)
        if send_at.tzinfo is None:
            send_at = send_at.replace(tzinfo=timezone.utc)
        notify_at = send_at - self.approvals.lead

        # If notify_at is already past (edge case on restart), fire immediately.
        if notify_at < datetime.now(timezone.utc):
            notify_at = datetime.now(timezone.utc) + timedelta(seconds=2)

        self._sched.add_job(
            self.approvals.notify_tick,
            trigger=DateTrigger(run_date=notify_at),
            args=[approval_id],
            id=f"approval-notify-{approval_id}",
            replace_existing=True,
        )
        self._sched.add_job(
            self.approvals.dispatch_tick,
            trigger=DateTrigger(run_date=send_at),
            args=[approval_id],
            id=f"approval-dispatch-{approval_id}",
            replace_existing=True,
        )
        log.info("Scheduled approval #%d: notify=%s, send=%s",
                 approval_id, notify_at.isoformat(), send_at.isoformat())

    def _reload_pending_approvals(self) -> None:
        for row in self.store.list_pending_approvals():
            self.schedule_approval_jobs(row["id"], row["scheduled_send"])

    # ------------------------------------------------------------ cadences
    def register_cadence(
        self,
        *,
        name: str,
        kind: str,             # 'cron' or 'interval'
        spec: dict[str, Any],
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Persist and schedule a recurring job."""
        self.store.upsert_cadence(name=name, kind=kind, spec=spec,
                                   action=action, payload=payload)
        self._schedule_one_cadence(name=name, kind=kind, spec=spec,
                                    action=action, payload=payload or {})

    def _schedule_one_cadence(
        self, *, name: str, kind: str, spec: dict[str, Any],
        action: str, payload: dict[str, Any],
    ) -> None:
        handler = self.actions.get(action)
        if not handler:
            log.warning("Unknown action %r for cadence %r", action, name)
            return

        if kind == "cron":
            trigger = CronTrigger(timezone=self.tz, **spec)
        elif kind == "interval":
            trigger = IntervalTrigger(**spec)
        else:
            log.warning("Unknown cadence kind %r", kind)
            return

        self._sched.add_job(
            handler,
            trigger=trigger,
            args=[payload],
            id=f"cadence-{name}",
            replace_existing=True,
        )
        log.info("Registered cadence %r (%s)", name, kind)

    def _reload_cadences(self) -> None:
        for row in self.store.list_cadences():
            self._schedule_one_cadence(
                name=row["name"],
                kind=row["kind"],
                spec=json.loads(row["spec"]),
                action=row["action"],
                payload=json.loads(row["payload"] or "{}"),
            )
