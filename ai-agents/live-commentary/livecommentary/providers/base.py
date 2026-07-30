"""The provider interface.

A provider is the only thing you need to write to support a new sport, league,
or data feed. Implement these methods and the rest of the system — dedup,
language, voice, the polling loop — works unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import MatchEvent, MatchState, MatchSummary


class MatchProvider(ABC):
    """Source of truth for a match: its state and its stream of events."""

    name: str = "provider"

    @abstractmethod
    def get_state(self, match_id: str) -> MatchState:
        """Return the current snapshot (score, clock, status) of a match."""

    @abstractmethod
    def get_events(self, match_id: str) -> List[MatchEvent]:
        """Return every event known so far, oldest first.

        The runner deduplicates using ``MatchEvent.id``, so returning the full
        list every poll is fine and expected.
        """

    def discover(self, query: str = "") -> List[MatchSummary]:
        """Find matches matching a free-text query (optional)."""
        raise NotImplementedError(
            f"{self.name} does not support discovery; pass an explicit match id"
        )

    def poll_interval(self) -> float:
        """Seconds between polls. Override for faster/slower feeds."""
        return 12.0

    def close(self) -> None:
        """Release resources (HTTP sessions, etc.). Optional."""
