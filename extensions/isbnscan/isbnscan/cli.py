"""
CLI interface for isbnscan — batch ISBN lookup tool.

Usage:
  isbnscan 9780141036144 9780061120084
  isbnscan --file isbns.txt
  isbnscan 9780141036144 --csv results.csv
"""

import argparse
import sys
from pathlib import Path

from .lookup import (
    batch_lookup,
    clean_isbn,
    is_valid_isbn,
    normalize_isbn,
    results_to_csv,
)


def read_isbns_from_file(path: str) -> list[str]:
    """Read ISBNs from a file (one per line, ignores blank/comment lines)."""
    isbns = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            isbns.append(line)
    return isbns


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI color codes if stdout is a terminal."""
    if not sys.stdout.isatty():
        return text
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_table(results, csv_path: str | None = None) -> None:
    """Print formatted results table to stdout."""
    found_count = sum(1 for r in results if r.found)
    total = len(results)

    print(colorize(f"\n{'='*80}", "cyan"))
    print(colorize(f"  ISBN LOOKUP RESULTS — {found_count}/{total} found", "bold"))
    print(colorize(f"{'='*80}", "cyan"))

    for i, r in enumerate(results, 1):
        status = colorize("✓ FOUND", "green") if r.found else colorize("✗ NOT FOUND", "red")
        print(f"\n{colorize(f'[{i}]', 'cyan')} {r.isbn} — {status}")

        if r.found:
            print(f"  {colorize('Title:', 'yellow')}    {r.title}")
            if r.authors:
                print(f"  {colorize('Authors:', 'yellow')}  {r.authors}")
            if r.publisher:
                print(f"  {colorize('Publisher:', 'yellow')} {r.publisher}")
            if r.publish_year:
                print(f"  {colorize('Year:', 'yellow')}     {r.publish_year}")
            if r.page_count:
                print(f"  {colorize('Pages:', 'yellow')}    {r.page_count}")
            if r.subjects:
                print(f"  {colorize('Subjects:', 'yellow')} {r.subjects}")
        else:
            print(f"  {colorize('No metadata found for this ISBN.', 'red')}")

    print(colorize(f"\n{'='*80}", "cyan"))
    print(f"  Summary: {found_count}/{total} ISBNs resolved")
    if csv_path:
        print(f"  CSV export: {csv_path}")
    print(colorize(f"{'='*80}\n", "cyan"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="isbnscan",
        description="Batch ISBN lookup tool — resolve ISBNs to book metadata via the Open Library API.",
        epilog="Examples:\n"
               "  isbnscan 9780141036144 9780061120084\n"
               "  isbnscan --file isbns.txt\n"
               "  isbnscan --file isbns.txt --csv results.csv\n"
               "  cat isbns.txt | isbnscan --stdin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("isbns", nargs="*", help="One or more ISBNs to look up")
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a file with one ISBN per line",
    )
    parser.add_argument(
        "--csv", "-c",
        type=str,
        help="Export results to a CSV file at this path",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read ISBNs from stdin (one per line)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args(argv)

    if args.version:
        from . import __version__
        print(f"isbnscan v{__version__}")
        return 0

    isbns: list[str] = []

    # Collect ISBNs from args
    if args.isbns:
        isbns.extend(args.isbns)

    # Collect from file
    if args.file:
        file_isbns = read_isbns_from_file(args.file)
        isbns.extend(file_isbns)

    # Collect from stdin
    if args.stdin or (not args.isbns and not args.file and not sys.stdin.isatty()):
        stdin_isbns = [line.strip() for line in sys.stdin if line.strip()]
        isbns.extend(stdin_isbns)

    if not isbns:
        parser.print_help()
        return 1

    # Clean and validate ISBNs
    valid: list[str] = []
    invalid: list[str] = []
    for raw in isbns:
        cleaned = normalize_isbn(raw)
        if is_valid_isbn(cleaned):
            valid.append(cleaned)
        else:
            invalid.append(raw)

    if invalid:
        print(colorize(f"\n⚠ Warning: {len(invalid)} invalid ISBN(s) skipped:", "yellow"))
        for inv in invalid:
            print(f"  {inv}")
        print()

    if not valid:
        print(colorize("Error: No valid ISBNs to look up.", "red"))
        return 1

    print(colorize(f"\nLooking up {len(valid)} ISBN(s) via Open Library API...", "cyan"))

    results = batch_lookup(valid)
    print_table(results, csv_path=args.csv)

    if args.csv:
        results_to_csv(results, args.csv)
        print(f"CSV written to: {args.csv}")

    return 0
