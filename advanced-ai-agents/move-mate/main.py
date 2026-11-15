"""MoveMate — Multi-Agent Relocation Assistant.

A CLI tool that coordinates 5 specialized agents to produce a complete
relocation playbook. No API keys required — uses free public APIs.

Usage:
  python main.py --current-zip 10001 --new-zip 90210 --move-date 2025-12-15 \\
      --household-size 2br --renting
    
  python main.py --interactive   # Guided mode
"""

import argparse
import sys
from datetime import date, datetime
from models import MoveDetails
from orchestrator import run as run_orchestrator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MoveMate — multi-agent relocation assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Run in interactive guided mode")
    parser.add_argument("--current-zip", type=str,
                        help="Current address ZIP code")
    parser.add_argument("--new-zip", type=str,
                        help="New address ZIP code")
    parser.add_argument("--move-date", type=str,
                        help="Move date (YYYY-MM-DD)")
    parser.add_argument("--household-size", type=str,
                        choices=["studio", "1br", "2br", "3br", "house"],
                        default="1br",
                        help="Household size (default: 1br)")
    parser.add_argument("--renting", action="store_true",
                        help="Current property is rented (not owned)")
    parser.add_argument("-o", "--output", type=str,
                        help="Save playbook to file (default: print to stdout)")
    return parser.parse_args(argv)


def _interactive_mode() -> MoveDetails:
    """Collect move details interactively."""
    print("\n📦 MoveMate — Let's build your relocation playbook!\n")

    current_zip = input("Current ZIP code: ").strip()
    new_zip = input("New ZIP code: ").strip()

    while True:
        raw = input("Move date (YYYY-MM-DD): ").strip()
        try:
            move_date = datetime.strptime(raw, "%Y-%m-%d").date()
            break
        except ValueError:
            print("  Invalid date. Use YYYY-MM-DD format.\n")

    size_map = {"1": "studio", "2": "1br", "3": "2br", "4": "3br", "5": "house"}
    print("\nHousehold size:")
    for k, v in size_map.items():
        print(f"  {k}. {v}")
    choice = input("Choice (1-5): ").strip()
    household = size_map.get(choice, "1br")

    renting = input("\nAre you renting? (y/n): ").strip().lower() == "y"

    current_addr = input("\nCurrent full address (optional — for better results): ").strip()
    new_addr = input("New full address (optional — for better results): ").strip()

    return MoveDetails(
        current_zip=current_zip or "10001",
        new_zip=new_zip or "10002",
        move_date=move_date,
        household_size=household,
        is_renting=renting,
        current_address=current_addr or None,
        new_address=new_addr or None,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.interactive:
        details = _interactive_mode()
    else:
        if not args.current_zip or not args.new_zip or not args.move_date or not args.household_size:
            print("Error: --current-zip, --new-zip, --move-date, and --household-size are required")
            print("Run with --interactive for guided mode, or --help for full usage.")
            return 1

        try:
            move_date = datetime.strptime(args.move_date, "%Y-%m-%d").date()
        except ValueError:
            print("Error: move-date must be YYYY-MM-DD format")
            return 1

        if args.household_size not in ["studio", "1br", "2br", "3br", "house"]:
            print("Error: household-size must be one of: studio, 1br, 2br, 3br, house")
            return 1

        details = MoveDetails(
            current_zip=args.current_zip,
            new_zip=args.new_zip,
            move_date=move_date,
            household_size=args.household_size,
            is_renting=args.renting,
        )

    # Run the 5 agents
    print("\n🧠 Running MoveMate agents...\n")
    print("  🤖 Utility Scheduler...", end=" ", flush=True)
    playbook = run_orchestrator(details)
    print("done")
    print("  🤖 Address Changer... done")
    print("  🤖 Cost Estimator... done")
    print("  🤖 Neighborhood Scout... done")
    print("  🤖 Timeline Architect... done")
    print("\n✅ All agents complete!\n")

    # Output
    output = playbook.to_markdown()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"📝 Playbook saved to: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())