#!/usr/bin/env python3
"""
Hacker Mentor — Main CLI entry point.

Combines ingest and query in one command.

Usage:
    # Ingest and query in two steps
    python hacker_mentor.py ingest --topic "python" --limit 30
    python hacker_mentor.py query "What are Python async best practices?"

    # Ingest only
    python hacker_mentor.py ingest --topic "microservices" --reindex

    # Query only
    python hacker_mentor.py query --interactive
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Hacker Mentor — HN Semantic Q&A")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Ingest subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Fetch HN data and build index")
    ingest_parser.add_argument("--topic", default="programming", help="Search topic")
    ingest_parser.add_argument("--limit", type=int, default=30, help="Number of stories")
    ingest_parser.add_argument("--reindex", action="store_true", help="Force rebuild")
    ingest_parser.add_argument("--comments", type=int, default=10, help="Comments per story")

    # Query subcommand
    query_parser = subparsers.add_parser("query", help="Search the index")
    query_parser.add_argument("query", nargs="?", help="Natural language query")
    query_parser.add_argument("-k", type=int, default=5, help="Number of results")
    query_parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.command == "ingest":
        from ingest import main as ingest_main
        # Rebuild args
        sys.argv = ["ingest.py", "--topic", args.topic,
                     "--limit", str(args.limit),
                     "--comments", str(args.comments)]
        if args.reindex:
            sys.argv.append("--reindex")
        ingest_main()
    elif args.command == "query":
        from query import main as query_main
        sys.argv = ["query.py"]
        if args.query:
            sys.argv.append(args.query)
        sys.argv.extend(["-k", str(args.k)])
        if args.interactive:
            sys.argv.append("--interactive")
        query_main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
