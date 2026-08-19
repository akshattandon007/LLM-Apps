#!/usr/bin/env python3
"""AlphaBrief — CLI entry point.

Usage:
    python main.py --portfolio AAPL,MSFT,GOOGL --shares 10,15,5 --costs 150,200,180
    python main.py --simulate  # uses default portfolio with mock data

When --simulate is passed, all agents use mock data (no network calls).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from src.coordinator import Coordinator
from src.models import DailyBriefing

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("alphabrief")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AlphaBrief — Financial Intelligence Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --simulate\n"
            "  python main.py --portfolio AAPL,MSFT,NVDA --shares 10,10,5 --costs 150,200,400\n"
        ),
    )
    parser.add_argument(
        "--portfolio", type=str, default=None,
        help="Comma-separated tickers (e.g. AAPL,MSFT,GOOGL)",
    )
    parser.add_argument(
        "--shares", type=str, default=None,
        help="Comma-separated share counts (e.g. 10,15,5)",
    )
    parser.add_argument(
        "--costs", type=str, default=None,
        help="Comma-separated average costs (e.g. 150,200,180)",
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Use simulated/mock data — no real network calls",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write briefing markdown to file instead of stdout",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(argv)


def _resolve_portfolio(args: argparse.Namespace) -> tuple[list[str], list[float], list[float]]:
    """Resolve tickers, shares, and costs from args or env defaults."""
    if args.simulate:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"], [10, 10, 5, 8, 4], [150, 200, 180, 140, 400]

    default_portfolio = os.getenv("DEFAULT_PORTFOLIO", "AAPL,MSFT,GOOGL,AMZN,NVDA")

    tickers_str = args.portfolio or default_portfolio
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]

    shares = []
    if args.shares:
        shares = [float(s.strip()) for s in args.shares.split(",")]
    if len(shares) < len(tickers):
        shares = shares + [10.0] * (len(tickers) - len(shares))

    costs = []
    if args.costs:
        costs = [float(c.strip()) for c in args.costs.split(",")]
    if len(costs) < len(tickers):
        costs = costs + [150.0] * (len(tickers) - len(costs))

    return tickers[:max(len(tickers), len(shares))], shares[:len(tickers)], costs[:len(tickers)]


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    args = parse_args(argv)

    if args.verbose:
        logging.getLogger("alphabrief").setLevel(logging.DEBUG)

    tickers, shares, costs = _resolve_portfolio(args)

    if not tickers:
        logger.error("No tickers specified. Use --portfolio or set DEFAULT_PORTFOLIO in .env")
        return 1

    logger.info("AlphaBrief starting — %d holdings: %s", len(tickers), ", ".join(tickers))
    if args.simulate:
        logger.info("SIMULATED MODE — using mock data, no network calls")

    coordinator = Coordinator(tickers, shares, costs, simulate=args.simulate)

    if args.simulate:
        from tests.conftest import inject_mocks
        inject_mocks()

    try:
        briefing = coordinator.run()
    except Exception as exc:
        logger.error("Briefing generation failed: %s", exc, exc_info=True)
        return 1

    markdown = coordinator.to_markdown(briefing)

    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        logger.info("Briefing written to %s", args.output)
    else:
        print(markdown)

    logger.info("AlphaBrief complete — %d alerts generated", len(briefing.all_alerts))
    return 0


if __name__ == "__main__":
    sys.exit(main())