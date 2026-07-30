"""ESPN provider — real, live, and key-less.

ESPN exposes public JSON endpoints used by their own scoreboard. No API key:

    scoreboard : https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard
    summary    : https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary?event={id}

``sport``/``league`` are ESPN slugs, e.g. soccer/eng.1, basketball/nba,
football/nfl, baseball/mlb, hockey/nhl. These endpoints are undocumented and
can change; parsing here is defensive and degrades gracefully.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import EventType, MatchEvent, MatchState, MatchSummary, Team
from .base import MatchProvider

BASE = "https://site.api.espn.com/apis/site/v2/sports"

_KEYWORDS = (
    ("goal", EventType.GOAL),
    ("penalty", EventType.PENALTY),
    ("yellow card", EventType.CARD),
    ("red card", EventType.CARD),
    ("substitution", EventType.SUBSTITUTION),
    ("foul", EventType.FOUL),
    ("saved", EventType.SAVE),
    ("var", EventType.VAR),
)


def _classify(text: str) -> EventType:
    low = text.lower()
    for word, etype in _KEYWORDS:
        if word in low:
            return etype
    if "scor" in low or "touchdown" in low or "made" in low or "homer" in low:
        return EventType.SCORE
    return EventType.GENERIC


class ESPNProvider(MatchProvider):
    name = "espn"

    def __init__(self, sport: str = "soccer", league: str = "eng.1",
                 timeout: float = 10.0):
        self.sport = sport
        self.league = league
        self.timeout = timeout
        self._session = None

    def _get(self, url: str, params: Optional[dict] = None) -> Dict[str, Any]:
        if self._session is None:
            import requests

            self._session = requests.Session()
            self._session.headers.update(
                {"User-Agent": "live-commentary/1.0 (+https://example.com)"}
            )
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def discover(self, query: str = "") -> List[MatchSummary]:
        data = self._get(f"{BASE}/{self.sport}/{self.league}/scoreboard")
        out: List[MatchSummary] = []
        for ev in data.get("events", []):
            desc = ev.get("name") or ev.get("shortName") or str(ev.get("id", ""))
            if query and query.lower() not in desc.lower():
                continue
            out.append(
                MatchSummary(
                    match_id=str(ev.get("id")),
                    sport=self.sport,
                    league=self.league,
                    description=desc,
                    status=self._status(ev),
                    clock=self._clock(ev),
                )
            )
        return out

    def get_state(self, match_id: str) -> MatchState:
        data = self._get(f"{BASE}/{self.sport}/{self.league}/summary",
                         params={"event": match_id})
        header = data.get("header", {}) or {}
        comp = (header.get("competitions") or [{}])[0]
        home_c, away_c = self._home_away(comp)
        return MatchState(
            match_id=str(match_id),
            sport=self.sport,
            league=self.league,
            home=self._team(home_c),
            away=self._team(away_c),
            home_score=_to_int(home_c.get("score")),
            away_score=_to_int(away_c.get("score")),
            status=self._status(comp),
            clock=self._clock(comp),
            period=str((comp.get("status", {}) or {}).get("period", "")),
            venue=((data.get("gameInfo", {}) or {}).get("venue", {}) or {}).get(
                "fullName", ""
            ),
        )

    def get_events(self, match_id: str) -> List[MatchEvent]:
        data = self._get(f"{BASE}/{self.sport}/{self.league}/summary",
                         params={"event": match_id})
        events: List[MatchEvent] = []

        for c in data.get("commentary", []) or []:
            text = (c.get("text") or "").strip()
            if not text:
                continue
            seq = c.get("sequence") or c.get("id") or text[:24]
            disp = str((c.get("time", {}) or {}).get("displayValue", "")).strip()
            events.append(
                MatchEvent(
                    id=f"c-{seq}",
                    type=_classify(text),
                    text=text,
                    minute=_minute(disp),
                    clock=disp,
                )
            )

        for grp in data.get("plays", []) or []:
            text = (grp.get("text") or "").strip()
            if not text:
                continue
            pid = grp.get("id") or grp.get("sequenceNumber") or text[:24]
            clock = ((grp.get("clock") or {}).get("displayValue")) or ""
            period = (grp.get("period") or {}).get("number")
            events.append(
                MatchEvent(
                    id=f"p-{pid}",
                    type=_classify(text),
                    text=text,
                    clock=(f"Q{period} {clock}".strip() if period else clock),
                    home_score=_opt_int(grp.get("homeScore")),
                    away_score=_opt_int(grp.get("awayScore")),
                )
            )

        if _looks_newest_first(events):
            events.reverse()
        return events

    @staticmethod
    def _home_away(comp: dict):
        competitors = comp.get("competitors", []) or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        if not home and competitors:
            home = competitors[0]
        if not away and len(competitors) > 1:
            away = competitors[1]
        return home, away

    @staticmethod
    def _team(c: dict) -> Team:
        t = c.get("team", {}) or {}
        return Team(
            id=str(t.get("id", "")),
            name=t.get("displayName") or t.get("name") or "Team",
            abbreviation=t.get("abbreviation", ""),
        )

    @staticmethod
    def _status(ev: dict) -> str:
        status = ev.get("status") or {}
        state = (status.get("type") or {}).get("state")
        return {"pre": "scheduled", "in": "in", "post": "final"}.get(
            state, state or "scheduled"
        )

    @staticmethod
    def _clock(ev: dict) -> str:
        status = ev.get("status") or {}
        return status.get("displayClock") or (status.get("type", {}) or {}).get(
            "shortDetail", ""
        )


def _looks_newest_first(events: List[MatchEvent]) -> bool:
    mins = [e.minute for e in events if e.minute is not None]
    return len(mins) >= 2 and mins[0] > mins[-1]


def _minute(disp: str) -> Optional[int]:
    if not disp:
        return None
    head = disp.split("+")[0].strip().rstrip("'")
    return int(head) if head.isdigit() else None


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _opt_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
