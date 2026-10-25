#!/usr/bin/env python3
"""SafeRide CLI — pre-trip safety check in one command.

Usage:
    saferide                     # Interactive mode
    saferide "Toyota" "Camry" 2020 "New York, NY" "Los Angeles, CA"
    saferide "Honda" "Civic" 2019 "Chicago, IL" "Miami, FL" -w "Nashville, TN" "Atlanta, GA"
    saferide --vin 1HGCM82633A004352 "Boston, MA" "Washington, DC"
"""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from saferide.coordinator import run_full_check


console = Console()


def _print_report(report) -> None:
    """Render the trip report to the console."""
    # Verdict
    console.print()
    console.print(Panel.fit(
        f"[bold]{report.verdict}[/bold]",
        border_style="green" if "All clear" in report.verdict else "yellow",
    ))
    console.print()

    # Vehicle section
    v = report.vehicle
    vehicle_title = f"🚗 Vehicle: {v.year} {v.make} {v.model}"
    if v.vin:
        vehicle_title += f" (VIN: {v.vin})"

    if v.status == "recall_found":
        table = Table(title="Open Recalls", border_style="red")
        table.add_column("ID", style="dim")
        table.add_column("Component", style="bold")
        table.add_column("Severity")
        table.add_column("Summary", max_width=60)
        table.add_column("Remedy")

        for r in v.recalls:
            severity_style = {
                "critical": "red bold",
                "high": "yellow bold",
                "medium": "yellow",
                "low": "green",
            }.get(r.safety_risk, "")
            table.add_row(
                r.nhtsa_id,
                r.component,
                Text(r.safety_risk.upper(), style=severity_style),
                r.summary[:120] + ("…" if len(r.summary) > 120 else ""),
                r.remedy[:80] + ("…" if len(r.remedy) > 80 else ""),
            )
        console.print(Panel(table, title=vehicle_title, border_style="red"))
    else:
        console.print(Panel(
            f"[green]✅ {v.message}[/green]",
            title=vehicle_title,
            border_style="green",
        ))

    console.print()

    # Weather section
    w = report.weather
    weather_style = {
        "good": "green",
        "moderate": "yellow",
        "caution": "orange1",
        "avoid": "red",
    }.get(w.overall_rating, "white")

    table = Table(title="Route Weather", border_style=weather_style)
    table.add_column("Location", style="bold")
    table.add_column("Temp")
    table.add_column("Conditions")
    table.add_column("Wind")
    table.add_column("Visibility")
    table.add_column("Hazard", style="red bold")

    def _row(fc):
        return [
            fc.location,
            f"{fc.temp_c:.0f}°C (feels {fc.feels_like_c:.0f}°C)",
            fc.condition.title(),
            f"{fc.wind_speed_kmh:.0f} km/h (gust {fc.wind_gust_kmh:.0f})",
            f"{fc.visibility_km:.1f} km",
            "⚠️ " + fc.hazard_note[:60] + ("…" if len(fc.hazard_note) > 60 else "") if fc.hazard else "✅ Clear",
        ]

    table.add_row(*_row(w.origin_forecast))
    for wp in w.waypoint_forecasts:
        table.add_row(*_row(wp))
    table.add_row(*_row(w.destination_forecast))

    console.print(Panel(table, border_style=weather_style))

    # Summary
    console.print()
    console.print("[bold]📋 Route Summary[/bold]")
    console.print(report.summary)
    console.print()

    # Final verdict again
    console.print(Panel.fit(report.verdict, border_style="green" if "All clear" in report.verdict else "yellow"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SafeRide — Multi-agent pre-trip safety check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  saferide                              # Interactive mode\n"
            '  saferide "Toyota" "Camry" 2020 "NYC" "LA"\n'
            '  saferide --vin 1HGCM82633A004352 "Boston" "DC"\n'
            '  saferide "Honda" "Civic" 2019 "Chicago" "Miami" -w "Nashville"'
        ),
    )
    parser.add_argument("make", nargs="?", help="Vehicle make (e.g. Toyota)")
    parser.add_argument("model", nargs="?", help="Vehicle model (e.g. Camry)")
    parser.add_argument("year", nargs="?", type=int, help="Vehicle year (e.g. 2020)")
    parser.add_argument("origin", nargs="?", help="Trip origin location")
    parser.add_argument("destination", nargs="?", help="Trip destination location")
    parser.add_argument("--vin", help="Vehicle VIN (17 characters) — overrides make/model/year")
    parser.add_argument("-w", "--waypoints", nargs="*", default=None, help="Optional waypoints")
    parser.add_argument("--demo", action="store_true", help="Run with simulated/demo data")

    args = parser.parse_args()

    # Interactive mode if not enough args
    interactive = not all([args.make, args.model, args.year, args.origin, args.destination]) and not args.vin

    if interactive:
        console.print(Panel.fit("[bold]🚗 SafeRide — Pre-Trip Safety Check[/bold]\n"
                                "Let's check your vehicle and route before you go."))
        console.print()

        has_vin = console.input("Do you have a VIN? (y/n): ").strip().lower() == "y"
        if has_vin:
            args.vin = console.input("Enter VIN (17 chars): ").strip()
        else:
            args.make = console.input("Vehicle make (e.g. Toyota): ").strip()
            args.model = console.input("Vehicle model (e.g. Camry): ").strip()
            args.year = int(console.input("Vehicle year (e.g. 2020): ").strip())

        args.origin = console.input("Trip origin (e.g. 'New York, NY'): ").strip()
        args.destination = console.input("Trip destination (e.g. 'Los Angeles, CA'): ").strip()
        wp_input = console.input("Waypoints (comma-separated, or Enter for none): ").strip()
        args.waypoints = [w.strip() for w in wp_input.split(",")] if wp_input else None

    console.print("[dim]Running SafeRide multi-agent check...[/dim]")

    # Run the multi-agent pipeline
    report = run_full_check(
        make=args.make or "Toyota",
        model=args.model or "Camry",
        year=args.year or 2020,
        origin=args.origin or "New York, NY",
        destination=args.destination or "Los Angeles, CA",
        waypoints=args.waypoints,
        vin=args.vin,
    )

    _print_report(report)


if __name__ == "__main__":
    main()