"""WhatToWatch CLI — test the MCP server tools locally."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.schedule import whats_on_right_now, whats_on_tonight, daily_schedule
from src.search import search_show, search_by_genre
from src.recommendations import find_similar_shows
from src.tvmaze import TVMazeClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WhatToWatch — TV schedule and streaming recommender"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # whats_on
    p = sub.add_parser("right-now", help="What's airing right now")
    p.add_argument("--country", default="US", help="Country code (US, GB, etc.)")
    p.add_argument("--genre", help="Filter by genre")

    p = sub.add_parser("tonight", help="What's on in primetime")
    p.add_argument("--country", default="US", help="Country code (US, GB, etc.)")
    p.add_argument("--genre", help="Filter by genre")

    p = sub.add_parser("schedule", help="Full day schedule")
    p.add_argument("--date", default=None, help="Date YYYY-MM-DD")
    p.add_argument("--country", default="US", help="Country code (US, GB, etc.)")

    p = sub.add_parser("search", help="Search for a show")
    p.add_argument("query", help="Show name to search")

    p = sub.add_parser("similar", help="Find similar shows")
    p.add_argument("show_name", help="Show you like")

    p = sub.add_parser("genre", help="Discover shows by genre")
    p.add_argument("genre", help="Genre (comedy, drama, sci-fi, etc.)")
    p.add_argument("--limit", type=int, default=10, help="Max results")

    args = parser.parse_args()
    client = TVMazeClient()

    try:
        if args.command == "right-now":
            result = whats_on_right_now(client, country=args.country, genre=args.genre)
        elif args.command == "tonight":
            result = whats_on_tonight(client, genre=args.genre, country=args.country)
        elif args.command == "schedule":
            result = daily_schedule(client, date=args.date, country=args.country)
        elif args.command == "search":
            result = search_show(client, query=args.query)
        elif args.command == "similar":
            result = find_similar_shows(client, show_name=args.show_name)
        elif args.command == "genre":
            result = search_by_genre(client, genre=args.genre, limit=args.limit)
        else:
            parser.print_help()
            sys.exit(1)

        print(result)
    finally:
        client.close()


if __name__ == "__main__":
    main()