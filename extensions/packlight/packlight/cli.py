"""Argument parsing and entry point for Pack Light."""
import argparse
import sys
from datetime import datetime, date
from pathlib import Path

from packlight.weather import WeatherClient, GeocodeError, ForecastError
from packlight.packer import PackingEngine


def _parse_date(raw: str) -> date:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date '{raw}'. Use YYYY-MM-DD format.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="packlight",
        description="Generate a weather-based packing list for your trip.",
    )
    location = parser.add_argument_group("Location (provide city OR lat/lon)")
    location.add_argument("city", nargs="?", default=None,
                          help="City name (e.g. 'Tokyo', 'Paris,FR')")
    location.add_argument("--lat", type=float, default=None,
                          help="Latitude (if not using city name)")
    location.add_argument("--lon", type=float, default=None,
                          help="Longitude (if not using city name)")

    parser.add_argument("--from", dest="date_from", default=None,
                        help="Start date YYYY-MM-DD (default: today)")
    parser.add_argument("--to", "--until", dest="date_to", default=None,
                        help="End date YYYY-MM-DD (default: 3 days from start)")
    parser.add_argument("-d", "--days", type=int, default=None,
                        help="Trip length in days (alternative to --to)")

    parser.add_argument("--rules", default=None,
                        help="Path to custom rules YAML file")
    parser.add_argument("--output", choices=["list", "table", "minimal"],
                        default="list",
                        help="Output format (default: list)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- Resolve location ---
    lat, lon = None, None
    location_name = args.city or "your destination"
    if args.city:
        try:
            wc = WeatherClient()
            lat, lon, resolved = wc.geocode(args.city)
            location_name = resolved
        except GeocodeError as e:
            print(f"❌ Could not find city '{args.city}': {e}", file=sys.stderr)
            return 1
    elif args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
    else:
        parser.print_help()
        print("\n⚠️  Provide a city name OR --lat/--lon.", file=sys.stderr)
        return 1

    # --- Resolve dates ---
    today = date.today()
    date_from: date
    date_to: date

    if args.date_from:
        date_from = _parse_date(args.date_from)
    else:
        date_from = today

    if args.date_to:
        date_to = _parse_date(args.date_to)
    elif args.days:
        from datetime import timedelta
        date_to = date_from + timedelta(days=args.days - 1)
    else:
        from datetime import timedelta
        date_to = date_from + timedelta(days=2)  # default 3-day trip

    if date_to < date_from:
        print("❌ End date must be after start date.", file=sys.stderr)
        return 1

    # --- Fetch weather ---
    try:
        wc = WeatherClient()
        daily = wc.get_forecast(lat, lon, date_from, date_to)
    except ForecastError as e:
        print(f"❌ Weather fetch failed: {e}", file=sys.stderr)
        return 1

    # --- Generate packing list ---
    rules_path: str | None = args.rules
    engine = PackingEngine(rules_path)

    print(f"\n🌍  {location_name}")
    trip_dates = f"{date_from} → {date_to} ({len(daily)} day(s))"
    print(f"📅  {trip_dates}")
    print()

    items = engine.generate(daily)

    if not items:
        print("No packing suggestions — check your rules file?")
        return 0

    groups = {}
    for itm in items:
        groups.setdefault(itm.category, []).append(itm.item)

    if args.output == "minimal":
        for cat, cat_items in groups.items():
            print(f"{cat}: {', '.join(cat_items)}")
    elif args.output == "table":
        print(f"{'Category':<20} {'Item':<30} {'Why':<40}")
        print("-" * 90)
        for itm in items:
            print(f"{itm.category:<20} {itm.item:<30} {itm.reason:<40}")
    else:
        for cat, cat_items in groups.items():
            print(f"═══ {cat.upper()} ═══")
            for it in cat_items:
                print(f"  ☐ {it}")
            print()

    print(f"\n✅ Packing list generated for {location_name} "
          f"({len(items)} items across {len(groups)} categories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())