"""Agent 4 — Archivist: tracks decisions across meetings.

The Archivist maintains historical context by reading/writing
an archive file that accumulates decisions and trends over time.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from teamscribe.agent_base import BaseAgent
from teamscribe.models import MeetingRecord


DEFAULT_ARCHIVE_PATH = Path.home() / ".teamscribe" / "archive.json"


class Archivist(BaseAgent):
    """Tracks decisions over time, builds an institutional memory."""

    def __init__(self, archive_path: str | None = None, **kwargs):
        super().__init__(
            name="Archivist",
            role="an institutional memory keeper who tracks decisions, recurring themes, and progress across all meetings",
            **kwargs,
        )
        self.archive_path = Path(archive_path or os.getenv("TEAMSCRIBE_ARCHIVE", str(DEFAULT_ARCHIVE_PATH)))

    def load_archive(self) -> dict:
        """Load historical meeting archive."""
        if self.archive_path.exists():
            return json.loads(self.archive_path.read_text())
        return {"meetings": [], "decisions": [], "trends": []}

    def save_archive(self, archive: dict) -> None:
        """Save archive to disk."""
        self.archive_path.parent.mkdir(parents=True, exist_ok=True)
        self.archive_path.write_text(json.dumps(archive, indent=2))

    def process(self, record: MeetingRecord) -> MeetingRecord:
        """Archive this meeting and identify trends / follow-ups."""
        archive = self.load_archive()

        # Add this meeting's decisions to history
        for decision in record.decisions:
            archive["decisions"].append({
                "meeting": record.title,
                "date": record.date,
                "topic": decision.topic,
                "outcome": decision.outcome,
            })

        # Add meeting metadata
        archive["meetings"].append({
            "title": record.title,
            "date": record.date,
            "participants": record.participants,
            "summary": record.summary,
        })

        # Generate trend analysis if more than 1 meeting archived
        if len(archive["meetings"]) > 1:
            trends = self._detect_trends(archive)
            archive["trends"] = trends

        self.save_archive(archive)
        return record

    def _detect_trends(self, archive: dict) -> list:
        """Ask LLM to identify patterns across meetings."""
        system = (
            "You are analyzing a meeting archive to identify trends. "
            "List 2-4 notable patterns: recurring topics, progress on decisions, "
            "repeated blockers, or shifts in priorities. "
            "Return as a JSON list of strings. If no trends, return []."
        )
        meetings_text = json.dumps(archive["meetings"][-5:], indent=1)  # last 5
        decisions_text = json.dumps(archive["decisions"][-10:], indent=1)
        user = f"Recent meetings:\n{meetings_text}\n\nRecent decisions:\n{decisions_text}"
        raw = self.call_llm(system, user, temperature=0.2)

        import re
        json_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return [raw.strip()]