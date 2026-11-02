"""PaperPilot CLI — search arXiv and query your local paper index."""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from . import __version__
from .arxiv_client import search_arxiv
from .indexer import PaperIndex
from .llm import query_papers, summarize_papers


def main(argv: list[str] | None = None) -> NoReturn:
    parser = argparse.ArgumentParser(
        prog="paperpilot",
        description="arXiv Research Paper RAG — search, ingest, and query academic papers.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── search ───────────────────────────────────────────────────────────
    search_p = sub.add_parser("search", help="Search arXiv and ingest papers")
    search_p.add_argument("query", help="Search query (e.g. 'transformer attention' or 'cat:cs.LG')")
    search_p.add_argument("-n", "--max-results", type=int, default=10, help="Max results (default: 10)")
    search_p.add_argument("--sort", choices=["relevance", "date"], default="relevance",
                         help="Sort order (default: relevance)")

    # ── query ────────────────────────────────────────────────────────────
    query_p = sub.add_parser("query", help="Ask a question against your indexed papers")
    query_p.add_argument("question", nargs="?", help="Your question")
    query_p.add_argument("-i", "--interactive", action="store_true", help="Interactive Q&A session")
    query_p.add_argument("-k", type=int, default=5, help="Number of context chunks (default: 5)")

    # ── list ─────────────────────────────────────────────────────────────
    sub.add_parser("list", help="List indexed papers")

    # ── summary ──────────────────────────────────────────────────────────
    summary_p = sub.add_parser("summary", help="Summarize all indexed papers")
    summary_p.add_argument("--query", help="Search and summarize in one step (experimental)")

    args = parser.parse_args(argv[1:] if argv else None)

    if args.command == "search":
        cmd_search(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "list":
        cmd_list()
    elif args.command == "summary":
        cmd_summary(args)

    sys.exit(0)


def cmd_search(args: argparse.Namespace) -> None:
    """Search arXiv, show results, and ingest into local index."""
    print(f"🔍 Searching arXiv for: {args.query}")
    print()

    sort_by = "relevance" if args.sort == "relevance" else "submittedDate"

    try:
        papers = search_arxiv(args.query, max_results=args.max_results, sort_by=sort_by)
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return

    if not papers:
        print("No papers found.")
        return

    print(f"Found {len(papers)} papers:\n")

    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.authors[:3])
        if len(p.authors) > 3:
            authors += f" et al."
        print(f"  {i:2d}. {p.title}")
        print(f"      {authors}  ({p.published[:10]})  [{', '.join(p.categories[:2])}]")
        print(f"      arXiv:{p.arxiv_id}")
        print()

    # Ingest all found papers
    print("📥 Ingesting papers into local index...")
    index = PaperIndex()
    index.load()  # load existing index if any

    added = index.add_papers(papers)
    index.save()

    print(f"✅ Added {added} chunks from {len(papers)} papers to index.")
    print(f"   Total: {index.paper_count} papers, {index.chunk_count} chunks in index.")
    print()
    print(f"Now try: paperpilot query \"your question about these papers\"")


def cmd_query(args: argparse.Namespace) -> None:
    """Query the local index."""
    index = PaperIndex()
    if not index.load():
        print("❌ No indexed papers found. Run 'paperpilot search <query>' first.")
        return

    if args.interactive:
        print("💬 Interactive Q&A session (type 'exit' to quit)\n")
        print(f"Index: {index.paper_count} papers, {index.chunk_count} chunks\n")
        while True:
            try:
                question = input("Q> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question or question.lower() in ("exit", "quit"):
                break
            _answer_question(index, question, args.k)
    elif args.question:
        _answer_question(index, args.question, args.k)
    else:
        print("❌ Provide a question or use --interactive for Q&A mode.")


def _answer_question(index: PaperIndex, question: str, k: int) -> None:
    """Retrieve and answer a single question."""
    print(f"\n🔎 Searching index for: {question}\n")

    hits = index.search(question, k=k)

    if not hits:
        print("No relevant context found in indexed papers.")
        return

    print(f"Retrieved {len(hits)} relevant passages:\n")
    for i, hit in enumerate(hits, 1):
        title = hit.chunk.title[:80]
        print(f"  [{i}] {title}  (score: {hit.score:.3f})")
    print()

    print("🤖 Generating answer...\n")
    answer = query_papers(question, hits)
    print(answer)
    print()


def cmd_list() -> None:
    """List indexed papers."""
    index = PaperIndex()
    if not index.load():
        print("❌ No indexed papers found.")
        return

    papers = index.list_papers()
    print(f"\n📚 Index contains {len(papers)} papers ({index.chunk_count} chunks):\n")
    for i, p in enumerate(papers, 1):
        print(f"  {i:2d}. {p['title']}")
        print(f"      arXiv:{p['id']}")
        print()


def cmd_summary(args: argparse.Namespace) -> None:
    """Summarize indexed papers."""
    if args.query:
        # Search, ingest, then summarize in one go
        cmd_search(args)

    index = PaperIndex()
    if not index.load():
        print("❌ No indexed papers found.")
        return

    papers_meta = index.list_papers()
    if not papers_meta:
        print("No papers to summarize.")
        return

    # Build paper objects from chunks
    from .arxiv_client import fetch_paper

    print(f"📝 Summarizing {len(papers_meta)} papers...\n")
    papers = []
    for p in papers_meta:
        paper = fetch_paper(p["id"])
        if paper:
            papers.append(paper)

    if papers:
        summary = summarize_papers(papers)
        print(summary)
    else:
        print("Could not fetch paper details for summary.")


if __name__ == "__main__":
    main()