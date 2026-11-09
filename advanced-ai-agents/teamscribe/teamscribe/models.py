"""Data models for TeamScribe — shared types across all agents."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class ActionItem:
    """A single action item from a meeting."""
    owner: str
    description: str
    deadline: Optional[str] = None
    status: str = "open"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ActionItem":
        return cls(**d)


@dataclass
class Decision:
    """A decision reached during a meeting."""
    topic: str
    outcome: str
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Decision":
        return cls(**d)


@dataclass
class MeetingRecord:
    """Complete record of a meeting processed by TeamScribe."""
    title: str
    date: str
    participants: list[str] = field(default_factory=list)
    raw_notes: str = ""

    # Populated by agents
    cleaned_notes: str = ""
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    follow_up_email: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "date": self.date,
            "participants": self.participants,
            "raw_notes": self.raw_notes,
            "cleaned_notes": self.cleaned_notes,
            "summary": self.summary,
            "key_points": self.key_points,
            "decisions": [d.to_dict() for d in self.decisions],
            "action_items": [a.to_dict() for a in self.action_items],
            "follow_up_email": self.follow_up_email,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "MeetingRecord":
        decisions = [Decision.from_dict(dd) for dd in d.get("decisions", [])]
        action_items = [ActionItem.from_dict(aa) for aa in d.get("action_items", [])]
        return cls(
            title=d["title"],
            date=d["date"],
            participants=d.get("participants", []),
            raw_notes=d.get("raw_notes", ""),
            cleaned_notes=d.get("cleaned_notes", ""),
            summary=d.get("summary", ""),
            key_points=d.get("key_points", []),
            decisions=decisions,
            action_items=action_items,
            follow_up_email=d.get("follow_up_email", ""),
        )