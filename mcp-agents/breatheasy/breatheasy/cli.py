"""argparse CLI for breatheasy — stdlib only (no click/typer).

Commands:
  breatheasy now "Brooklyn"          current AQI + category emoji + advice
  breatheasy forecast "LA" --days 3  daily max AQI trend
  breatheasy pollen "Chicago"        per-type pollen peaks
  breatheasy serve                   MCP stdio server

Every place argument also accepts "lat,lon" (e.g. "40.71,-74.01"), which
skips geocoding entirely.  Unknown places and API failures print a clear
message to stderr and exit with code 1.
"""

from __future__ import annotations

import argparse
import sys

from .advice import (
    POLLEN_EMOJI,
    POLLEN_GUIDANCE,
    POLLEN_TYPES,
    POLLUTANT_DISPLAY,
    POLLUTANT_UNITS,
    aqi_band,
    pollen_bucket,
    top_pollutant,
)
from .api import (
    OpenMeteoClient,
    daily_max_aqi,
    pollen_peak_per_type,
    today_from_payload,
    worst_hour_today,
)
from .geo import GeoLookupError, resolve_place

MAX_FORECAST_DAYS = 7

UNKNOWN_PLACE_HINT = (
    " — try a city name like 'Brooklyn', 'City, State', or 'lat,lon' "
    "(e.g. '40.71,-74.01')."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="breatheasy",
        description=(
            "Is it OK to go outside? Air quality and pollen answers for any "
            "place on Earth — zero API keys, zero signup."
        ),
        epilog=(
            "All commands accept a city name or 'lat,lon'. Examples:\n"
            "  %(prog)s now 'Brooklyn'\n"
            "  %(prog)s forecast 'Los Angeles' --days 3\n"
            "  %(prog)s pollen 'Chicago' --days 1\n"
            "  %(prog)s serve\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    p_now = sub.add_parser("now", help="Current AQI + category + advice for a place")
    p_now.add_argument("place", help="City name or 'lat,lon'")

    p_forecast = sub.add_parser(
        "forecast", help="Daily max AQI trend for a place"
    )
    p_forecast.add_argument("place", help="City name or 'lat,lon'")
    p_forecast.add_argument(
        "--days", type=int, default=3,
        help="Forecast days, clamped to 1-7 (default: 3)",
    )

    p_pollen = sub.add_parser("pollen", help="Per-type pollen peaks for a place")
    p_pollen.add_argument("place", help="City name or 'lat,lon'")
    p_pollen.add_argument(
        "--days", type=int, default=1,
        help="Days to summarize, clamped to 1-7 (default: 1)",
    )

    sub.add_parser("serve", help="Run the MCP stdio server")
    return parser


def main(argv: list[str] | None = None, client: OpenMeteoClient | None = None) -> int:
    """Run the CLI. Returns the process exit code (0 ok, 1 error)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    client = client if client is not None else OpenMeteoClient()

    if args.command == "serve":
        from .server import mcp  # lazy: imports `mcp` only when serving

        mcp.run()  # blocks on stdin until the MCP client disconnects
        return 0
    if args.command == "now":
        return cmd_now(args, client)
    if args.command == "forecast":
        return cmd_forecast(args, client)
    if args.command == "pollen":
        return cmd_pollen(args, client)
    return 0


def cmd_now(args, client: OpenMeteoClient) -> int:
    try:
        lat, lon, label = resolve_place(args.place, client)
        data = client.air_quality(lat, lon, days=1)
    except GeoLookupError:
        print(
            f"Could not find place: {args.place!r}{UNKNOWN_PLACE_HINT}",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001 - user-facing error, exit 1
        print(f"Could not fetch air quality data: {exc}", file=sys.stderr)
        return 1

    current = data.get("current") or {}
    us = current.get("us_aqi")
    eu = current.get("european_aqi")
    if us is None and eu is None:
        print(f"No current air quality data available for {label}.")
        return 0
    aqi = us if us is not None else eu
    band = aqi_band(aqi)
    source = "US AQI" if us is not None else "European AQI"
    print(f"🌬️  {label}")
    print(f"{source}: {aqi} — {band.category} {band.emoji}")
    if us is not None and eu is not None:
        print(f"European AQI: {eu}")
    tp = top_pollutant(current)
    if tp is not None:
        key, value = tp
        print(
            f"Top pollutant: {POLLUTANT_DISPLAY.get(key, key)} "
            f"({value:g} {POLLUTANT_UNITS.get(key, '')})"
        )
    print(f"Advice: {band.advice}")
    return 0


def cmd_forecast(args, client: OpenMeteoClient) -> int:
    days = min(max(int(args.days), 1), MAX_FORECAST_DAYS)
    try:
        lat, lon, label = resolve_place(args.place, client)
        data = client.air_quality(lat, lon, days=days)
    except GeoLookupError:
        print(
            f"Could not find place: {args.place!r}{UNKNOWN_PLACE_HINT}",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Could not fetch air quality forecast: {exc}", file=sys.stderr)
        return 1

    hourly = data.get("hourly") or {}
    daily = daily_max_aqi(hourly)
    if not daily:
        print(f"No air quality forecast data available for {label}.")
        return 0
    today = today_from_payload(data)
    worst = worst_hour_today(hourly, today)
    print(f"📈  Air quality forecast for {label} ({days}-day forecast)")
    print()
    print(f"{'Date':<12} {'Max AQI':<8} Category")
    for date, value in daily[:days]:
        band = aqi_band(value)
        print(f"{date:<12} {value:<8} {band.category} {band.emoji}")
    if worst is not None:
        hh, value = worst
        band = aqi_band(value)
        print()
        print(
            f"Worst hour today ({today}): {hh} — AQI {value} "
            f"({band.category} {band.emoji})"
        )
    overall = aqi_band(max(value for _, value in daily[:days]))
    print()
    print(f"Advice: {overall.advice}")
    return 0


def cmd_pollen(args, client: OpenMeteoClient) -> int:
    days = min(max(int(args.days), 1), MAX_FORECAST_DAYS)
    try:
        lat, lon, label = resolve_place(args.place, client)
        data = client.air_quality(lat, lon, days=days)
    except GeoLookupError:
        print(
            f"Could not find place: {args.place!r}{UNKNOWN_PLACE_HINT}",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Could not fetch pollen forecast: {exc}", file=sys.stderr)
        return 1

    peaks = pollen_peak_per_type(data.get("hourly") or {})
    print(f"🌼  Pollen forecast for {label} ({days}-day peak)")
    if not peaks:
        print(
            "No pollen data for this region/season "
            "(Open-Meteo pollen coverage is mostly Europe)."
        )
        return 0
    for key, display in POLLEN_TYPES:
        if key in peaks:
            peak = peaks[key]
            bucket = pollen_bucket(peak)
            print(
                f"  {display:<8} {peak:>6g} P/m³  {bucket:<6} "
                f"{POLLEN_EMOJI[bucket]}  {POLLEN_GUIDANCE[bucket]}"
            )
        else:
            print(
                f"  {display:<8} {'—':>6} P/m³  no data  🚫  "
                "No pollen data for this region/season."
            )
    return 0


def entrypoint() -> None:
    """Console-script entry (`breatheasy` on PATH after `pip install .`)."""
    sys.exit(main())