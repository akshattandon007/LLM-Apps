"""Deterministic date and deadline extraction from school paperwork.

School documents are full of dates ("October 14", "10/28/2026", "next
Wednesday") and deadlines ("return this slip by...", "due..."). We extract
them with regexes + a nearest-future resolution policy — no LLM, no dateparser
dependency, fully testable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from .textutil import clean_whitespace, split_sentences

MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}

_MONTH_DAY_RE = re.compile(
    r"\b(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|"
    r"aug|august|sep|sept|september|oct|october|nov|november|dec|december)"
    r"\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b",
    re.IGNORECASE,
)
_MDY_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b")
_ISO_RE = re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b")
_WEEKDAY_RE = re.compile(
    r"\b((?:next|this|coming)\s+)?(monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday)\b",
    re.IGNORECASE,
)

# Substring signals that a sentence is stating a deadline, not just an event.
# "return", "due", "submit" dominate real school-document phrasing.
_DEADLINE_SIGNALS = (
    "due", "deadline", "must ", "need to", "return", "submit",
    "no later than", "sign and", "please sign", "complete and",
)


@dataclass(frozen=True)
class DateHit:
    iso: str          # resolved date, ISO format (YYYY-MM-DD)
    kind: str         # "event" or "deadline"
    context: str      # the sentence the date came from
    original: str     # the raw matched text


def _is_deadline(sentence: str) -> bool:
    low = sentence.lower()
    return any(sig in low for sig in _DEADLINE_SIGNALS)


def _resolve(month: int, day: int, year: int | None, today: date) -> date | None:
    try:
        if year is not None:
            return date(year, month, day)
    except ValueError:
        return None
    # No year given: pick the nearest future occurrence (school docs are
    # almost always about upcoming dates; roll over to next year when passed).
    for y in (today.year, today.year + 1):
        try:
            candidate = date(y, month, day)
        except ValueError:
            continue
        if candidate >= today:
            return candidate
    return None


def _weekday_date(day_name: str, qualifier: str | None, today: date) -> date:
    target = WEEKDAYS[day_name.lower()]
    delta = (target - today.weekday()) % 7
    if qualifier and qualifier.lower() == "next":
        delta = delta + 7 if delta else 7
    elif delta == 0:
        delta = 7  # a bare weekday, or "this X", on the same day → next week
    return today + timedelta(days=delta)


def extract_dates(text: str, today: date | None = None) -> list[DateHit]:
    """Return every distinct date in *text*, resolved to ISO format.

    Dates are deduplicated by (ISO date, kind) and sorted chronologically.
    """
    today = today or date.today()
    hits: list[DateHit] = []
    for sentence in split_sentences(text):
        kind = "deadline" if _is_deadline(sentence) else "event"
        clean = clean_whitespace(sentence)
        # When a sentence already carries an explicit calendar date, an
        # unqualified weekday in the same sentence ("Saturday, October 24")
        # is redundant — without this guard it would spawn a phantom
        # near-date (the *next* Saturday, not October 24). Qualifier-carrying
        # weekdays ("next Wednesday") are always kept.
        explicit_found = False

        for m in _MONTH_DAY_RE.finditer(sentence):
            month = MONTH_NAMES[m.group(1).lower().rstrip(".")]
            day = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else None
            resolved = _resolve(month, day, year, today)
            if resolved is None:
                continue
            explicit_found = True
            hits.append(DateHit(resolved.isoformat(), kind, clean, m.group(0)))

        for m in _MDY_RE.finditer(sentence):
            a, b = int(m.group(1)), int(m.group(2))
            year = int(m.group(3)) if m.group(3) else None
            if a > 12 and b <= 12:  # clearly DD/MM, e.g. 31/12/2026
                month, day = b, a
            else:                   # default US-style MM/DD
                month, day = a, b
            resolved = _resolve(month, day, year, today)
            if resolved is None:
                continue
            explicit_found = True
            hits.append(DateHit(resolved.isoformat(), kind, clean, m.group(0)))

        for m in _ISO_RE.finditer(sentence):
            try:
                resolved = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                continue
            explicit_found = True
            hits.append(DateHit(resolved.isoformat(), kind, clean, m.group(0)))

        for m in _WEEKDAY_RE.finditer(sentence):
            qualifier = m.group(1).strip().lower() if m.group(1) else None
            if explicit_found and not qualifier:
                continue
            resolved = _weekday_date(m.group(2), qualifier, today)
            hits.append(DateHit(resolved.isoformat(), kind, clean, m.group(0)))

    deduped: dict[tuple[str, str], DateHit] = {}
    for h in hits:
        deduped.setdefault((h.iso, h.kind), h)
    return sorted(deduped.values(), key=lambda h: h.iso)