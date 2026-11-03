"""Local SQLite store: plan history and 'already served' memory.

The memory matters more than the history: without it every morning hands you
the same Wikipedia article, and the app feels broken by day three.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

from .models import Plan

SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    minutes REAL NOT NULL,
    mode TEXT NOT NULL,
    transport TEXT,
    total_seconds INTEGER NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS served (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    served_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_served_at ON served(served_at);
"""

DEFAULT_RETENTION_DAYS = 14


def default_db_path() -> Path:
    """Respect ``COMMUTECRAFTER_DB`` so tests never touch the real cache."""
    override = os.environ.get("COMMUTECRAFTER_DB")
    if override:
        return Path(override).expanduser()
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "commutecrafter" / "commutecrafter.db"


class Store:
    """Thin, dependency-free persistence layer."""

    def __init__(self, path: str | os.PathLike | None = None) -> None:
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # -- writes -------------------------------------------------------------
    def record_plan(self, plan: Plan) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO plans (created_at, minutes, mode, transport, total_seconds, payload)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    time.time(),
                    plan.minutes,
                    plan.mode,
                    plan.transport,
                    plan.total_seconds,
                    json.dumps(plan.to_dict()),
                ),
            )
            return int(cur.lastrowid or 0)

    def mark_served(self, urls: Iterable[tuple[str, str, str]]) -> int:
        """Record ``(url, title, source)`` tuples as consumed."""
        now = time.time()
        rows = [(u.strip().lower(), t, s, now) for u, t, s in urls if u and u.strip()]
        if not rows:
            return 0
        with self._connect() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO served (url, title, source, served_at)"
                " VALUES (?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM served")
            conn.execute("DELETE FROM plans")

    # -- reads --------------------------------------------------------------
    def recently_served(self, days: int = DEFAULT_RETENTION_DAYS) -> set[str]:
        cutoff = time.time() - days * 86400
        with self._connect() as conn:
            rows = conn.execute("SELECT url FROM served WHERE served_at >= ?", (cutoff,))
            return {r["url"] for r in rows}

    def history(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, minutes, mode, transport, total_seconds, payload"
                " FROM plans ORDER BY id DESC LIMIT ?",
                (max(1, limit),),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                payload = json.loads(row["payload"])
            except ValueError:
                payload = {}
            out.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "minutes": row["minutes"],
                    "mode": row["mode"],
                    "transport": row["transport"],
                    "total_seconds": row["total_seconds"],
                    "items": [
                        {
                            "title": item.get("title"),
                            "segment": item.get("segment"),
                            "minutes": item.get("minutes"),
                        }
                        for seg in payload.get("segments", [])
                        for item in seg.get("items", [])
                    ],
                }
            )
        return out

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            plans = conn.execute("SELECT COUNT(*) AS n FROM plans").fetchone()["n"]
            served = conn.execute("SELECT COUNT(*) AS n FROM served").fetchone()["n"]
        return {"plans": plans, "served_items": served, "db": str(self.path)}
