"""Normalized data models shared across providers and the commentary engine.

Every provider, no matter the sport or data source, converts its raw payloads
into these structures. The runner and the commentary engine only ever see these
types, which is what makes new providers truly pluggable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    """A sport-agnostic taxonomy of match events."""

    KICKOFF = "kickoff"
    GOAL = "goal"
    SCORE = "score"
    SHOT = "shot"
    SAVE = "save"
    FOUL = "foul"
    CARD = "card"
    SUBSTITUTION = "substitution"
    PENALTY = "penalty"
    TIMEOUT = "timeout"
    PERIOD_START = "period_start"
    PERIOD_END = "period_end"
    INJURY = "injury"
    VAR = "var"
    FULL_TIME = "full_time"
    GENERIC = "generic"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Team:
    """One side of a match."""

    id: str
    name: str
    abbreviation: str = ""

    def label(self) -> str:
        return self.abbreviation or self.name


@dataclass(frozen=True)
class MatchEvent:
    """A single thing that happened in a match.

    ``id`` MUST be stable for a given real-world event so the runner can
    deduplicate across polls.
    """

    id: str
    type: EventType
    text: str
    minute: Optional[int] = None
    clock: str = ""
    team_id: Optional[str] = None
    player: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def is_scoring(self) -> bool:
        return self.type in (EventType.GOAL, EventType.SCORE, EventType.PENALTY)


@dataclass
class MatchState:
    """A snapshot of the match at a moment in time."""

    match_id: str
    sport: str
    league: str
    home: Team
    away: Team
    home_score: int = 0
    away_score: int = 0
    status: str = "scheduled"   # "scheduled" | "in" | "final"
    clock: str = ""
    period: str = ""
    venue: str = ""

    @property
    def is_live(self) -> bool:
        return self.status == "in"

    @property
    def is_final(self) -> bool:
        return self.status == "final"

    def scoreline(self) -> str:
        return (
            f"{self.home.label()} {self.home_score} - "
            f"{self.away_score} {self.away.label()}"
        )

    def headline(self) -> str:
        bits = [self.scoreline()]
        if self.clock:
            bits.append(self.clock)
        elif self.status == "scheduled":
            bits.append("not started")
        elif self.status == "final":
            bits.append("FULL TIME")
        return " · ".join(bits)


@dataclass(frozen=True)
class MatchSummary:
    """Lightweight result of a discovery search ("what's on right now")."""

    match_id: str
    sport: str
    league: str
    description: str
    status: str
    clock: str = ""
