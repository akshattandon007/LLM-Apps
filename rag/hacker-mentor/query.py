#!/usr/bin/env python3
"""
Query — search the FAISS index with a natural language query.

Usage:
    python query.py "What are common microservice pitfalls?"
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from embedder import Embedder
from vector_store import VectorStore


def format_result(score: float, doc: dict, rank: int) -> str:
    """Format a single result for display."""
    lines = []
    lines.append(f"\n  {'─' * 55}")
    lines.append(f"  {rank}. [Score: {score:.2f}] {doc.get('story_title', 'Untitled')[:70]}")
    lines.append(f"     {doc.get('hn_url', '')}")
    lines.append(f"     👤 {doc.get('author', '?')} · ⭐ {doc.get('points', 0)} · {doc.get('source', '?')}")

    text = doc.get("text", "")
    if len(text) > 300:
        text = text[:300] + "..."

    # Indent the text
    for line in text.split("\n"):
        lines.append(f"     {line}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Query the HN vector index")
    parser.add_argument("query", nargs="?", help="Natural language query")
    parser.add_argument("-k", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    store = VectorStore()
    if not store.load():
        print("❌ No index found. Run ingest.py first:")
        print("   python ingest.py --topic <topic> --limit 50")
        return

    print(f"📚 Loaded index with {store.size} documents\n")

    if args.interactive:
        print("🧠 Hacker Mentor — interactive mode (Ctrl+D to exit)")
        print()
        while True:
            try:
                q = input("🔍 Query: ").strip()
                if not q:
                    continue
            except (EOFError, KeyboardInterrupt):
                print()
                break

            _run_query(q, store, args.k)
            print()
    elif args.query:
        _run_query(args.query, store, args.k)
    else:
        parser.print_help()


def _run_query(query: str, store: VectorStore, k: int):
    embedder = Embedder()
    query_embedding = embedder.embed(query)
    results = store.search(query_embedding, k=k)

    if not results:
        print("  No results found.")
        return

    print(f"  {'─' * 55}")
    print(f"  Top {len(results)} HN Discussions")
    print(f"  {'─' * 55}")

    for i, (score, doc) in enumerate(results, 1):
        print(format_result(score, doc, i))
    print(f"\n  {'─' * 55}")


if __name__ == "__main__":
    main()
