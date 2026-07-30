"""football-data.org provider (soccer).

Uses the football-data.org REST API. The free tier gives fixtures, live scores
and goal events for major competitions. Get a free key at
https://www.football-data.org/ and set ``FOOTBALL_DATA_API_KEY``.

This feed is score/goal oriented rather than minute-by-minute, so it is a good
example of a provider that emits coarse but real events.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..models import EventType, MatchEvent, MatchState, MatchSummary, Team
from .base import MatchProvider

BASE = "https://api.football-data.org/v4"


class FootballDataProvider(MatchProvider):
    name = "football-data"

    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or os.environ.get("FOOTBALL_DATA_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "FootballDataProvider needs FOOTBALL_DATA_API_KEY "
                "(free key at https://www.football-data.org/)"
            )
        self.timeout = timeout
        self._session = None
        self._last_scores: Dict[str, tuple] = {}

    def _get(self, path: str, params: Optional[dict] = None) -> Dict[str, Any]:
        if self._session is None:
            import requests

            self._session = requests.Session()
            self._session.headers.update({"X-Auth-Token": self.api_key})
        resp = self._session.get(f"{BASE}{path}", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def poll_interval(self) -> float:
        return 30.0  # respect the free tier's rate limits

    def discover(self, query: str = "") -> List[MatchSummary]:
        data = self._get("/matches")
        out: List[MatchSummary] = []
        for m in data.get("matches", []):
            desc = f"{m['homeTeam']['name']} vs {m['awayTeam']['name']}"
            if query and query.lower() not in desc.lower():
                continue
            out.append(
                MatchSummary(
                    match_id=str(m["id"]),
                    sport="soccer",
                    league=m.get("competition", {}).get("name", ""),
                    description=desc,
                    status=_status(m.get("status")),
                    clock=str(m.get("minute", "") or ""),
                )
            )
        return out

    def _match(self, match_id: str) -> dict:
        data = self._get(f"/matches/{match_id}")
        return data.get("match", data)

    def get_state(self, match_id: str) -> MatchState:
        m = self._match(match_id)
        home = Team(str(m["homeTeam"]["id"]), m["homeTeam"]["name"],
                    m["homeTeam"].get("tla", ""))
        away = Team(str(m["awayTeam"]["id"]), m["awayTeam"]["name"],
                    m["awayTeam"].get("tla", ""))
        ft = m.get("score", {}).get("fullTime", {})
        return MatchState(
            match_id=str(match_id),
            sport="soccer",
            league=m.get("competition", {}).get("name", ""),
            home=home,
            away=away,
            home_score=ft.get("home") or 0,
            away_score=ft.get("away") or 0,
            status=_status(m.get("status")),
            clock=str(m.get("minute", "") or ""),
        )

    def get_events(self, match_id: str) -> List[MatchEvent]:
        # Free tier has no play-by-play, so synthesise goals from score changes.
        state = self.get_state(match_id)
        events: List[MatchEvent] = []
        last = self._last_scores.get(match_id)
        cur = (state.home_score, state.away_score)
        if last is not None and cur != last:
            side = state.home.label() if cur[0] > last[0] else state.away.label()
            events.append(
                MatchEvent(
                    id=f"score-{cur[0]}-{cur[1]}",
                    type=EventType.GOAL,
                    text=f"GOAL for {side}! It's now {state.scoreline()}.",
                    minute=int(state.clock) if state.clock.isdigit() else None,
                    home_score=cur[0],
                    away_score=cur[1],
                )
            )
        self._last_scores[match_id] = cur
        return events


def _status(s: Optional[str]) -> str:
    return {
        "SCHEDULED": "scheduled",
        "TIMED": "scheduled",
        "IN_PLAY": "in",
        "PAUSED": "in",
        "FINISHED": "final",
    }.get(s or "", "scheduled")
