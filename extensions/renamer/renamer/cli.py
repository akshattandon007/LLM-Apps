#!/usr/bin/env python3
"""Renamer CLI — batch file renaming from the terminal."""

import argparse
import sys
from pathlib import Path

from renamer import __version__
from renamer.core import history, preview, rename, undo


def positive_int(value: str) -> int:
    try:
        n = int(value)
        if n < 1:
            raise ValueError
        return n
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got '{value}'")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="renamer",
        description="Batch file renamer — regex patterns, number sequences, dry-run preview.",
    )
    parser.add_argument(
        "--version", action="version", version=f"renamer {__version__}"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # rename
    rp = sub.add_parser("rename", help="Rename files matching a pattern")
    rp.add_argument("directory", help="Directory containing files to rename")
    rp.add_argument("pattern", help="Regex pattern to match in filenames")
    rp.add_argument(
        "replacement",
        help="Replacement string. Use {n} for counter, {n:3} for zero-padded.",
    )
    rp.add_argument(
        "-r", "--recursive", action="store_true", help="Search subdirectories"
    )
    rp.add_argument(
        "-e", "--ext", metavar="EXT", help="Only rename files with this extension"
    )
    rp.add_argument(
        "--start", type=positive_int, default=1, help="Starting counter value (default: 1)"
    )
    rp.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without renaming",
    )

    # preview (alias for rename --dry-run, but explicit)
    pp = sub.add_parser("preview", help="Preview rename without executing")
    pp.add_argument("directory", help="Directory containing files to rename")
    pp.add_argument("pattern", help="Regex pattern to match in filenames")
    pp.add_argument("replacement", help="Replacement string with {n} for counter")
    pp.add_argument("-r", "--recursive", action="store_true")
    pp.add_argument("-e", "--ext", metavar="EXT")
    pp.add_argument("--start", type=positive_int, default=1)

    # undo
    up = sub.add_parser("undo", help="Undo the last rename operation")
    up.add_argument(
        "count",
        nargs="?",
        type=positive_int,
        default=1,
        help="Number of operations to undo (default: 1)",
    )

    # history
    sub.add_parser("history", help="Show recent rename operations")

    return parser


def print_results(results, dry_run: bool = False) -> None:
    if not results:
        print("No files to rename.")
        return

    label = "Would rename" if dry_run else "Renamed"
    renamed = [r for r in results if r[2]]
    skipped = [r for r in results if not r[2]]

    for src, dest, ok in renamed:
        print(f"  ✓  {src.name} → {dest.name}")
    for src, dest, ok in skipped:
        print(f"  ⚠  COLLISION: {src.name} → {dest.name} (skipped)")

    print(f"\n{label} {len(renamed)} file{'s' if len(renamed) != 1 else ''}.")
    if skipped:
        print(f"Skipped {len(skipped)} collision{'s' if len(skipped) != 1 else ''}.")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "rename":
        results = rename(
            directory=args.directory,
            pattern=args.pattern,
            replacement=args.replacement,
            recursive=args.recursive,
            file_ext=args.ext,
            start_num=args.start,
            dry_run=args.dry_run,
        )
        print_results(results, dry_run=args.dry_run)

    elif args.command == "preview":
        results = preview(
            directory=args.directory,
            pattern=args.pattern,
            replacement=args.replacement,
            recursive=args.recursive,
            file_ext=args.ext,
            start_num=args.start,
        )
        print_results(results, dry_run=True)

    elif args.command == "undo":
        count = undo(limit=args.count)
        if count:
            print(f"\nUndid {count} operation{'s' if count != 1 else ''}.")

    elif args.command == "history":
        history()


if __name__ == "__main__":
    main()