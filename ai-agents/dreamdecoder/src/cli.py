"""CLI entry point — argument parsing and command dispatch."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from . import journal, engine
from .display import (
    print_entry,
    print_entry_list,
    print_stats,
    print_welcome,
    print_success,
)
from .models import DreamEntry, DreamInterpretation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dreamdecoder",
        description="🌙 DreamDecoder — AI-powered dream journal and interpreter",
        epilog="Record your dreams, understand their symbols, and discover patterns over time.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # log
    log_p = sub.add_parser("log", help="Record a new dream and get interpretation")
    log_p.add_argument("text", nargs="+", help="Describe your dream")
    log_p.add_argument("--tag", "-t", action="append", default=[], help="Add tags")

    # list
    sub.add_parser("list", help="Browse all journal entries")

    # view
    view_p = sub.add_parser("view", help="View a specific entry by ID")
    view_p.add_argument("entry_id", help="Entry ID (from list)")

    # search
    search_p = sub.add_parser("search", help="Search entries by keyword")
    search_p.add_argument("query", help="Keyword or phrase to search")

    # stats
    sub.add_parser("stats", help="Show dream pattern insights")

    # delete
    delete_p = sub.add_parser("delete", help="Delete an entry by ID")
    delete_p.add_argument("entry_id", help="Entry ID to delete")
    delete_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # clear
    clear_p = sub.add_parser("clear", help="Delete ALL entries")
    clear_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    return parser


def cmd_log(text: str, tags: list[str]) -> None:
    """Record a dream, get interpretation, save, and display."""
    dream_text = " ".join(text)

    print("\n  🔮  Analyzing your dream...")
    interp = engine.interpret(dream_text)

    entry = DreamEntry(
        dream_text=dream_text,
        tags=tags,
    )
    if interp:
        entry.interpretation = interp

    journal.save_entry(entry)
    print_success("Dream recorded and interpreted!", f"Entry ID: {entry.id}")
    print_entry(entry, detailed=True)


def cmd_list() -> None:
    entries = journal.load_all()
    print_entry_list(entries)


def cmd_view(entry_id: str) -> None:
    entry = journal.get_entry(entry_id)
    if not entry:
        print(f"\n  ❌  No entry found with ID '{entry_id}'.")
        print("     Use 'list' to see available entries.\n")
        sys.exit(1)
    print_entry(entry, detailed=True)


def cmd_search(query: str) -> None:
    results = journal.search_entries(query)
    if not results:
        print(f"\n  🔍  No entries match '{query}'.\n")
        return
    print(f"\n  🔍  Search results for: '{query}'")
    print_entry_list(results)


def cmd_stats() -> None:
    s = journal.compute_stats()
    print_stats(s)


def cmd_delete(entry_id: str, force: bool) -> None:
    entry = journal.get_entry(entry_id)
    if not entry:
        print(f"\n  ❌  No entry found with ID '{entry_id}'.\n")
        sys.exit(1)
    if not force:
        print(f"\n  ⚠️   About to delete entry {entry_id}:")
        print(f"      \"{entry.dream_text[:80]}...\"")
        resp = input("  Confirm? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("  Cancelled.\n")
            return
    if journal.delete_entry(entry_id):
        print_success("Entry deleted.", entry_id)
    else:
        print("\n  ❌  Failed to delete entry.\n")


def cmd_clear(force: bool) -> None:
    count = len(journal.load_all())
    if count == 0:
        print("\n  📭  No entries to clear.\n")
        return
    if not force:
        print(f"\n  ⚠️   This will DELETE all {count} journal entries. Are you sure?")
        resp = input("  Type 'yes' to confirm: ").strip().lower()
        if resp != "yes":
            print("  Cancelled.\n")
            return
    removed = journal.clear_all()
    print_success(f"Cleared {removed} entr{'y' if removed == 1 else 'ies'}.")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command or args.command == "help":
        print_welcome()
        parser.print_help()
        return

    dispatch = {
        "log": lambda: cmd_log(args.text, args.tag),
        "list": lambda: cmd_list(),
        "view": lambda: cmd_view(args.entry_id),
        "search": lambda: cmd_search(args.query),
        "stats": lambda: cmd_stats(),
        "delete": lambda: cmd_delete(args.entry_id, args.force),
        "clear": lambda: cmd_clear(args.force),
    }

    dispatch[args.command]()


if __name__ == "__main__":
    main()