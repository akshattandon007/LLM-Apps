"""
main.py
───────
Entry point for the API Documentation RAG Agent.

User flow:
  1. Provide an API documentation URL
  2. Agent fetches, embeds, and indexes the content
  3. Ask natural-language questions about the API docs
  4. Claude answers using only the retrieved context

Usage:
  python main.py
  python main.py --url https://developers.facebook.com/docs/graph-api/
  python main.py --url <URL> --no-crawl --k 3
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

# ── Load .env before importing project modules ────────────────────────────────
load_dotenv()

# Validate API key early
if not os.getenv("ANTHROPIC_API_KEY"):
    print(
        "\n[ERROR] ANTHROPIC_API_KEY is not set.\n"
        "Copy .env.example → .env and add your key.\n"
    )
    sys.exit(1)

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from document_loader import load_documents_from_url   # noqa: E402
from vector_store import build_vector_store, get_retriever  # noqa: E402
from rag_chain import build_rag_chain                 # noqa: E402

console = Console()

# ─── Banner ───────────────────────────────────────────────────────────────────

BANNER = """
[bold cyan]
  █████╗ ██████╗ ██╗    ██████╗  █████╗  ██████╗
 ██╔══██╗██╔══██╗██║    ██╔══██╗██╔══██╗██╔════╝
 ███████║██████╔╝██║    ██████╔╝███████║██║  ███╗
 ██╔══██║██╔═══╝ ██║    ██╔══██╗██╔══██║██║   ██║
 ██║  ██║██║     ██║    ██║  ██║██║  ██║╚██████╔╝
 ╚═╝  ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
[/bold cyan]
[dim]  API Documentation RAG Agent — powered by Claude + LangChain[/dim]
"""

HELP_TEXT = """
[bold]Available commands:[/bold]
  [cyan]/reset[/cyan]    — Clear conversation history (start fresh)
  [cyan]/sources[/cyan]  — Show source URLs for the last answer
  [cyan]/url[/cyan]      — Load a new documentation URL
  [cyan]/help[/cyan]     — Show this help message
  [cyan]/quit[/cyan]     — Exit the agent
"""


# ─── CLI args ─────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="API Documentation RAG Agent powered by Claude"
    )
    p.add_argument(
        "--url",
        type=str,
        help="API documentation URL to load (will prompt if omitted)",
    )
    p.add_argument(
        "--no-crawl",
        action="store_true",
        help="Disable link crawling; only index the exact URL provided",
    )
    p.add_argument(
        "--k",
        type=int,
        default=int(os.getenv("RETRIEVAL_K", "5")),
        help="Number of document chunks to retrieve per query (default: 5)",
    )
    p.add_argument(
        "--chunk-size",
        type=int,
        default=int(os.getenv("CHUNK_SIZE", "1000")),
        help="Character chunk size for text splitting (default: 1000)",
    )
    p.add_argument(
        "--chunk-overlap",
        type=int,
        default=int(os.getenv("CHUNK_OVERLAP", "200")),
        help="Overlap between chunks (default: 200)",
    )
    return p.parse_args()


# ─── Core pipeline ────────────────────────────────────────────────────────────

def load_and_index(
    url: str,
    crawl: bool,
    chunk_size: int,
    chunk_overlap: int,
    k: int,
):
    """Run the ingestion pipeline for the given URL and return a RAGAgent."""
    console.print(Rule("[bold cyan]Step 1 — Loading Documentation[/bold cyan]"))
    docs = load_documents_from_url(
        start_url=url,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        crawl=crawl,
    )

    console.print(Rule("[bold cyan]Step 2 — Building Vector Index[/bold cyan]"))
    vs = build_vector_store(docs)
    retriever = get_retriever(vs, k=k)

    console.print(Rule("[bold cyan]Step 3 — Initialising Claude RAG Chain[/bold cyan]"))
    agent = build_rag_chain(retriever)

    return agent


# ─── Interaction loop ─────────────────────────────────────────────────────────

def prompt_for_url() -> str:
    """Interactively prompt the user for a documentation URL."""
    console.print(
        Panel(
            "[bold]Enter the API documentation URL you want to query.[/bold]\n"
            "[dim]Example: https://developers.facebook.com/docs/graph-api/[/dim]",
            title="📄 Load Documentation",
            border_style="cyan",
        )
    )
    while True:
        url = console.input("[bold cyan]Documentation URL:[/bold cyan] ").strip()
        if url.startswith(("http://", "https://")):
            return url
        console.print("[red]Please enter a valid URL starting with http:// or https://[/red]")


def run_chat_loop(agent, last_sources: list) -> tuple:
    """
    Run one iteration of the Q&A loop.
    Returns (should_reload_url, new_url_or_none).
    """
    console.print(
        f"\n[dim]Turn {agent.turn_count + 1} | "
        "Type [cyan]/help[/cyan] for commands[/dim]"
    )
    user_input = console.input("[bold green]You:[/bold green] ").strip()

    if not user_input:
        return False, None

    # ── Commands ──
    if user_input.lower() in ("/quit", "/exit", "/q"):
        console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
        sys.exit(0)

    if user_input.lower() == "/help":
        console.print(Panel(HELP_TEXT, border_style="cyan"))
        return False, None

    if user_input.lower() == "/reset":
        agent.reset_history()
        console.print("[green]✔ Conversation history cleared.[/green]")
        return False, None

    if user_input.lower() == "/sources":
        if last_sources:
            console.print("\n[bold]Sources from last answer:[/bold]")
            for s in last_sources:
                console.print(f"  • {s}")
        else:
            console.print("[dim]No sources yet — ask a question first.[/dim]")
        return False, None

    if user_input.lower() == "/url":
        return True, None   # signal caller to reload

    # ── Ask the RAG agent ──
    console.print("\n[dim]Retrieving context and generating answer…[/dim]")
    try:
        result = agent.ask(user_input)
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        return False, None

    answer = result["answer"]
    sources = result["sources"]
    last_sources[:] = sources  # mutate in-place so caller sees updated list

    # ── Render answer ──
    console.print("\n" + Rule("[bold blue]Claude[/bold blue]"))
    try:
        console.print(Markdown(answer))
    except Exception:
        console.print(answer)

    if sources:
        console.print("\n[dim]Sources:[/dim]")
        for s in sources:
            console.print(f"  [dim]• {s}[/dim]")

    console.print(Rule())
    return False, None


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    console.print(BANNER)
    console.print(
        Panel(
            "[bold]Welcome![/bold] This agent indexes any API documentation URL "
            "and lets you ask questions in plain English.\n"
            "Claude uses [italic]only[/italic] the fetched docs as its knowledge "
            "source — no hallucinated API details.",
            title="API RAG Agent",
            border_style="cyan",
            expand=False,
        )
    )

    url = args.url or prompt_for_url()
    crawl = not args.no_crawl
    last_sources: list = []

    agent = load_and_index(
        url=url,
        crawl=crawl,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        k=args.k,
    )

    console.print(
        Panel(
            f"[bold green]Ready![/bold green] Indexed: [cyan]{url}[/cyan]\n"
            "Ask any question about this API documentation below.",
            border_style="green",
            expand=False,
        )
    )

    while True:
        reload, new_url = run_chat_loop(agent, last_sources)
        if reload:
            url = new_url or prompt_for_url()
            agent = load_and_index(
                url=url,
                crawl=crawl,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                k=args.k,
            )
            last_sources.clear()


if __name__ == "__main__":
    main()
