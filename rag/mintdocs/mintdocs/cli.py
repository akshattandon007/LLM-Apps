"""CLI entry point for MintDocs — `mintdocs index` and `mintdocs ask`."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .fetcher import Fetcher
from .chunker import chunk_filings
from .embedder import Embedder
from .indexer import Indexer
from .query import QueryEngine

# Default storage location
DEFAULT_INDEX_DIR = Path.home() / ".mintdocs" / "index"


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with index and ask subcommands."""
    parser = argparse.ArgumentParser(
        prog="mintdocs",
        description="SEC Filing & Annual Report Q&A — RAG-powered analysis of "
        "10-K and 10-Q filings from the SEC EDGAR database.",
    )
    parser.add_argument(
        "--version", action="version", version=f"mintdocs {__version__}"
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help=f"Index storage directory (default: {DEFAULT_INDEX_DIR})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Shared simulate flag added to each subparser
    _SIMULATE_HELP = "Run in simulated mode (no ML dependencies needed for demo)"

    # --- index subcommand ---
    index_parser = subparsers.add_parser(
        "index",
        help="Download filings and build a search index for a ticker",
    )
    index_parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)",
    )
    index_parser.add_argument(
        "--quarters",
        type=int,
        default=8,
        help="Number of filing quarters to fetch (default: 8)",
    )
    index_parser.add_argument(
        "--forms",
        type=str,
        nargs="+",
        default=["10-K", "10-Q"],
        help="Filing forms to fetch (default: 10-K 10-Q)",
    )
    index_parser.add_argument(
        "--simulate",
        action="store_true",
        help=_SIMULATE_HELP,
    )

    # --- ask subcommand ---
    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a natural-language question about a ticker's filings",
    )
    ask_parser.add_argument(
        "question",
        type=str,
        help='Your question in natural language (e.g., "What are the risk factors?")',
    )
    ask_parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="Stock ticker symbol to query (must be indexed first)",
    )
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of source chunks to retrieve (default: 5)",
    )
    ask_parser.add_argument(
        "--simulate",
        action="store_true",
        help=_SIMULATE_HELP,
    )

    return parser


def cmd_index(args: argparse.Namespace) -> int:
    """Fetch + chunk + embed + index for a ticker."""
    print(f"MintDocs: Indexing {args.ticker.upper()} filings...")
    if args.simulate:
        print("  [SIMULATED MODE] Using fake filing data")

    # 1. Fetch
    fetcher = Fetcher(simulate=args.simulate)
    print(f"  Resolving CIK for {args.ticker.upper()}...")
    try:
        metadata_list = fetcher.fetch_all(
            ticker=args.ticker,
            forms=args.forms,
            quarters=args.quarters,
        )
    except Exception as e:
        print(f"  ERROR fetching filings: {e}", file=sys.stderr)
        return 1
    finally:
        fetcher.close()

    if not metadata_list:
        print("  No filings found.")
        return 1

    print(f"  Found {len(metadata_list)} filings")

    # 2. Fetch filing texts + chunk
    chunker_texts = []
    fetcher2 = Fetcher(simulate=args.simulate)
    try:
        for meta in metadata_list:
            filing_dict = {
                "cik": meta.cik,
                "company_name": meta.company_name,
                "ticker": meta.ticker,
                "filing_type": meta.filing_type,
                "filing_date": meta.filing_date.isoformat(),
                "accession_number": meta.accession_number,
                "primary_doc": meta.primary_doc,
            }
            text = fetcher2.fetch_filing_text(filing_dict)
            chunker_texts.append((text, meta))
    except Exception as e:
        print(f"  ERROR downloading filing text: {e}", file=sys.stderr)
        return 1
    finally:
        fetcher2.close()

    chunks = chunk_filings(chunker_texts)
    print(f"  Generated {len(chunks)} section chunks")

    if not chunks:
        print("  No chunks extracted from filings.")
        return 1

    # 3. Embed
    embedder = Embedder(simulate=args.simulate)
    print("  Computing embeddings..." if not args.simulate else "  [SIMULATED] Computing embeddings...")
    chunks_with_emb = embedder.embed_chunks(chunks)
    print(f"  Embedded {len(chunks_with_emb)} chunks")

    # 4. Index
    indexer = Indexer(index_dir=args.index_dir, simulate=args.simulate)
    ticker_dir = indexer.build_index(chunks_with_emb, ticker=args.ticker)
    print(f"  Index built at: {ticker_dir}")

    print(f"\nDone! Indexed {args.ticker.upper()} — {len(chunks)} chunks across {len(metadata_list)} filings.")
    print(f"Next: mintdocs ask \"your question\" --ticker {args.ticker.upper()}")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    """Ask a question against an indexed ticker."""
    if not args.simulate:
        # Check index exists
        indexer = Indexer(index_dir=args.index_dir, simulate=False)
        if not indexer.index_exists(args.ticker):
            print(
                f"ERROR: No index found for {args.ticker.upper()}. "
                f"Run 'mintdocs index {args.ticker.upper()}' first.",
                file=sys.stderr,
            )
            return 1

    engine = QueryEngine(
        index_dir=args.index_dir,
        simulate=args.simulate,
        top_k=args.top_k,
    )
    print(f"MintDocs: Querying {args.ticker.upper()} index...")
    if args.simulate:
        print("  [SIMULATED MODE] Using hardcoded answers\n")

    try:
        result = engine.query(question=args.question, ticker=args.ticker)
    except Exception as e:
        print(f"  ERROR during query: {e}", file=sys.stderr)
        return 1

    print(result.format())
    return 0


def main() -> int:
    """Parse args and dispatch."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "index":
        return cmd_index(args)
    elif args.command == "ask":
        return cmd_ask(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())