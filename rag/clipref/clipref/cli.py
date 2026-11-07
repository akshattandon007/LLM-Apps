"""ClipRef — CLI entry point with argparse."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from clipref import utils
from clipref import indexer
from clipref import searcher


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clipref",
        description="🔖 ClipRef — Your personal bookmark & clipping search engine.",
        epilog="Examples:\n"
        "  clipref index ~/my-clippings/\n"
        "  clipref search 'serverless database patterns'\n"
        "  clipref ask 'What did I save about microservices?'\n"
        "  clipref stats\n"
        "  clipref drop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- index ---
    p_idx = sub.add_parser("index", help="Index files for search")
    p_idx.add_argument("paths", nargs="+", help="Files or directories to index")
    p_idx.add_argument("--db", help="Database directory (default: ~/.clipref)")
    p_idx.add_argument("--chunk-size", type=int, help="Chunk size in chars")
    p_idx.add_argument("--chunk-overlap", type=int, help="Overlap between chunks")
    p_idx.add_argument("--model", help="Embedding model name")
    p_idx.add_argument("--glob", help="File glob pattern (default: *.md *.txt *.html)")

    # --- search ---
    p_srch = sub.add_parser("search", help="Search indexed clips")
    p_srch.add_argument("query", nargs="?", help="Search query")
    p_srch.add_argument("--db", help="Database directory")
    p_srch.add_argument("--top-k", type=int, help="Number of results")
    p_srch.add_argument("--model", help="Embedding model name")
    # Interactive mode
    p_srch.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive REPL mode")

    # --- ask ---
    p_ask = sub.add_parser("ask", help="Ask a question with AI-generated answer")
    p_ask.add_argument("question", nargs="?", help="Your question")
    p_ask.add_argument("--db", help="Database directory")
    p_ask.add_argument("--top-k", type=int, help="Number of results to retrieve")
    p_ask.add_argument("--model", help="LLM model name")
    p_ask.add_argument("--embed-model", help="Embedding model name")
    p_ask.add_argument("--system-prompt", help="Custom system prompt")
    # Interactive mode
    p_ask.add_argument("--interactive", "-i", action="store_true",
                       help="Interactive Q&A mode")

    # --- stats ---
    p_stats = sub.add_parser("stats", help="Show index statistics")
    p_stats.add_argument("--db", help="Database directory (default: ~/.clipref)")

    # --- drop ---
    p_drop = sub.add_parser("drop", help="Delete the entire index")
    p_drop.add_argument("--db", help="Database directory (default: ~/.clipref)")

    return parser


def _confirm(prompt: str = "Are you sure?") -> bool:
    """Ask for confirmation."""
    resp = input(f"{prompt} [y/N] ").strip().lower()
    return resp in ("y", "yes")


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_index(args: argparse.Namespace) -> int:
    db_path = utils.resolve_db_path(args.db)
    chunk_sz = args.chunk_size or utils.chunk_size()
    ov = args.chunk_overlap or utils.chunk_overlap()
    model_name = args.model or utils.embedding_model_name()

    print(f"🔍 Scanning files...")
    files = indexer.scan_files(args.paths, args.glob)
    if not files:
        print("No text files found matching the pattern.")
        return 1

    print(f"📄 Found {len(files)} files. Chunking...")
    chunks = indexer.chunk_files(files, chunk_sz, ov)
    if not chunks:
        print("No chunkable content found in the scanned files.")
        return 1

    print(f"🧩 Generated {len(chunks)} chunks. Loading embedding model ({model_name})...")
    model = utils.get_embedding_model(model_name)

    print(f"💾 Embedding and storing in {db_path}...")
    stored = indexer.embed_and_store(chunks, model, db_path)
    print(f"✅ Indexed {stored} chunks from {len(files)} files.")
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    if args.interactive:
        return _interactive_search(args)

    query = args.query
    if not query:
        print("Enter a search query or use --interactive / -i for REPL mode.")
        return 1

    db_path = utils.resolve_db_path(args.db)
    top_k = args.top_k or utils.top_k()
    model_name = args.model or utils.embedding_model_name()

    model = utils.get_embedding_model(model_name)
    results = searcher.search(query, db_path, model, top_k)

    if not results:
        print(f"No results found for: {query}")
        return 0

    print(f"\n🔍 Results for: {query}\n")
    for r in results:
        print(r)
        print()
    return 0


def _interactive_search(args: argparse.Namespace) -> int:
    db_path = utils.resolve_db_path(args.db)
    model = utils.get_embedding_model(args.model or utils.embedding_model_name())

    print("🔍 ClipRef Interactive Search (Ctrl+C or empty query to exit)")
    try:
        while True:
            query = input("\nSearch: ").strip()
            if not query:
                break
            results = searcher.search(query, db_path, model, utils.top_k())
            for r in results:
                print(r)
                print()
    except (EOFError, KeyboardInterrupt):
        print()
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    if args.interactive:
        return _interactive_ask(args)

    question = args.question
    if not question:
        print("Enter a question or use --interactive / -i for REPL mode.")
        return 1

    db_path = utils.resolve_db_path(args.db)
    top_k = args.top_k or utils.top_k()
    model_name = args.embed_model or utils.embedding_model_name()

    model = utils.get_embedding_model(model_name)
    results = searcher.search(question, db_path, model, top_k)

    if not results:
        print(f"No context found for: {question}")
        return 0

    print(f"🤖 Generating answer...")
    answer = searcher.generate_answer(
        question, results,
        llm_model=args.model,
        system_prompt=args.system_prompt,
    )

    if answer:
        print(f"\nAnswer:\n{answer.text}\n")
        print("Sources:")
        for i, src in enumerate(answer.sources, 1):
            print(f"  {i}. {src.source_path} (score: {src.score:.3f})")
    else:
        print("Could not generate an answer. Check your API key.")
        print("\nRetrieved context (no LLM):")
        for r in results:
            print(r)
            print()
    return 0


def _interactive_ask(args: argparse.Namespace) -> int:
    db_path = utils.resolve_db_path(args.db)
    model = utils.get_embedding_model(args.embed_model or utils.embedding_model_name())

    print("💬 ClipRef Interactive Q&A (Ctrl+C or empty question to exit)")
    print("Tip: Set OPENAI_API_KEY for AI-generated answers.\n")
    try:
        while True:
            question = input("Q: ").strip()
            if not question:
                break
            top_k = args.top_k or utils.top_k()
            results = searcher.search(question, db_path, model, top_k)
            if not results:
                print("No relevant context found.")
                continue

            answer = searcher.generate_answer(
                question, results,
                llm_model=args.model,
                system_prompt=args.system_prompt,
            )

            if answer:
                print(f"A: {answer.text}")
                print(f"  (sources from {len(answer.sources)} clips)")
            else:
                print("A: (no LLM — showing raw results)")
                for r in results:
                    print(f"  [{r.score:.3f}] {r.source_path}")
            print()
    except (EOFError, KeyboardInterrupt):
        print()
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    db_path = utils.resolve_db_path(getattr(args, "db", None))
    stats = indexer.get_stats(db_path)
    if stats is None:
        print("No index found. Run 'clipref index <directory>' first.")
        return 0

    print(f"📊 Index Statistics")
    print(f"  Chunks indexed: {stats.chunk_count}")
    print(f"  Database size:  {stats.database_size_kb:.1f} KB")
    return 0


def _cmd_drop(args: argparse.Namespace) -> int:
    db_path = utils.resolve_db_path(getattr(args, "db", None))
    if _confirm("Delete the entire ClipRef index?"):
        if indexer.drop_index(db_path):
            print("✅ Index deleted. Run 'clipref index' to rebuild.")
        else:
            print("No index existed.")
    else:
        print("Cancelled.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command_map = {
        "index": _cmd_index,
        "search": _cmd_search,
        "ask": _cmd_ask,
        "stats": _cmd_stats,
        "drop": _cmd_drop,
    }

    handler = command_map.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())