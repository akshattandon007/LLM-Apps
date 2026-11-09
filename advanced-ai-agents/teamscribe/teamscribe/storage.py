"""File-based persistence for MeetingRecords."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from teamscribe.models import MeetingRecord


DEFAULT_OUTPUT_DIR = Path.home() / ".teamscribe" / "meetings"


class Storage:
    """Saves and loads MeetingRecords as JSON files."""

    def __init__(self, output_dir: str | None = None):
        self.output_dir = Path(output_dir or os.getenv("TEAMSCRIBE_OUTPUT", str(DEFAULT_OUTPUT_DIR)))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: MeetingRecord) -> Path:
        """Save a meeting record as JSON, return the file path."""
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in record.title)
        safe_name = safe_name.strip().replace(" ", "_")[:60]
        filename = f"{record.date}--{safe_name}.json"
        path = self.output_dir / filename
        path.write_text(record.to_json())
        return path

    def load(self, path: str | Path) -> Optional[MeetingRecord]:
        """Load a meeting record from a JSON file."""
        path = Path(path)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return MeetingRecord.from_dict(data)

    def list_meetings(self) -> list[dict]:
        """List all saved meeting records with metadata."""
        meetings = []
        for f in sorted(self.output_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text())
                meetings.append({
                    "path": str(f),
                    "title": data.get("title", "Untitled"),
                    "date": data.get("date", ""),
                    "participants": len(data.get("participants", [])),
                    "decisions": len(data.get("decisions", [])),
                    "actions": len(data.get("action_items", [])),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return meetings