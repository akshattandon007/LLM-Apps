"""Data models for DreamDecoder."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class DreamInterpretation:
    """Structured output from the dream interpretation engine."""

    interpretation: str  # 2-3 paragraph analysis
    symbols: list[str]  # Key symbols identified in the dream
    mood: str  # Overall mood/tone (e.g., "peaceful", "anxious", "surreal")
    themes: list[str]  # Recurring themes (e.g., "freedom", "loss", "transformation")


@dataclass
class DreamEntry:
    """A single dream journal entry."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    dream_text: str = ""
    interpretation: Optional[DreamInterpretation] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.interpretation is not None:
            d["interpretation"] = asdict(self.interpretation)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "DreamEntry":
        inter = d.get("interpretation")
        if isinstance(inter, dict):
            d["interpretation"] = DreamInterpretation(**inter)
        return cls(**d)


@dataclass
class DreamStats:
    """Aggregated statistics across journal entries."""

    total_entries: int = 0
    top_symbols: list[tuple[str, int]] = field(default_factory=list)
    top_themes: list[tuple[str, int]] = field(default_factory=list)
    mood_distribution: dict[str, int] = field(default_factory=dict)
    first_date: Optional[str] = None
    last_date: Optional[str] = None