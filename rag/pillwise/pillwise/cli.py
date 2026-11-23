#!/usr/bin/env python3
"""PillWise CLI — Medication Information Assistant powered by RAG.

Usage:
    pillwise fetch           Fetch drug labels from OpenFDA
    pillwise index           Build/rebuild the semantic index
    pillwise ask QUERY       Ask a question about medications
    pillwise search QUERY    Show raw retrieval results
    pillwise info            Show index stats

Examples:
    pillwise fetch --limit 100
    pillwise index
    pillwise ask "What are the side effects of ibuprofen?"
    pillwise ask "Can I take aspirin with blood pressure medication?"
    pillwise search "acetaminophen dosage adults"
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for standalone use
PARENT = Path(__file__).resolve().parent.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from pillwise.fetcher import fetch_drug_labels, save_labels, load_labels, prepare_chunks
from pillwise.indexer import build_index, search
from pillwise.generator import generate


def cmd_fetch(args):
    """Fetch drug labels from OpenFDA."""
    print(f"Fetching {args.limit} drug labels from OpenFDA...")
    records = fetch_drug_labels(limit=args.limit, skip=args.skip)
    path = save_labels(records)
    print(f"Done. {len(records)} labels saved to {path}")
    return 0


def cmd_index(args):
    """Build the FAISS semantic index."""
    records = load_labels()
    if not records:
        print("No drug labels found. Run 'pillwise fetch' first.")
        return 1
    print(f"Loaded {len(records)} drug labels.")
    chunks = prepare_chunks(records, chunk_size=args.chunk_size)
    print(f"Created {len(chunks)} searchable chunks.")
    index, texts, metadata = build_index(chunks, force_rebuild=True)
    print(f"Index ready: {len(texts)} chunks indexed.")
    return 0


def cmd_ask(args):
    """Ask a question and get a plain-language answer."""
    records = load_labels()
    if not records:
        print("No drug labels found. Run 'pillwise fetch' first.")
        return 1

    chunks = prepare_chunks(records)
    index, texts, metadata = build_index(chunks)

    query = args.query
    results = search(index, texts, metadata, query, k=args.k)

    if not results:
        print("No relevant information found.")
        return 0

    if args.raw:
        # Just show retrieval results
        for r in results:
            print(f"\n[{r['score']:.3f}] {r['source']}")
            print(f"    {r['text'][:300]}...")
        return 0

    answer = generate(
        query=query,
        results=results,
        hf_token=args.token,
        use_local=args.local,
    )
    print(answer)
    return 0


def cmd_info(args):
    """Show index statistics."""
    records = load_labels()
    if records:
        chunks = prepare_chunks(records)
        index, texts, metadata = build_index(chunks)
        brands = set(m["drug_name"] for m in metadata if m.get("drug_name"))
        print(f"Drug labels: {len(records)}")
        print(f"Indexed chunks: {len(texts)}")
        print(f"Unique drugs: {len(brands)}")
        print(f"Sample drugs: {', '.join(sorted(brands)[:10])}")
    else:
        print("No data. Run 'pillwise fetch' first.")


def main():
    parser = argparse.ArgumentParser(
        description="PillWise — RAG over FDA drug labels for plain-language medication answers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch drug labels from OpenFDA")
    p_fetch.add_argument("--limit", type=int, default=100, help="Number of labels to fetch")
    p_fetch.add_argument("--skip", type=int, default=0, help="Skip N results")
    p_fetch.set_defaults(func=cmd_fetch)

    # index
    p_index = sub.add_parser("index", help="Build/rebuild the search index")
    p_index.add_argument("--chunk-size", type=int, default=500, help="Words per chunk")
    p_index.set_defaults(func=cmd_index)

    # ask
    p_ask = sub.add_parser("ask", help="Ask a question about medications")
    p_ask.add_argument("query", nargs="+", help="Your question (e.g., side effects of ibuprofen)")
    p_ask.add_argument("--k", type=int, default=5, help="Number of chunks to retrieve")
    p_ask.add_argument("--raw", action="store_true", help="Show raw retrieval results instead of LLM answer")
    p_ask.add_argument("--token", help="HuggingFace API token")
    p_ask.add_argument("--local", action="store_true", help="Use local transformer model (experimental)")
    p_ask.set_defaults(func=cmd_ask)

    # search (alias for ask --raw)
    p_search = sub.add_parser("search", help="Search drug labels (raw retrieval)")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("--k", type=int, default=5)
    p_search.set_defaults(func=lambda a: cmd_ask(argparse.Namespace(
        query=" ".join(a.query), k=a.k, raw=True, token=None, local=False
    )))

    # info
    p_info = sub.add_parser("info", help="Show index statistics")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    # Convert query list to string if present
    if hasattr(args, "query") and isinstance(args.query, list):
        args.query = " ".join(args.query)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
