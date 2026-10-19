"""Wikipedia "On This Day" data layer for ThenPaper.

Fetches what happened, who was born, who died, and which holidays fall on a
given calendar date using Wikipedia's public REST API (zero auth, free).

Deliberately stdlib-only: ``urllib.request`` instead of ``requests`` so the
project runs anywhere with no pip installs at runtime.
"""

from __future__ import annotations

import datetime as _dt
import json
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable, Optional

BASE_URL = "https://en.wikipedia.org/api/rest_v1/feed/onthisday"
USER_AGENT = "ThenPaper/1.0 (personal AI app; contact akshattandon4@gmail.com)"
TIMEOUT_SECONDS = 15

#: Injection point for tests. Tests replace this with a function returning
#: canned (status, body) tuples; production uses urllib.
_fetch_json: Optional[Callable[[str], tuple[int, Any]]] = None


def set_fetcher(fn: Optional[Callable[[str], tuple[int, Any]]]) -> None:
    """Override the HTTP layer so tests stay offline and hermetic."""
    global _fetch_json
    _fetch_json = fn


def _default_fetch_json(url: str) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        status = resp.status
        body = resp.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(body)
    except ValueError:
        data = {}
    return status, data


def _get_json(url: str) -> tuple[int, Any]:
    if _fetch_json is not None:
        return _fetch_json(url)
    return _default_fetch_json(url)


@dataclass
class ArticlePage:
    """A linked Wikipedia article attached to an On This Day item."""

    title: str
    url: str = ""


@dataclass
class DayItem:
    """One event / birth / death / holiday entry for a date."""

    year: int
    text: str
    pages: list[ArticlePage] = field(default_factory=list)
    kind: str = "event"


@dataclass
class DayFacts:
    """Everything ThenPaper knows about one calendar date."""

    month: int
    day: int
    events: list[DayItem] = field(default_factory=list)
    births: list[DayItem] = field(default_factory=list)
    deaths: list[DayItem] = field(default_factory=list)
    holidays: list[DayItem] = field(default_factory=list)
    selected: list[DayItem] = field(default_factory=list)
    source: str = "live"  # "live" or "simulated"

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_date(month: int, day: int) -> None:
    if not isinstance(month, int) or not isinstance(day, int):
        raise ValueError("month and day must be integers")
    if not (1 <= month <= 12):
        raise ValueError(f"month must be 1..12, got {month}")
    if not (1 <= day <= 31):
        raise ValueError(f"day must be 1..31, got {day}")
    try:
        _dt.date(2000, month, day)
    except ValueError:
        raise ValueError(f"no such date: {month}/{day}")


def _parse_pages(raw_pages: Any) -> list[ArticlePage]:
    pages: list[ArticlePage] = []
    for pg in raw_pages or []:
        if not isinstance(pg, dict):
            continue
        title = pg.get("title") or pg.get("displaytitle") or "Unknown"
        url = ""
        content_urls = pg.get("content_urls") or {}
        desktop = content_urls.get("desktop") or {}
        url = desktop.get("page", "") or pg.get("fullurl", "") or ""
        pages.append(ArticlePage(title=title, url=url))
    return pages


def _parse_items(raw: Any, kind: str) -> list[DayItem]:
    items: list[DayItem] = []
    for entry in raw or []:
        if not isinstance(entry, dict):
            continue
        year_raw = entry.get("year")
        try:
            year = int(year_raw) if year_raw is not None else 0
        except (TypeError, ValueError):
            year = 0
        items.append(
            DayItem(
                year=year,
                text=(entry.get("text") or "").strip(),
                pages=_parse_pages(entry.get("pages")),
                kind=kind,
            )
        )
    return items


def fetch_day(
    month: int,
    day: int,
    kinds: Iterable[str] = ("events", "births", "deaths", "holidays", "selected"),
) -> DayFacts:
    """Fetch every On This Day facet for ``month``/``day``.

    One endpoint per kind. If every endpoint fails (network down, API change,
    blocked), returns deterministic simulated data so the tool always demos.
    """
    _validate_date(month, day)
    facts = DayFacts(month=month, day=day)
    live_hits = 0
    for kind in kinds:
        url = f"{BASE_URL}/{kind}/{month:02d}/{day:02d}"
        try:
            status, data = _get_json(url)
        except Exception:
            continue
        if status != 200:
            continue
        live_hits += 1
        raw = (data or {}).get(kind, [])
        _SINGULAR = {
            "events": "event",
            "births": "birth",
            "deaths": "death",
            "holidays": "holiday",
            "selected": "selected",
        }
        setattr(facts, kind, _parse_items(raw, _SINGULAR.get(kind, kind)))
    if live_hits == 0:
        return simulate_day(month, day)
    return facts


def simulate_day(month: int, day: int) -> DayFacts:
    """Deterministic offline fallback so ThenPaper always prints something."""
    _validate_date(month, day)
    return DayFacts(
        month=month,
        day=day,
        events=[
            DayItem(
                year=1969,
                text="First crewed Moon landing footage is replayed on every channel across the planet",
                kind="event",
            ),
            DayItem(
                year=1945,
                text="The first general-purpose electronic computer hums to life in a university basement",
                kind="event",
            ),
            DayItem(
                year=1519,
                text="A fleet of five small ships sets sail on a voyage that will circle the globe",
                kind="event",
            ),
        ],
        births=[
            DayItem(
                year=1984,
                text="A future front-page reader, born to change the world",
                kind="birth",
            ),
            DayItem(
                year=1922,
                text="A beloved novelist, born this day",
                kind="birth",
            ),
        ],
        deaths=[],
        holidays=[DayItem(year=0, text="World Make-Believe Day", kind="holiday")],
        selected=[],
        source="simulated",
    )