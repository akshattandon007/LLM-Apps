"""Command-line entry point for ThenPaper.

Usage:
    python -m thenpaper [DATE] [--theme morning|evening|late] [--json]
                        [--offline] [--no-llm] [--events N]

DATE formats: MM/DD, M/D, YYYY/MM/DD, or "today" (default).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from typing import Optional

from . import api, paper, voice


def _parse_date(value: str) -> tuple[int, int, Optional[int]]:
    """Return (month, day, focus_year_or_None) from a user-supplied date."""
    v = value.strip().lower()
    if v == "today":
        today = _dt.date.today()
        return today.month, today.day, None
    parts = [p for p in v.split("/") if p != ""]
    if len(parts) == 2:
        month, day = int(parts[0]), int(parts[1])
        result = (month, day, None)
    elif len(parts) == 3:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        result = (month, day, year)
    else:
        raise ValueError(
            "expected MM/DD, M/D, YYYY/MM/DD, or 'today' (e.g. 10/19, 1984/12/25)"
        )
    api._validate_date(result[0], result[1])  # noqa: SLF001 (shared validation)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="thenpaper",
        description="The day you were born, as a front page. "
        "Pulls real events, births, deaths and holidays from Wikipedia's "
        "On This Day API and prints them as a newspaper front page.",
    )
    parser.add_argument(
        "date",
        nargs="?",
        default="today",
        help="MM/DD, M/D, YYYY/MM/DD, or 'today' (default: today)",
    )
    parser.add_argument(
        "--theme",
        choices=("morning", "evening", "late"),
        default="morning",
        help="front-page edition style (default: morning)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print structured JSON instead of the ASCII front page",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use built-in simulated data (no network)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="skip the LLM editor entirely; use template headlines",
    )
    parser.add_argument(
        "--events",
        type=int,
        default=6,
        help="how many events to list on the front page (default: 6)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        month, day, focus_year = _parse_date(args.date)
    except ValueError as exc:
        print(f"thenpaper: bad date: {exc}", file=sys.stderr)
        return 2
    except (TypeError, ValueError):
        print("thenpaper: bad date format", file=sys.stderr)
        return 2

    if args.offline:
        facts = api.simulate_day(month, day)
    else:
        facts = api.fetch_day(month, day)

    enhancement = voice.enhance(facts, month, day, allow_llm=not args.no_llm)
    page = paper.build_front_page(
        facts,
        month,
        day,
        theme=args.theme,
        enhancement=enhancement,
        events_limit=max(1, args.events),
        focus_year=focus_year,
    )

    if args.json:
        print(json.dumps(page.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(paper.render(page))
    return 0


if __name__ == "__main__":
    sys.exit(main())