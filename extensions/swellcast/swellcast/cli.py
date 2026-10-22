"""SwellCast CLI entry point."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .geo import geocode
from .core import fetch_report, _wind_dir_label, WMO_CODES


def _fmt_temp(t: float | None) -> str:
    if t is None:
        return "--°C"
    return f"{t:.0f}°C"


def _fmt_wave(h: float | None) -> str:
    if h is None:
        return "--"
    return f"{h:.1f}m"


def _fmt_speed(s: float | None) -> str:
    if s is None:
        return "--"
    return f"{s:.0f} km/h"


def _fmt_wind_dir(deg: int | None, label: str) -> str:
    if deg is None:
        return "N/A"
    return f"{label} ({deg}°)"


def _weather_description(code: int | None) -> str:
    if code is None:
        return ""
    return WMO_CODES.get(code, f"Code {code}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="swellcast",
        description="Surf condition forecaster — wave height, swell period, wind data.",
        epilog="Powered by Open-Meteo Marine & Weather APIs (free, no key required).",
    )
    parser.add_argument("place", nargs="*", help="Place name (e.g. 'Santa Cruz') or lat lon")
    parser.add_argument("-d", "--days", type=int, default=5, help="Forecast days (default: 5)")
    parser.add_argument("--no-weather", action="store_true", help="Skip weather data")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    args = parser.parse_args()

    if args.version:
        print(f"swellcast v{__version__}")
        return

    if not args.place:
        parser.print_help()
        sys.exit(1)

    # Parse place: either "Place Name" or "lat lon"
    place_input = " ".join(args.place)

    location = None
    # Try lat/lon format
    parts = place_input.split()
    if len(parts) == 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            # Use a placeholder location
            from .models import Location
            location = Location(
                name=f"{lat:.4f}°N, {lon:.4f}°E" if lon >= 0 else f"{lat:.4f}°N, {abs(lon):.4f}°W",
                country="",
                lat=lat,
                lon=lon,
                timezone="UTC",
            )
        except ValueError:
            pass

    if location is None:
        # Geocode by place name
        location = geocode(place_input)
        if location is None:
            print(f"Error: Could not find location '{place_input}'. Try a different name or use lat/lon.", file=sys.stderr)
            sys.exit(1)

    print(f"{'─' * 48}")
    print(f"  SwellCast — {location.name}, {location.admin1}, {location.country}".rstrip(", "))
    print(f"  {location.lat:.4f}°N, {abs(location.lon):.4f}°{'W' if location.lon < 0 else 'E'}")
    print(f"{'─' * 48}")

    report = fetch_report(location, days=args.days)

    if not report.days:
        print("  No forecast data available.")
        sys.exit(1)

    for day in report.days:
        # Date header
        day_str = day.dt.strftime("%a %b %d")
        print(f"\n  {day_str} — Surf Score {day.score:.0f}/10 {day.score_label.split()[-1]}")

        # Wave info
        wave_info = f"  Waves: {_fmt_wave(day.wave_height_m)}"
        if day.wave_dir_deg is not None:
            wave_info += f" from {_wind_dir_label(day.wave_dir_deg)} ({day.wave_dir_deg}°)"
        if day.wave_period_s is not None:
            wave_info += f" · Period: {day.wave_period_s:.0f}s"
        print(wave_info)

        # Swell info (only if different from wave_height)
        if day.swell_height_m is not None and day.swell_height_m > 0:
            swell_info = f"  Swell: {_fmt_wave(day.swell_height_m)}"
            if day.swell_dir_deg is not None:
                swell_info += f" from {_wind_dir_label(day.swell_dir_deg)} ({day.swell_dir_deg}°)"
            if day.swell_period_s is not None:
                swell_info += f" · Period: {day.swell_period_s:.0f}s"
            print(swell_info)

        # Wind + temp
        weather_parts = []
        if day.wind_speed_kmh is not None:
            wind_info = f"Wind: {_fmt_speed(day.wind_speed_kmh)}"
            if day.wind_dir_deg is not None:
                wind_info += f" from {_wind_dir_label(day.wind_dir_deg)}"
            weather_parts.append(wind_info)
        if day.temp_max_c is not None:
            weather_parts.append(f"High: {_fmt_temp(day.temp_max_c)}")
        if day.weather_code is not None:
            desc = _weather_description(day.weather_code)
            if desc:
                weather_parts.append(desc)
        if weather_parts:
            print("  " + " · ".join(weather_parts))

        # Conditions note
        print(f"  Conditions: {day.conditions_note}")

    print("")


if __name__ == "__main__":
    main()