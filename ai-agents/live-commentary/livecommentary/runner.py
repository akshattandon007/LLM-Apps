"""The orchestration loop.

Pulls state + events from a provider, detects genuinely new events (by stable
id), feeds each to the commentary engine in order, and emits the result
(printed, and optionally spoken). This is deliberately provider-agnostic and
engine-agnostic — it is the glue, nothing more.
"""

from __future__ import annotations

import sys
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque, List, Optional, Set

from .engine import CommentaryEngine
from .models import MatchEvent, MatchState
from .providers.base import MatchProvider
from .tts import Speaker, NullSpeaker


@dataclass
class CommentaryLine:
    event: MatchEvent
    text: str
    state_clock: str


@dataclass
class Runner:
    provider: MatchProvider
    engine: CommentaryEngine
    speaker: Speaker = field(default_factory=NullSpeaker)
    history_size: int = 6
    emit: Callable[[CommentaryLine], None] = None  # output sink

    _seen: Set[str] = field(default_factory=set, init=False)
    _history: Deque[str] = field(default_factory=deque, init=False)

    def __post_init__(self):
        self._history = deque(maxlen=self.history_size)
        if self.emit is None:
            self.emit = _default_emit

    # -- single tick ------------------------------------------------------
    def tick(self, match_id: str) -> List[CommentaryLine]:
        """Process one poll: return commentary for any new events."""
        state = self.provider.get_state(match_id)
        events = self.provider.get_events(match_id)
        produced: List[CommentaryLine] = []
        for event in events:
            if event.id in self._seen:
                continue
            self._seen.add(event.id)
            try:
                text = self.engine.commentate(state, event, list(self._history))
            except Exception as exc:  # never let one bad event kill the loop
                text = f"[commentary unavailable: {exc}] {event.text}"
            if text:
                self._history.append(text)
            line = CommentaryLine(event=event, text=text, state_clock=state.clock)
            produced.append(line)
            self.emit(line)
            self.speaker.say(text)
        return produced

    # -- full run ---------------------------------------------------------
    def run(
        self,
        match_id: str,
        max_ticks: Optional[int] = None,
        on_state: Optional[Callable[[MatchState], None]] = None,
    ) -> None:
        """Poll until the match is final (or ``max_ticks`` is reached)."""
        ticks = 0
        interval = self.provider.poll_interval()
        try:
            while True:
                state = self.provider.get_state(match_id)
                if on_state:
                    on_state(state)
                self.tick(match_id)
                ticks += 1
                if state.is_final:
                    break
                if max_ticks is not None and ticks >= max_ticks:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[stopped]", file=sys.stderr)
        finally:
            self.provider.close()
            self.speaker.close()


def _default_emit(line: CommentaryLine) -> None:
    clock = line.state_clock or line.event.clock or ""
    prefix = f"[{clock}] " if clock else ""
    print(f"{prefix}{line.text}", flush=True)
