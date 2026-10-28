"""CLI entry point for MailMerge — offline email RAG."""

import argparse
import os
import sys
from pathlib import Path

from .ingest import chunk_emails
from .models import EmailChunk
from .search import add_chunks, search, get_or_create_collection


def cmd_ingest(args):
    """Ingest an mbox file into the vector store."""
    mbox_path = Path(args.mbox)
    if not mbox_path.exists():
        print(f"Error: mbox file not found: {mbox_path}", file=sys.stderr)
        return 1

    print(f"Ingesting {mbox_path} ...")
    chunk_list = []
    for chunk in chunk_emails(str(mbox_path), chunk_size=args.chunk_size, overlap=args.overlap):
        chunk_list.append(
            {
                "id": chunk.chunk_id,
                "text": chunk.text,
                "subject": chunk.metadata.subject,
                "sender": chunk.metadata.sender,
                "date": chunk.metadata.date,
                "labels": ", ".join(chunk.metadata.labels),
            }
        )

    if not chunk_list:
        print("No email content found in the mbox file.")
        return 1

    print(f"  Parsed {len(chunk_list)} chunks from mbox")
    add_chunks(chunk_list, db_dir=args.db_dir)
    print(f"  Stored in ChromaDB at {args.db_dir}")
    return 0


def cmd_search(args):
    """Search the ingested email archive."""
    hits = search(
        query=args.query,
        top_k=args.top_k,
        db_dir=args.db_dir,
        metadata_filter=None,  # could extend with --sender / --date-from etc.
    )

    if not hits:
        print("No results found.")
        return 0

    print(f"\n{'='*60}")
    print(f"  Top {len(hits)} results for: \"{args.query}\"")
    print(f"{'='*60}\n")

    for i, hit in enumerate(hits, 1):
        score_pct = hit.score * 100
        print(f"  [{i}] {score_pct:.0f}% match")
        print(f"      From: {hit.sender}")
        print(f"      Subject: {hit.subject}")
        print(f"      Date: {hit.date}")
        print(f"      Snippet: {hit.snippet[:200]}...")
        print()

    return 0


def cmd_status(args):
    """Show index status."""
    try:
        col = get_or_create_collection(db_dir=args.db_dir)
        count = col.count()
        print(f"MailMerge index: {count} chunks in ChromaDB at {args.db_dir}")
    except Exception as e:
        print(f"Index not found or error: {e}", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(prog="mailmerge", description="Offline email RAG — search your email archives locally.")
    parser.add_argument("--db-dir", default=os.path.expanduser("~/.mailmerge/chroma"), help="ChromaDB directory")

    sub = parser.add_subparsers(dest="command", required=True)

    # ingest
    p_ingest = sub.add_parser("ingest", help="Ingest an mbox file")
    p_ingest.add_argument("mbox", help="Path to .mbox file (e.g., from Google Takeout)")
    p_ingest.add_argument("--chunk-size", type=int, default=800, help="Character chunk size")
    p_ingest.add_argument("--overlap", type=int, default=100, help="Chunk overlap in chars")

    # search
    p_search = sub.add_parser("search", help="Search the email archive")
    p_search.add_argument("query", help="Search query (natural language)")
    p_search.add_argument("--top-k", type=int, default=10, help="Number of results")

    # status
    sub.add_parser("status", help="Show index status")

    args = parser.parse_args()

    if args.command == "ingest":
        return cmd_ingest(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "status":
        return cmd_status(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())