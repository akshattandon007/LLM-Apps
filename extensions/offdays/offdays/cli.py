"""CLI entry point for offdays — max your time off."""

import argparse
import json
import sys
from datetime import date
from typing import Any


def to_json(obj: Any) -> str:
    """JSON serializer that handles date objects."""
    def _default(o: Any) -> str:
        if isinstance(o, date):
            return o.isoformat()
        if hasattr(o, "__dict__"):
            return o.__dict__
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    return json.dumps(obj, default=_default, indent=2)


def get_country_name(code: str) -> str:
    """Country code to emoji flag + common name mapping."""
    # Only the most common; full list comes from API
    names = {
        "US": "United States", "GB": "United Kingdom", "DE": "Germany",
        "FR": "France", "CA": "Canada", "AU": "Australia", "IN": "India",
        "JP": "Japan", "BR": "Brazil", "MX": "Mexico", "IT": "Italy",
        "ES": "Spain", "NL": "Netherlands", "CH": "Switzerland", "SE": "Sweden",
        "NO": "Norway", "DK": "Denmark", "FI": "Finland", "NZ": "New Zealand",
        "SG": "Singapore", "HK": "Hong Kong", "ZA": "South Africa",
        "IE": "Ireland", "BE": "Belgium", "AT": "Austria", "PL": "Poland",
        "PT": "Portugal", "GR": "Greece", "CZ": "Czech Republic",
        "CN": "China", "RU": "Russia", "KR": "South Korea",
    }
    return names.get(code.upper(), code)


def flag_emoji(country_code: str) -> str:
    """Convert ISO 3166-1 alpha-2 code to regional indicator emoji."""
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord("A")) + chr(0x1F1E6 + ord(code[1]) - ord("A"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Max your time off — find optimal leave dates to maximize consecutive holidays.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  offdays                              # US, current year, up to 3 leave days
  offdays --country GB                 # United Kingdom
  offdays --country DE --year 2027 --days 5  # Germany 2027, 5 leave days
  offdays --list-countries             # All supported countries
  offdays --json                       # Machine-readable JSON output
  offdays --min-stretch 5              # Only show plans with 5+ consecutive days off
        """,
    )
    parser.add_argument("--country", "-c", default="US", help="ISO 3166-1 alpha-2 country code")
    parser.add_argument("--year", "-y", type=int, default=date.today().year, help="Year (default: current)")
    parser.add_argument("--days", "-d", type=int, default=3, help="Max leave days to plan for (default: 3)")
    parser.add_argument("--top", "-t", type=int, default=10, help="Number of top plans to show (default: 10)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--list-countries", action="store_true", help="List supported countries and exit")
    parser.add_argument("--min-stretch", type=int, default=0, help="Minimum consecutive days off to show")

    args = parser.parse_args()

    try:
        from .api import fetch_holidays, fetch_countries
        from .planner import compute_plans, build_off_set, find_blocks
    except ImportError:
        # Fallback for direct run
        from api import fetch_holidays, fetch_countries  # type: ignore
        from planner import compute_plans, build_off_set, find_blocks  # type: ignore

    if args.list_countries:
        countries = fetch_countries()
        print(f"{'Code':<8} {'Country'}")
        print("-" * 40)
        for c in sorted(countries, key=lambda x: x["name"].lower()):
            print(f"{c['countryCode']:<8} {c['name']}")
        return

    # Fetch holidays
    try:
        raw_holidays = fetch_holidays(args.country, args.year)
    except Exception as e:
        print(f"Error fetching holidays: {e}", file=sys.stderr)
        sys.exit(1)

    if not raw_holidays:
        print(f"No public holidays found for {args.country} in {args.year}.", file=sys.stderr)
        sys.exit(1)

    # Filter to national (global) public/bank holidays
    holidays = [h for h in raw_holidays if h.get("global") is True]

    if not holidays:
        # Fallback: use all with "Public" type
        holidays = [h for h in raw_holidays if "Public" in (h.get("types") or [])]
    if not holidays:
        holidays = raw_holidays  # last resort: use everything

    plans = compute_plans(holidays, args.year, args.days, args.top)

    # Filter by min-stretch
    if args.min_stretch:
        plans = [p for p in plans if p.days_off >= args.min_stretch]

    # Build country name mapping from API
    try:
        countries = fetch_countries()
        country_names = {c["countryCode"]: c["name"] for c in countries}
    except Exception:
        country_names = {}

    country_name = country_names.get(args.country.upper(), get_country_name(args.country))

    if args.json:
        output = {
            "country": args.country.upper(),
            "country_name": country_name,
            "year": args.year,
            "leave_budget": args.days,
            "public_holidays": len(holidays),
            "plans": [
                {
                    "leave_dates": [d.isoformat() for d in p.leave_dates],
                    "stretch_start": p.stretch_start.isoformat(),
                    "stretch_end": p.stretch_end.isoformat(),
                    "days_off": p.days_off,
                    "leave_used": p.leave_used,
                    "extra_free": p.extra_free,
                    "holidays_covered": p.holidays_covered,
                }
                for p in plans
            ],
        }
        print(to_json(output))
        return

    # Human output
    # Header
    total_workdays = sum(
        1 for d in range(
            date(args.year, 1, 1).toordinal(),
            date(args.year + 1, 1, 1).toordinal()
        )
        if date.fromordinal(d).weekday() < 5
    )
    print(f"\n{flag_emoji(args.country)}  **{args.year} \u00b7 {country_name}** ({args.country.upper()})")
    print(f"Public holidays: {len(holidays)} \u00b7 Workdays: {total_workdays}")
    print()

    if not plans:
        print("No optimal leave plans found. Try a larger leave budget or a different year.")
        return

    # Free 3+ day weekends
    off, _ = build_off_set(holidays, args.year)
    blocks = find_blocks(off, args.year)
    free_long = [b for b in blocks if len(b) >= 3]
    if free_long:
        print("**\u2726 Free long weekends** (no leave needed):")
        for b in sorted(free_long, key=len, reverse=True)[:5]:
            h_names = [
                h["name"] for h in holidays
                if date.fromisoformat(h["date"]) in b
            ]
            h_str = f" \u00b7 {'/'.join(set(h_names))}" if h_names else ""
            print(f"  {b[0].strftime('%b %d')}\u2013{b[-1].strftime('%d')} "
                  f"({len(b)} days){h_str}")
        print()

    # Top plans
    # Top plans
    print(f"\n**\U0001F3AF TOP LEAVE PLANS** (using up to {args.days} leave days):")
    print()

    for i, p in enumerate(plans, 1):
        ld_str = ", ".join(d.strftime("%a %b %d") for d in p.leave_dates) if p.leave_dates else "—"
        date_range = f"{p.stretch_start.strftime('%b %d')} \u2013 {p.stretch_end.strftime('%b %d')}"
        h_str = f" \u00b7 {'/'.join(p.holidays_covered)}" if p.holidays_covered else ""

        print(f"  **{i}.** Book {p.leave_used} day{'' if p.leave_used == 1 else 's'} "
              f"\u2192 {p.days_off} off ({p.extra_free} free)")
        print(f"       {ld_str}")
        print(f"       {date_range}{h_str}")
        print()

    # Summary tip
    print("---")
    print("**Tip:** Plans ranked by max days off. Book the fewest leave days "
          "for the longest break you need.")
    print()


if __name__ == "__main__":
    main()