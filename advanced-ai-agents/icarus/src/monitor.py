"""Monitor — memory/learning: records past incidents and surfaces similar ones.

The incident database is a JSONL file at ``INCIDENT_DB_PATH`` (env var) or
``<project-root>/data/incidents.jsonl`` by default.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.models import Alert, PostMortem, RootCause


def get_db_path() -> Path:
    """Return the path to the incident database file."""
    env = os.environ.get("INCIDENT_DB_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "data" / "incidents.jsonl"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_incident(
    incident: Any,
    root_cause: RootCause,
    postmortem: PostMortem,
    db_path: str | Path | None = None,
) -> Path:
    """Append one incident record to the JSONL database.

    Returns the path to the database file.
    """
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "incident": incident.model_dump(mode="json"),
        "root_cause": root_cause.model_dump(mode="json"),
        "postmortem": postmortem.model_dump(mode="json"),
        "recorded_at": _utcnow(),
    }
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return path


def load_incidents(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load all incident records from the database."""
    path = Path(db_path) if db_path else get_db_path()
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def find_similar(alert: Alert, db_path: str | Path | None = None, limit: int = 3) -> list[dict[str, Any]]:
    """Find past incidents that match the alert's service and severity."""
    records = load_incidents(db_path)
    scored: list[tuple[int, dict[str, Any]]] = []
    for rec in records:
        inc = rec.get("incident", {})
        if not inc:
            continue
        score = 0
        stored_alert = inc.get("alert", {})
        if stored_alert.get("service") == alert.service:
            score += 3
        if inc.get("severity") == alert.severity.value:
            score += 1
        if score > 0:
            scored.append((score, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:limit]]


def recent_learnings(alert: Alert, db_path: str | Path | None = None) -> list[str]:
    """Return human-readable summaries of similar past incidents."""
    similar = find_similar(alert, db_path)
    summaries: list[str] = []
    for r in similar:
        inc = r.get("incident", {})
        rc = r.get("root_cause", {})
        summaries.append(
            f"{inc.get('title', 'Unknown')} — resolved with: {rc.get('summary', 'no summary')}"
        )
    return summaries