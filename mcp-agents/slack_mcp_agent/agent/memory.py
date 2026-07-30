"""SQLite-backed persistence.

Four tables:
- approvals:   outbound messages waiting for human OK
- cadences:    recurring jobs (daily digest, Friday ROTA, etc.)
- seen_dms:    DM tracking for the 24h-unreplied watcher
- rotas:       named rotations for ops reminders
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel         TEXT NOT NULL,
    thread_ts       TEXT,
    draft_text      TEXT NOT NULL,
    reason          TEXT,                -- why the agent is sending this
    scheduled_send  TEXT NOT NULL,       -- ISO8601 UTC
    notified_at     TEXT,                -- when we pinged the principal
    status          TEXT NOT NULL DEFAULT 'pending',
                                         -- pending|approved|edited|cancelled|sent|expired
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cadences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,
    kind            TEXT NOT NULL,       -- 'cron' | 'interval'
    spec            TEXT NOT NULL,       -- JSON: cron fields or interval seconds
    action          TEXT NOT NULL,       -- 'daily_digest'|'rota_reminder'|'custom'
    payload         TEXT,                -- JSON args for action
    enabled         INTEGER DEFAULT 1,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seen_dms (
    dm_channel      TEXT NOT NULL,
    message_ts      TEXT NOT NULL,
    sender          TEXT NOT NULL,
    replied         INTEGER DEFAULT 0,
    nudged          INTEGER DEFAULT 0,   -- have we already flagged this as stale?
    first_seen      TEXT NOT NULL,
    PRIMARY KEY (dm_channel, message_ts)
);

CREATE TABLE IF NOT EXISTS rotas (
    name            TEXT PRIMARY KEY,
    members         TEXT NOT NULL,       -- JSON list of Slack user IDs
    current_index   INTEGER DEFAULT 0,
    channel         TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
"""


class Store:
    """Thin SQLite wrapper. Thread-safe via a single lock (good enough here)."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(self.path, isolation_level=None)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    # ------------------------------------------------------------------ approvals
    def create_approval(
        self,
        *,
        channel: str,
        draft_text: str,
        scheduled_send: datetime,
        reason: str | None = None,
        thread_ts: str | None = None,
    ) -> int:
        with self._conn() as c:
            cur = c.execute(
                """INSERT INTO approvals
                   (channel, thread_ts, draft_text, reason, scheduled_send, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (channel, thread_ts, draft_text, reason,
                 scheduled_send.isoformat(), datetime.utcnow().isoformat()),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def update_approval(self, approval_id: int, **fields: Any) -> None:
        if not fields:
            return
        sets = ", ".join(f"{k} = ?" for k in fields)
        with self._conn() as c:
            c.execute(
                f"UPDATE approvals SET {sets} WHERE id = ?",
                (*fields.values(), approval_id),
            )

    def get_approval(self, approval_id: int) -> dict[str, Any] | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            return dict(row) if row else None

    def list_pending_approvals(self) -> list[dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM approvals WHERE status = 'pending' ORDER BY scheduled_send"
            ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------ cadences
    def upsert_cadence(
        self,
        *,
        name: str,
        kind: str,
        spec: dict[str, Any],
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO cadences (name, kind, spec, action, payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET
                       kind=excluded.kind, spec=excluded.spec,
                       action=excluded.action, payload=excluded.payload,
                       enabled=1""",
                (name, kind, json.dumps(spec), action,
                 json.dumps(payload or {}), datetime.utcnow().isoformat()),
            )

    def list_cadences(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        q = "SELECT * FROM cadences"
        if enabled_only:
            q += " WHERE enabled = 1"
        with self._conn() as c:
            return [dict(r) for r in c.execute(q).fetchall()]

    def disable_cadence(self, name: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE cadences SET enabled = 0 WHERE name = ?", (name,))

    # ------------------------------------------------------------------ DMs
    def record_dm(self, *, dm_channel: str, message_ts: str, sender: str) -> bool:
        """Return True if newly inserted."""
        with self._conn() as c:
            cur = c.execute(
                """INSERT OR IGNORE INTO seen_dms
                   (dm_channel, message_ts, sender, first_seen)
                   VALUES (?, ?, ?, ?)""",
                (dm_channel, message_ts, sender, datetime.utcnow().isoformat()),
            )
            return cur.rowcount > 0

    def mark_dm_replied(self, dm_channel: str, message_ts: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE seen_dms SET replied = 1 WHERE dm_channel = ? AND message_ts = ?",
                (dm_channel, message_ts),
            )

    def stale_dms(self, older_than_iso: str) -> list[dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT * FROM seen_dms
                   WHERE replied = 0 AND nudged = 0 AND first_seen <= ?""",
                (older_than_iso,),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_dm_nudged(self, dm_channel: str, message_ts: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE seen_dms SET nudged = 1 WHERE dm_channel = ? AND message_ts = ?",
                (dm_channel, message_ts),
            )

    # ------------------------------------------------------------------ rotas
    def set_rota(self, *, name: str, members: list[str], channel: str) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO rotas (name, members, channel, created_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(name) DO UPDATE SET members=excluded.members,
                                                   channel=excluded.channel""",
                (name, json.dumps(members), channel, datetime.utcnow().isoformat()),
            )

    def next_rota(self, name: str) -> tuple[str, str] | None:
        """Return (next_user, channel) and advance pointer."""
        with self._conn() as c:
            row = c.execute("SELECT * FROM rotas WHERE name = ?", (name,)).fetchone()
            if not row:
                return None
            members = json.loads(row["members"])
            if not members:
                return None
            idx = row["current_index"] % len(members)
            user = members[idx]
            c.execute(
                "UPDATE rotas SET current_index = ? WHERE name = ?",
                ((idx + 1) % len(members), name),
            )
            return user, row["channel"]
