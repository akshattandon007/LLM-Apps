"""CLI entry point for TripTome."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from triptome import __version__
from triptome.indexer import ingest_directory
from triptome.embedder import index_documents, search, get_stats, reset
from triptome.generator import answer_query

console = Console()


@click.group()
@click.version_option(__version__, prog_name="triptome")
def cli():
    """🌍 TripTome — Your travel knowledge companion.

    Index travel guides, PDFs, and blog posts, then ask
    natural-language questions about any destination.
    """
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--chunk-size", default=500, show_default=True,
              help="Target words per chunk")
@click.option("--overlap", default=50, show_default=True,
              help="Overlap words between chunks")
def ingest(path: str, chunk_size: int, overlap: int):
    """Ingest travel documents from a file or directory."""
    source_path = Path(path)
    if not source_path.exists():
        console.print(f"[red]❌ Path not found: {path}[/red]")
        sys.exit(1)

    with console.status(f"[bold green]📖 Ingesting {source_path.name}..."):
        docs = ingest_directory(source_path, chunk_size, overlap)

    if not docs:
        console.print("[yellow]⚠️  No supported documents found. "
                      "Supported: .txt, .md, .pdf[/yellow]")
        sys.exit(1)

    with console.status("[bold green]🗄️  Indexing into vector store..."):
        count = index_documents(docs)

    console.print(f"\n[green]✅ Ingested [bold]{count}[/bold] chunks from "
                  f"[bold]{len(set(d.source for d in docs))}[/bold] "
                  f"document(s)[/green]")
    stats = get_stats()
    console.print(f"📊 Total chunks in store: [bold]{stats['total_chunks']}[/bold]")


@cli.command()
@click.argument("query", nargs=-1, required=True)
@click.option("--top-k", default=5, show_default=True,
              help="Number of results to retrieve")
def ask(query: tuple[str, ...], top_k: int):
    """Ask a travel question.

    Searches your indexed travel documents and returns an answer
    with citations.
    """
    q = " ".join(query)
    with console.status("[bold green]🔍 Searching travel guides..."):
        result = answer_query(q, n_results=top_k)

    if not result.citations:
        console.print("[yellow]📭 No relevant results found. "
                      "Try 'triptome ingest <path>' first.[/yellow]")
        return

    # Print answer
    console.print(Panel(
        Markdown(result.answer),
        title=f"[bold blue]💬 {q}[/bold blue]",
        border_style="blue",
        padding=(1, 2),
    ))

    # Print sources
    if result.citations:
        table = Table(title="📚 Sources", show_header=True,
                      header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Document", style="white")
        table.add_column("Relevance", justify="right", style="green")
        table.add_column("Page", justify="right", style="dim")

        for i, cit in enumerate(result.citations[:5], 1):
            page_str = str(cit.page) if cit.page else "—"
            table.add_row(
                str(i),
                cit.source,
                f"{cit.score:.1%}",
                page_str,
            )
        console.print(table)


@cli.command()
def stats():
    """Show statistics about the indexed collection."""
    info = get_stats()
    if info["total_chunks"] == 0:
        console.print("[yellow]📭 No documents indexed yet. "
                      "Use 'triptome ingest <path>' to add travel guides.[/yellow]")
        return

    console.print("[bold]📊 TripTome Collection Stats[/bold]")
    console.print(f"  📄 Total chunks: [bold]{info['total_chunks']}[/bold]")
    console.print(f"  📚 Source documents: [bold]{info['source_count']}[/bold]")
    console.print("\n[bold]Sources:[/bold]")
    for src in info["sources"]:
        console.print(f"  📖 {src}")


@cli.command()
@click.confirmation_option(prompt="Delete all indexed travel documents?")
def clear():
    """Delete all indexed documents and start fresh."""
    reset()
    console.print("[green]✅ Vector store cleared. "
                  "You can re-ingest with 'triptome ingest'.[/green]")


def main():
    cli()