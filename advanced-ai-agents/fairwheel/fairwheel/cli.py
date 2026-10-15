"""CLI entry point for FairWheel."""

from __future__ import annotations

import argparse
import sys

from .models import VehicleQuery
from .orchestrator import run_pipeline
from .report import render_markdown


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fairwheel",
        description="FairWheel — multi-agent car-purchase advisor. Researches NHTSA safety, complaints, recalls, and real MPG, then gives a WORTH IT / WAIT / AVOID verdict with negotiation talking points.",
    )
    parser.add_argument("--year", type=int, default=None, help="Model year, e.g. 2021")
    parser.add_argument("--make", type=str, default=None, help="Make, e.g. Honda")
    parser.add_argument("--model", type=str, default=None, help="Model, e.g. Accord")
    parser.add_argument("--budget", type=float, default=None, help="Purchase budget in USD (optional)")
    parser.add_argument("--annual-miles", type=int, default=12_000, help="Miles driven per year (default 12000)")
    parser.add_argument("--fuel-price", type=float, default=3.50, help="USD per gallon (default 3.50)")
    parser.add_argument("--family-size", type=int, default=1, help="Household size (default 1)")
    parser.add_argument("--commute-miles", type=int, default=None, help="Daily one-way commute miles (optional)")
    parser.add_argument("--demo", action="store_true", help="Force simulated data (no network)")
    parser.add_argument("--output", type=str, default=None, help="Write the report to this markdown file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Interactive prompt when vehicle args are missing.
    year = args.year
    make = args.make
    model = args.model
    if not (year and make and model):
        print("FairWheel — car purchase advisor. Enter vehicle details (or use flags).")
        try:
            if not year:
                year = int(input("  Model year: ").strip())
            if not make:
                make = input("  Make: ").strip()
            if not model:
                model = input("  Model: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNo input provided. Use: python -m fairwheel --year 2021 --make Honda --model Accord")
            return 1

    query = VehicleQuery(
        year=int(year),
        make=make,
        model=model,
        budget=args.budget,
        annual_miles=args.annual_miles,
        fuel_price=args.fuel_price,
        family_size=args.family_size,
        commute_miles=args.commute_miles,
    )

    report = run_pipeline(query, demo=args.demo)
    markdown = render_markdown(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        print(f"Report written to {args.output}")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())