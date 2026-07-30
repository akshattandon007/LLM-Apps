"""Simulated provider — a fully offline, scripted match.

No network, no API key. It advances a believable football match in real time
(or accelerated) so you can see the whole pipeline work end to end, and so the
test-suite can run anywhere. It implements the exact same interface as the live
providers, which is the point: swapping ``simulated`` for ``espn`` changes
nothing else.
"""

from __future__ import annotations

import time
from typing import List, Optional

from ..models import EventType, MatchEvent, MatchState, MatchSummary, Team
from .base import MatchProvider

HOME = Team(id="ARS", name="Arsenal", abbreviation="ARS")
AWAY = Team(id="CHE", name="Chelsea", abbreviation="CHE")

# (game_minute, EventType, text). Scores are derived from goal events.
SCRIPT = [
    (0, EventType.KICKOFF, "The referee blows the whistle and we are underway at the Emirates."),
    (7, EventType.SHOT, "Saka drives in from the right and curls one just wide of the far post."),
    (14, EventType.FOUL, "A heavy challenge in midfield from Caicedo earns a stern word from the referee."),
    (23, EventType.GOAL, "GOAL! Odegaard threads it through and Jesus finishes first time into the bottom corner for Arsenal!"),
    (31, EventType.SAVE, "Raya is out smartly to smother a dangerous through ball before Jackson can pounce."),
    (39, EventType.CARD, "Yellow card for Chelsea's Cucurella after a cynical trip on Saka."),
    (45, EventType.PERIOD_END, "Half time. Arsenal lead, but Chelsea have grown into the game."),
    (46, EventType.PERIOD_START, "We're back for the second half, no changes from either side."),
    (58, EventType.GOAL, "GOAL! Out of nowhere, Palmer curls a free kick over the wall and in! Chelsea are level!"),
    (67, EventType.SUBSTITUTION, "Arsenal make a change: Trossard comes on for Jesus, looking for fresh legs up top."),
    (74, EventType.PENALTY, "PENALTY to Arsenal! Saka is brought down in the box and the referee points to the spot."),
    (75, EventType.GOAL, "GOAL! Odegaard sends the keeper the wrong way from the spot. Arsenal lead again!"),
    (88, EventType.VAR, "VAR is checking a possible Chelsea equaliser for offside... and the goal is ruled out!"),
    (90, EventType.GENERIC, "Five minutes of stoppage time signalled as Chelsea throw everyone forward."),
    (95, EventType.FULL_TIME, "FULL TIME! Arsenal hold on to win a thriller against Chelsea."),
]


class SimulatedProvider(MatchProvider):
    name = "simulated"

    def __init__(self, speed: float = 6.0, match_id: str = "sim-1",
                 clock_minutes: Optional[float] = None):
        """``speed`` = simulated game-minutes per real second (higher = faster;
        the default plays the ~95' match in roughly 16 real seconds).

        ``clock_minutes`` pins the match clock to a fixed value and ignores the
        wall clock — useful for deterministic tests and reproducible demos.
        """
        self.speed = max(speed, 0.1)
        self.match_id = match_id
        self._fixed = clock_minutes
        self._start = time.time()

    def _elapsed_minutes(self) -> float:
        if self._fixed is not None:
            return self._fixed
        return (time.time() - self._start) * self.speed

    def poll_interval(self) -> float:
        return max(60.0 / self.speed / 4.0, 0.25)

    def discover(self, query: str = "") -> List[MatchSummary]:
        return [
            MatchSummary(
                match_id=self.match_id,
                sport="soccer",
                league="Simulated Premier League",
                description=f"{HOME.name} vs {AWAY.name}",
                status=self.get_state(self.match_id).status,
                clock=self.get_state(self.match_id).clock,
            )
        ]

    def _scores_through(self, minute: float):
        h = a = 0
        for m, etype, text in SCRIPT:
            if m > minute or etype != EventType.GOAL:
                continue
            if "Arsenal" in text or text.startswith("GOAL! Odegaard sends"):
                h += 1
            else:
                a += 1
        return h, a

    def get_state(self, match_id: str) -> MatchState:
        mins = self._elapsed_minutes()
        h, a = self._scores_through(mins)
        if mins <= 0:
            status, clock = "scheduled", ""
        elif mins >= 95:
            status, clock = "final", "FT"
        else:
            status, clock = "in", f"{int(min(mins, 90))}'"
        return MatchState(
            match_id=match_id,
            sport="soccer",
            league="Simulated Premier League",
            home=HOME,
            away=AWAY,
            home_score=h,
            away_score=a,
            status=status,
            clock=clock,
            venue="Emirates Stadium",
        )

    def get_events(self, match_id: str) -> List[MatchEvent]:
        mins = self._elapsed_minutes()
        out: List[MatchEvent] = []
        for i, (m, etype, text) in enumerate(SCRIPT):
            if m > mins:
                break
            h, a = self._scores_through(m)
            out.append(
                MatchEvent(
                    id=f"sim-{i}",
                    type=etype,
                    text=text,
                    minute=m,
                    clock=f"{m}'",
                    home_score=h,
                    away_score=a,
                )
            )
        return out
