#!/usr/bin/env python3
"""HomeCourt — a playful AI judge for settling daily-life dilemmas.

Usage:
    python main.py --plead         Interactive mode: plead your case and get a verdict.
    python main.py --simulate      Demo mode: random case and persona, no input needed.
    python main.py --help          Show this help and exit.
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HomeCourt — a playful AI judge for daily-life dilemmas.",
    )
    parser.add_argument(
        "--plead",
        action="store_true",
        help="Interactive mode: plead your case and receive a formal verdict.",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Demo mode: runs with a random case and persona, no input needed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for HomeCourt."""
    load_dotenv()
    args = _parse_args(argv)

    if args.simulate:
        from src.court import run_simulated_demo
        run_simulated_demo()
    elif args.plead:
        from src.court import run_interactive_session
        run_interactive_session()
    else:
        # Default: show usage
        print("⚖️  HomeCourt — The AI Judge for Life's Tiny Battles")
        print()
        print("Usage:")
        print("  python main.py --plead       Plead your case interactively")
        print("  python main.py --simulate    Run a simulated demo")
        print("  python main.py --help        Show full help")
        print()
        print("Examples:")
        print("  python main.py --simulate")
        sys.exit(0)


if __name__ == "__main__":
    main()