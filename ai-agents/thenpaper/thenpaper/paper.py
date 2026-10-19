"""Front-page assembly and ASCII rendering for ThenPaper."""

from __future__ import annotations

import datetime as _dt
from dataclasses import asdict, dataclass, field
from typing import Optional

from .api import DayFacts, DayItem

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

THEMES = {
    "morning": {"accent": "★", "edition": "Morning Edition"},
    "evening": {"accent": "☾", "edition": "Evening Edition"},
    "late": {"accent": "✦", "edition": "Late Edition — Final"},
}

TAGLINE = "All the news that was, we print."


@dataclass
class FrontPage:
    """The assembled front page before rendering."""

    month: int
    day: int
    date_label: str
    weekday: str
    theme: str
    edition: str
    headline: str
    dek: str
    twin_intro: str
    lead: Optional[DayItem]
    events: list[DayItem] = field(default_factory=list)
    twins: list[DayItem] = field(default_factory=list)
    deaths: list[DayItem] = field(default_factory=list)
    holidays: list[str] = field(default_factory=list)
    source: str = "live"
    focus_year: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _recency_bonus(year: int) -> float:
    if year >= 2000:
        return 30.0
    if year >= 1900:
        return 20.0
    if year >= 1800:
        return 10.0
    if year >= 1500:
        return 4.0
    return 0.0


def _focus_bonus(year: int, focus_year: Optional[int]) -> float:
    if focus_year is None:
        return 0.0
    gap = abs(year - focus_year)
    if gap <= 25:
        return 26.0
    if gap <= 65:
        return 14.0
    return 0.0


def _richness(item: DayItem) -> float:
    return min(len(item.text), 60) / 60.0


def rank_events(
    events: list[DayItem], limit: int = 6, focus_year: Optional[int] = None
) -> list[DayItem]:
    """Rank events: era affinity, then recency, then story richness."""
    def key(e: DayItem) -> tuple:
        if focus_year is not None:
            # "Front page of your era": events closest to the focus year first.
            return (-abs(e.year - focus_year), _recency_bonus(e.year), e.year, _richness(e))
        return (0, _recency_bonus(e.year), e.year, _richness(e))

    scored = sorted(events, key=key, reverse=True)
    return scored[:limit]


def rank_births(births: list[DayItem], limit: int = 3) -> list[DayItem]:
    """Rank births: prefer relatable modern births, then famous older ones."""
    def key(b: DayItem) -> tuple:
        era = 20.0 if 1900 <= b.year <= 2026 else (6.0 if b.year < 1900 else 0.0)
        return (era, b.year if b.year else 0, _richness(b))

    scored = sorted(births, key=key, reverse=True)
    return scored[:limit]


def rank_deaths(deaths: list[DayItem], limit: int = 2) -> list[DayItem]:
    return rank_events(deaths, limit=limit)


def _plain_holiday_text(item: DayItem) -> str:
    text = item.text.replace("\n", " ").strip()
    return text[:80]


def build_front_page(
    facts: DayFacts,
    month: int,
    day: int,
    theme: str = "morning",
    enhancement: Optional[object] = None,
    events_limit: int = 6,
    focus_year: Optional[int] = None,
) -> FrontPage:
    """Assemble a FrontPage from DayFacts plus optional LLM enhancement."""
    theme = theme if theme in THEMES else "morning"
    selected = facts.selected or []
    ranked = rank_events(facts.events, limit=events_limit, focus_year=focus_year)

    lead: Optional[DayItem] = None
    if selected:
        lead = selected[0]
    elif ranked:
        lead = ranked[0]
    elif facts.events:
        lead = facts.events[0]

    lead_key = (lead.year, lead.text) if lead is not None else None
    events = [e for e in ranked if (e.year, e.text) != lead_key]
    if len(events) < 4 and len(facts.events) > len(events):
        rest = [
            e for e in rank_events(facts.events, limit=20, focus_year=focus_year)
            if (e.year, e.text) != lead_key and e not in events
        ]
        events.extend(rest[: 6 - len(events)])

    twins = rank_births(facts.births, limit=3)
    deaths = rank_deaths(facts.deaths, limit=2)
    holidays = [_plain_holiday_text(h) for h in facts.holidays[:4]]

    weekday = WEEKDAY_NAMES[_dt.date(2000, month, day).weekday()]
    date_label = f"{weekday}, {MONTH_NAMES[month - 1]} {day}"

    if enhancement is not None:
        headline = getattr(enhancement, "headline", "") or _fallback_headline(lead, month, day)
        dek = getattr(enhancement, "dek", "") or _fallback_dek(month, day)
        twin_intro = getattr(enhancement, "twin_intro", "") or _fallback_twin_intro(twins)
    else:
        headline = _fallback_headline(lead, month, day)
        dek = _fallback_dek(month, day)
        twin_intro = _fallback_twin_intro(twins)

    return FrontPage(
        month=month,
        day=day,
        date_label=date_label,
        weekday=weekday,
        theme=theme,
        edition=THEMES[theme]["edition"],
        headline=headline,
        dek=dek,
        twin_intro=twin_intro,
        lead=lead,
        events=events[: max(0, 6 - (1 if lead is not None else 0))],
        twins=twins,
        deaths=deaths,
        holidays=holidays,
        source=facts.source,
        focus_year=focus_year,
    )


def _fallback_headline(lead: Optional[DayItem], month: int, day: int) -> str:
    if lead is None:
        return f"THE DAY THAT WAS: {month}/{day}"
    snippet = lead.text[:52].rstrip().upper()
    if lead.year:
        return f"{lead.year}: {snippet}"
    return snippet


def _fallback_dek(month: int, day: int) -> str:
    return (
        f"A front page for {month}/{day}, straight from the archive of "
        "everything that ever happened."
    )


def _fallback_twin_intro(twins: list[DayItem]) -> str:
    if not twins:
        return "The archives are quiet on births today."
    return f"Your birthday twins include {twins[0].text[:70]}."


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _wrap(text: str, width: int) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in text.split():
        # Words longer than the width get hard-wrapped.
        while len(word) > width:
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(word[:width])
            word = word[width:]
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def _center(text: str, width: int) -> str:
    if len(text) >= width:
        return text[:width]
    total = width - len(text)
    left = total // 2
    right = total - left
    return " " * left + text + " " * right


def _bullet(lines_text: str, width: int, marker: str = "•") -> list[str]:
    """Render a bullet with hanging indent so wrapped lines stay aligned."""
    parts = _wrap(lines_text, width - 6)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i == 0:
            out.append(f"   {marker} {part}")
        else:
            out.append("      " + part)
    return out


def render(page: FrontPage, width: int = 74) -> str:
    """Render the front page as an ASCII newspaper."""
    accent = THEMES[page.theme]["accent"]
    out: list[str] = []

    title = f"THE {accent} THEN {accent} PAPER"
    inner = width - 2
    out.append("╔" + "═" * inner + "╗")
    out.append("║" + _center(title, inner) + "║")
    out.append("║" + _center(TAGLINE, inner) + "║")
    out.append("║" + _center(f"{page.date_label} · {page.edition}", inner) + "║")
    if page.focus_year:
        out.append("║" + _center(f"Focus year: {page.focus_year}", inner) + "║")
    out.append("╚" + "═" * inner + "╝")
    out.append("")

    # Headline + dek
    headline_lines = _wrap(page.headline.upper(), width - 8)
    for line in headline_lines:
        out.append(_center(line, width))
    out.append("")
    for line in _wrap(page.dek, width - 10):
        out.append(_center(line, width))
    out.append("")
    out.append("─" * width)
    out.append("")

    # Lead story
    if page.lead is not None:
        out.append(f"★ LEAD STORY — {page.lead.year or 'Year unknown'}")
        out.append("")
        for line in _wrap(page.lead.text, width - 4):
            out.append("   " + line)
        out.append("")

    # Born this day / birthday twins
    if page.twins:
        out.append("★ BORN THIS DAY — your birthday twins")
        out.append("")
        for twin in page.twins:
            label = f"{twin.year}: " if twin.year else ""
            out.extend(_bullet(f"{label}{twin.text}", width))
        out.append("")

    # More events
    if page.events:
        out.append("★ MORE FROM THE FRONT PAGE")
        out.append("")
        for ev in page.events:
            label = f"{ev.year}: " if ev.year else ""
            out.extend(_bullet(f"{label}{ev.text}", width))
        out.append("")

    # In memoriam
    if page.deaths:
        out.append("★ IN MEMORIAM")
        out.append("")
        for d in page.deaths:
            label = f"{d.year}: " if d.year else ""
            out.extend(_bullet(f"{label}{d.text}", width))
        out.append("")

    # Holidays
    if page.holidays:
        out.append("★ ON THE CALENDAR")
        out.append("")
        for h in page.holidays:
            out.extend(_bullet(h, width))
        out.append("")

    out.append("─" * width)
    out.append(_center(f"SOURCE: Wikipedia On This Day ({page.source}) · Generated by ThenPaper", width))
    return "\n".join(out)