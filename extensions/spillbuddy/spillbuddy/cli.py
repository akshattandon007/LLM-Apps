"""SpillBuddy CLI — stain removal guide in your terminal."""

import argparse
import sys

from . import __version__
from .data import lookup, list_stains, list_fabrics, STAIN_DB


def format_result(result: dict) -> str:
    """Format a stain removal result for display."""
    lines = [
        f"🧴 SpillBuddy — {result['stain'].title()} on {result['fabric'].title()}",
        "",
        "📋 Method:",
        f"  {result['method']}",
        "",
        "⚠️  Caution:",
        f"  {result['caution']}",
    ]
    return "\n".join(lines)


def cmd_lookup(args: argparse.Namespace) -> None:
    """Handle the 'lookup' subcommand."""
    result = lookup(args.stain, args.fabric)
    if result:
        print(format_result(result))
    else:
        known = list_stains()
        print(f"❌ Stain type '{args.stain}' not found in database.")
        print(f"   Known stains: {', '.join(known)}")
        print("   Tip: use 'spillbuddy list' to see all stain types.")
        sys.exit(1)


def cmd_list(_args: argparse.Namespace) -> None:
    """Handle the 'list' subcommand."""
    print("🧺 SpillBuddy — Known Stain Types")
    print("=" * 40)
    for stain in list_stains():
        fabrics = list(STAIN_DB[stain].keys())
        fabric_str = ", ".join(f for f in fabrics if f != "all")
        print(f"\n• {stain.title()}")
        print(f"  Fabrics: {fabric_str}")
    print("\n" + "=" * 40)
    print(f"Total: {len(list_stains())} stain types")
    print("Tip: spillbuddy lookup <stain> <fabric>")


def cmd_interactive(_args: argparse.Namespace) -> None:
    """Run interactive mode."""
    print("🧴 SpillBuddy Interactive Mode")
    print("=" * 40)
    print("Type 'quit' to exit, 'list' to see stain types.\n")

    while True:
        stain = input("What did you spill? ").strip().lower()
        if stain in ("quit", "exit", "q"):
            break
        if stain == "list":
            print("Known stains:", ", ".join(list_stains()))
            continue
        if stain not in STAIN_DB:
            print(f"❌ Unknown stain '{stain}'.")
            print(f"Known stains: {', '.join(list_stains())}")
            print()
            continue

        fabric = input(f"On what fabric? ({', '.join(list_fabrics())}): ").strip().lower()
        if fabric in ("quit", "exit", "q"):
            break

        result = lookup(stain, fabric)
        if result:
            print()
            print(format_result(result))
            print()
        else:
            print(f"❌ No method found for {stain} on {fabric}.")
            print(f"   Try one of: {', '.join(list_fabrics())}")
            print()


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="spillbuddy",
        description="🧴 SpillBuddy — Stain removal guide for everyday spills",
        epilog="Example: spillbuddy lookup 'red wine' cotton",
    )
    parser.add_argument(
        "--version", action="version", version=f"SpillBuddy v{__version__}"
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # lookup subcommand
    p_lookup = sub.add_parser("lookup", help="Look up a stain removal method")
    p_lookup.add_argument("stain", help="Type of stain (e.g. 'red wine', 'coffee')")
    p_lookup.add_argument("fabric", help="Fabric type (e.g. cotton, silk, carpet)")

    # list subcommand
    sub.add_parser("list", help="List all known stain types")

    # interactive subcommand
    sub.add_parser("interactive", help="Interactive stain lookup mode")

    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "lookup":
        cmd_lookup(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "interactive":
        cmd_interactive(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()