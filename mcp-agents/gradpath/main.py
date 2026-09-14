"""CLI entry point for GradPath.

Usage:
  # Interactive MCP stdio mode (for MCP clients like Claude Desktop)
  python main.py

  # HTTP SSE server (for HTTP clients)
  python main.py --http --port 8080

  # Direct CLI invocation (for quick testing)
  python main.py find --budget-max 15000 --state CA
  python main.py profile "State University of Technology"
  python main.py compare "State University of Technology" "Preston Liberal Arts College"
  python main.py earnings "State University of Technology" "Computer Science"

  # Force simulated mode (no API key needed)
  python main.py --simulate find --budget-max 20000
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="GradPath — find affordable US colleges with real outcome data."
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP SSE server instead of stdio.",
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)."
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host for HTTP server."
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Force simulated mode (use sample data, no API key needed).",
    )
    parser.add_argument(
        "--list-colleges",
        action="store_true",
        help="List all simulated colleges and exit.",
    )

    subparsers = parser.add_subparsers(dest="command")

    # find
    find_p = subparsers.add_parser("find", help="Search colleges by criteria.")
    find_p.add_argument("--budget-max", type=float, default=None)
    find_p.add_argument("--state", type=str, default="")
    find_p.add_argument("--major", type=str, default="")
    find_p.add_argument("--size-pref", type=str, default="")

    # profile
    profile_p = subparsers.add_parser("profile", help="Get college profile.")
    profile_p.add_argument("school_name", type=str)

    # compare
    compare_p = subparsers.add_parser("compare", help="Compare two colleges.")
    compare_p.add_argument("school1", type=str)
    compare_p.add_argument("school2", type=str)

    # earnings
    earn_p = subparsers.add_parser("earnings", help="Get earnings by program.")
    earn_p.add_argument("school", type=str)
    earn_p.add_argument("field_of_study", type=str)

    args = parser.parse_args()

    if args.simulate:
        os.environ["COLLEGE_SCORECARD_API_KEY"] = ""
        from src.scorecard import _is_simulated

    if args.list_colleges:
        from src.scorecard import _SAMPLE_COLLEGES, _row_to_college

        print("Simulated colleges:")
        for row in _SAMPLE_COLLEGES:
            c = _row_to_college(row)
            print(f"  {c.name:<35} {c.city:<20} {c.state}  net: ${c.net_price:,}" if c.net_price else "")
        return

    if args.command is None and not args.http:
        # Default: run MCP stdio server
        from server import run_stdio

        run_stdio()
        return

    if args.http:
        from server import run_sse

        run_sse(host=args.host, port=args.port)
        return

    import asyncio

    async def _run():
        if args.command == "find":
            from src.searcher import find_colleges

            result = await find_colleges(
                budget_max=args.budget_max,
                state=args.state,
                major=args.major,
                size_pref=args.size_pref,
            )
        elif args.command == "profile":
            from src.profile import college_profile

            result = await college_profile(args.school_name)
        elif args.command == "compare":
            from src.comparer import compare_colleges

            result = await compare_colleges(args.school1, args.school2)
        elif args.command == "earnings":
            from src.earnings import earnings_by_program

            result = await earnings_by_program(args.school, args.field_of_study)
        else:
            result = "Unknown command."
        print(result)

    asyncio.run(_run())


if __name__ == "__main__":
    main()