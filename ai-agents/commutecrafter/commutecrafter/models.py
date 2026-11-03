"""Core data model for CommuteCrafter.

Everything the planner touches is a frozen-ish dataclass so plans can be
serialised to JSON, diffed in tests, and rendered without surprises.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

SEGMENT_WARMUP = "warm-up"
SEGMENT_CORE = "core"
SEGMENT_WINDDOWN = "wind-down"
SEGMENT_ORDER = (SEGMENT_WARMUP, SEGMENT_CORE, SEGMENT_WINDDOWN)


@dataclass
class ContentItem:
    """One piece of consumable content discovered from a source."""

    title: str
    source: str
    url: str
    words: int
    summary: str = ""
    category: str = "general"
    published: Optional[str] = None

    def __post_init__(self) -> None:
        self.words = max(0, int(self.words))
        self.title = (self.title or "").strip()
        self.summary = " ".join((self.summary or "").split())

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "words": self.words,
            "summary": self.summary,
            "category": self.category,
            "published": self.published,
        }


@dataclass
class ScheduledItem:
    """A content item placed into a segment with a concrete time cost.

    ``fraction`` is how much of the item the commuter is asked to consume.
    1.0 means the whole thing; 0.45 means "read roughly the first 45%".
    """

    item: ContentItem
    seconds: int
    segment: str
    fraction: float = 1.0
    reason: str = ""

    @property
    def partial(self) -> bool:
        return self.fraction < 0.999

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.item.title,
            "source": self.item.source,
            "url": self.item.url,
            "category": self.item.category,
            "words": self.item.words,
            "seconds": self.seconds,
            "minutes": round(self.seconds / 60, 2),
            "fraction": round(self.fraction, 3),
            "partial": self.partial,
            "segment": self.segment,
            "reason": self.reason,
            "summary": self.item.summary,
        }


@dataclass
class Segment:
    """A named block of the commute with its own time budget."""

    name: str
    budget_seconds: int
    items: list[ScheduledItem] = field(default_factory=list)

    @property
    def seconds(self) -> int:
        return sum(i.seconds for i in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "budget_seconds": self.budget_seconds,
            "budget_minutes": round(self.budget_seconds / 60, 2),
            "seconds": self.seconds,
            "minutes": round(self.seconds / 60, 2),
            "items": [i.to_dict() for i in self.items],
        }


@dataclass
class Plan:
    """The finished commute plan."""

    minutes: float
    mode: str
    segments: list[Segment]
    tolerance_seconds: int = 90
    weather: Optional[dict[str, Any]] = None
    transport: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    @property
    def target_seconds(self) -> int:
        return int(round(self.minutes * 60))

    @property
    def total_seconds(self) -> int:
        return sum(s.seconds for s in self.segments)

    @property
    def delta_seconds(self) -> int:
        return self.total_seconds - self.target_seconds

    @property
    def fits(self) -> bool:
        return abs(self.delta_seconds) <= self.tolerance_seconds

    @property
    def scheduled_items(self) -> list[ScheduledItem]:
        return [item for segment in self.segments for item in segment.items]

    def to_dict(self) -> dict[str, Any]:
        return {
            "minutes": self.minutes,
            "mode": self.mode,
            "transport": self.transport,
            "target_seconds": self.target_seconds,
            "total_seconds": self.total_seconds,
            "total_minutes": round(self.total_seconds / 60, 2),
            "delta_seconds": self.delta_seconds,
            "fits": self.fits,
            "tolerance_seconds": self.tolerance_seconds,
            "weather": self.weather,
            "warnings": list(self.warnings),
            "segments": [s.to_dict() for s in self.segments],
            "item_count": len(self.scheduled_items),
        }
