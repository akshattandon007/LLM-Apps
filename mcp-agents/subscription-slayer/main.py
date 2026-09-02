#!/usr/bin/env python3
"""Subscription Slayer — CLI entry point for testing.

Usage:
    python main.py <command> [args]

Commands:
    scan <csv_path>              — Scan a bank statement CSV
    scan-text <csv_text>         — Parse raw CSV text
    detect-recurring <csv_path>  — Scan + detect recurring charges
    categorize <csv_path>        — Full pipeline: scan → detect → categorize
    annual-cost <csv_path>       — Full pipeline + annual cost summary
    cancel <service_name>        — Get cancellation info for a service
    known                        — List known subscription merchants
    pipeline <csv_path>          — Run full pipeline end-to-end
"""

import json
import os
import sys
from datetime import date

from src.canceller import get_cancellation_info, list_known_merchants
from src.categorizer import categorize, detect_recurring, estimate_annual_cost
from src.models import CategorizedSub, Charge, Subscription
from src.scanner import scan_statements


def _load_charges_from_csv(csv_path: str) -> list[Charge]:
    """Scan CSV and return charges."""
    result = scan_statements(csv_path)
    if result.errors:
        print("Warnings:")
        for e in result.errors:
            print(f"  {e}")
    print(f"  → {result.total_transactions} transactions found\n")
    return result.charges


def cmd_scan(csv_path: str) -> None:
    """Scan and display charges."""
    charges = _load_charges_from_csv(csv_path)
    for c in charges:
        print(f"{c.transaction_date}  ${c.amount:>7.2f}  {c.description[:50]:50s}  [{c.merchant or 'unknown'}]")


def cmd_detect_recurring(csv_path: str) -> None:
    """Scan and detect recurring subscriptions."""
    charges = _load_charges_from_csv(csv_path)
    subs = detect_recurring(charges)
    print(f"→ {len(subs)} recurring subscriptions detected:\n")
    for s in subs:
        freq = s.frequency.value if s.frequency else "?"
        print(f"  {s.merchant:25s} ${s.amount:>7.2f}/{freq:10s}  ({s.occurrences}x, last: {s.last_seen})")


def cmd_categorize(csv_path: str) -> None:
    """Full pipeline: scan → detect → categorize."""
    charges = _load_charges_from_csv(csv_path)
    subs = detect_recurring(charges)
    cats = categorize(subs)
    print(f"→ {len(cats)} categorized subscriptions:\n")
    for c in cats:
        cat_label = c.category.value.replace("_", " ").title()
        print(f"  [{cat_label:18s}] {c.merchant:25s} ${c.amount:>7.2f}/{c.frequency.value:8s}  ${c.annual_cost:>7.2f}/yr")


def cmd_annual(csv_path: str) -> None:
    """Full pipeline + annual cost summary."""
    charges = _load_charges_from_csv(csv_path)
    subs = detect_recurring(charges)
    cats = categorize(subs)
    print(estimate_annual_cost(cats))


def cmd_cancel(service_name: str) -> None:
    """Get cancellation info."""
    print(get_cancellation_info(service_name))


def cmd_known() -> None:
    """List known merchants."""
    print("Known subscription merchants:")
    for name in list_known_merchants():
        print(f"  • {name}")


def cmd_pipeline(csv_path: str) -> None:
    """Run full pipeline end-to-end."""
    charges = _load_charges_from_csv(csv_path)
    if not charges:
        print("No transactions found. Check the file path and format.")
        return

    # Step 1: Detect recurring
    subs = detect_recurring(charges)
    print(f"\n{'='*60}")
    print(f"STEP 2: Detected {len(subs)} recurring subscriptions")
    print(f"{'='*60}")
    for s in subs:
        print(f"  {s.merchant:25s} ${s.amount:>7.2f}/{s.frequency.value:10s}  ({s.occurrences}x)")

    # Step 2: Categorize
    cats = categorize(subs)
    print(f"\n{'='*60}")
    print("STEP 3: Categorized subscriptions")
    print(f"{'='*60}")
    for c in cats:
        cat_label = c.category.value.replace("_", " ").title()
        print(f"  [{cat_label:18s}] {c.merchant:25s} ${c.annual_cost:>7.2f}/yr")

    # Step 3: Annual cost
    print(f"\n{'='*60}")
    print("STEP 4: Annual cost estimate")
    print(f"{'='*60}")
    print(estimate_annual_cost(cats))

    # Step 4: Cancellation info for known services
    print(f"{'='*60}")
    print("STEP 5: Cancellation info (known services)")
    print(f"{'='*60}")
    for c in cats:
        info = get_cancellation_info(c.merchant)
        print(f"\n{info}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "scan": cmd_scan,
        "scan-text": lambda _: print("Use server.py for CSV text scanning."),
        "detect-recurring": cmd_detect_recurring,
        "categorize": cmd_categorize,
        "annual-cost": cmd_annual,
        "cancel": cmd_cancel,
        "known": lambda _: cmd_known(),
        "pipeline": cmd_pipeline,
    }

    handler = commands.get(command)
    if not handler:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    if command == "known":
        handler(None)
    elif command == "cancel" and len(sys.argv) >= 3:
        handler(sys.argv[2])
    else:
        if len(sys.argv) < 3:
            print(f"Usage: python main.py {command} <path/service>")
            sys.exit(1)
        handler(sys.argv[2])


if __name__ == "__main__":
    main()