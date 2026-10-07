"""ManualMate CLI — Click-based command line interface."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel

from manualmate.rag_engine import ManualMateRAG

console = Console()


@click.group()
@click.option(
    "--store-dir",
    default=None,
    help="Override the default store directory (~/.manualmate).",
)
@click.pass_context
def cli(ctx, store_dir):
    """ManualMate — your home appliance manual assistant."""
    ctx.ensure_object(dict)
    try:
        ctx.obj["engine"] = ManualMateRAG(store_dir=store_dir)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.pass_context
def ingest(ctx, filepath):
    """Load a manual (PDF or TXT) into the knowledge base."""
    engine = ctx.obj["engine"]
    with console.status(f"Ingesting [bold]{filepath}[/bold]...", spinner="dots"):
        try:
            result = engine.ingest(filepath)
        except Exception as e:
            console.print(f"[red]Error ingesting file:[/red] {e}")
            sys.exit(1)

    console.print(f"\n[green]✓[/green] Ingested [bold]{result.filepath}[/bold]")
    console.print(f"   Chunks: {result.chunks}")
    console.print(f"   Characters: {result.characters:,}")
    console.print(f"   Time: {result.elapsed_seconds:.1f}s")
    console.print("\nReady to answer questions. Run: [bold]manualmate ask \"your question\"[/bold]")


@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--top-k", default=5, show_default=True, help="Number of chunks to retrieve.")
@click.pass_context
def ask(ctx, question, top_k):
    """Ask a question about your ingested manuals."""
    question_text = " ".join(question)
    engine = ctx.obj["engine"]

    with console.status("Searching manuals and generating answer...", spinner="dots"):
        result = engine.ask(question_text, top_k=top_k)

    if not result.sources:
        console.print(f"\n[yellow]No relevant documents found.[/yellow]")
        console.print("Ingest a manual first: [bold]manualmate ingest <file>[/bold]")
        return

    # Answer
    console.print()
    md = Markdown(result.answer)
    console.print(Panel(md, title="Answer", border_style="green"))
    console.print()

    # Sources
    sources_table = Table(title="Sources", show_header=True, header_style="bold cyan")
    sources_table.add_column("Source", style="cyan")
    sources_table.add_column("Relevance", style="yellow")
    for src, score in zip(result.sources, result.scores):
        sources_table.add_row(src, f"{score:.4f}")
    console.print(sources_table)


@cli.command()
@click.pass_context
def list_(ctx):
    """List all ingested documents and their chunk counts."""
    engine = ctx.obj["engine"]
    docs = engine.list_docs()

    if not docs:
        console.print("[yellow]No documents ingested yet.[/yellow]")
        console.print("Ingest a manual: [bold]manualmate ingest <file>[/bold]")
        return

    table = Table(title="Ingested Documents", show_header=True, header_style="bold cyan")
    table.add_column("Document", style="cyan")
    table.add_column("Chunks", style="yellow", justify="right")
    for name, count in docs:
        table.add_row(name, str(count))
    console.print(table)


@cli.command()
@click.argument("doc_name")
@click.pass_context
def remove(ctx, doc_name):
    """Remove an ingested document by its filename."""
    engine = ctx.obj["engine"]
    if engine.remove_doc(doc_name):
        console.print(f"[green]✓[/green] Removed [bold]{doc_name}[/bold]")
    else:
        console.print(f"[yellow]Document not found:[/yellow] {doc_name}")
        console.print("Run [bold]manualmate list[/bold] to see available documents.")


@cli.command()
@click.confirmation_option(prompt="Remove ALL ingested data?")
@click.pass_context
def clear(ctx):
    """Remove all ingested data and reset."""
    engine = ctx.obj["engine"]
    engine.clear()
    console.print("[green]✓[/green] All data cleared.")