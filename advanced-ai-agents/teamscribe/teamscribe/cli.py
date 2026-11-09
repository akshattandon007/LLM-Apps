"""Command-line interface for TeamScribe."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from teamscribe.models import MeetingRecord, ActionItem, Decision
from teamscribe.orchestrator import Orchestrator
from teamscribe.storage import Storage


def build_record_from_args(args: argparse.Namespace) -> MeetingRecord:
    """Build a MeetingRecord from CLI arguments."""
    return MeetingRecord(
        title=args.title,
        date=args.date or date.today().isoformat(),
        participants=[p.strip() for p in args.participants.split(",")] if args.participants else [],
        raw_notes=args.notes,
    )


def cmd_process(args: argparse.Namespace) -> None:
    """Process a meeting through the multi-agent pipeline."""
    record = build_record_from_args(args)
    orch = Orchestrator(model=args.model, archive_path=args.archive)
    record = orch.run(record)
    storage = Storage()
    path = storage.save(record)
    print(f"\n📁 Saved to: {path}")
    print(f"\n📋 Summary:\n{record.summary[:500]}..." if len(record.summary) > 500 else f"\n📋 Summary:\n{record.summary}")
    if record.action_items:
        print(f"\n✅ Action Items ({len(record.action_items)}):")
        for a in record.action_items:
            dl = f" (by {a.deadline})" if a.deadline else ""
            print(f"   ☐ {a.owner}: {a.description}{dl}")


def cmd_list(args: argparse.Namespace) -> None:
    """List saved meetings."""
    storage = Storage()
    meetings = storage.list_meetings()
    if not meetings:
        print("No meetings found in storage.")
        return
    print(f"📁 Saved Meetings ({len(meetings)}):")
    for m in meetings:
        print(f"   {m['date']}  {m['title']}  [{m['decisions']} decisions, {m['actions']} actions]")


def cmd_show(args: argparse.Namespace) -> None:
    """Show a saved meeting record."""
    storage = Storage()
    record = storage.load(args.path)
    if not record:
        print(f"Error: meeting not found at {args.path}")
        sys.exit(1)
    print(record.to_json())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TeamScribe — Multi-agent meeting companion",
    )
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--archive", default=None, help="Archive file path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # process
    p = subparsers.add_parser("process", help="Process meeting notes")
    p.add_argument("title", help="Meeting title")
    p.add_argument("notes", help="Raw meeting notes (text)")
    p.add_argument("--participants", "-p", default="", help="Comma-separated participant names")
    p.add_argument("--date", "-d", default="", help="Meeting date (YYYY-MM-DD)")
    p.set_defaults(func=cmd_process)

    # list
    subparsers.add_parser("list", help="List saved meetings").set_defaults(func=cmd_list)

    # show
    p = subparsers.add_parser("show", help="Show a saved meeting")
    p.add_argument("path", help="Path to meeting JSON file")
    p.set_defaults(func=cmd_show)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()