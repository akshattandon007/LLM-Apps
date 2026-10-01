#!/usr/bin/env python3
"""GardenGuide — RAG-powered garden wisdom from your own documents.

Usage:
  gardenguide ingest <file>     Add a gardening document (txt, pdf, md)
  gardenguide ask <question>    Ask a question using your ingested docs
  gardenguide query <question>  Just retrieve relevant passages (no generation)
  gardenguide list              Show ingested documents
  gardenguide remove <file>     Remove an ingested document
  gardenguide clear             Remove ALL ingested data
  gardenguide info              Show database statistics
"""

import os
import sys
from typing import Optional

import click


# ── Lazy-load the RAG engine ────────────────────────────────────────────


def _get_rag():
    from src.rag_engine import GardenRAG

    store_dir = os.environ.get("GARDENGUIDE_DIR", "~/.gardenguide")
    embed_model = os.environ.get("GARDENGUIDE_EMBED_MODEL", "text-embedding-3-small")
    gen_model = os.environ.get("GARDENGUIDE_GEN_MODEL", "gpt-4o-mini")
    return GardenRAG(store_dir=store_dir, embed_model=embed_model, gen_model=gen_model)


# ── CLI ──────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """GardenGuide — RAG-powered garden wisdom from your own documents.

    Ingest seed packets, planting guides, and garden journals, then ask
    questions grounded in YOUR data.
    """


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False))
def ingest(filepath: str):
    """Ingest a gardening document (txt, pdf, md)."""
    rag = _get_rag()
    click.echo(f"📥 Ingesting {filepath}... ", nl=False)
    try:
        result = rag.ingest(filepath)
        click.echo(click.style("OK", fg="green"))
        click.echo(
            f"   {result['chunks']} chunks from {result['characters']:,} chars "
            f"({result['elapsed_seconds']}s)"
        )
    except Exception as e:
        click.echo(click.style("FAILED", fg="red"))
        click.echo(f"   Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("-k", "--top-k", default=3, help="Number of context chunks to retrieve")
@click.option("-m", "--model", help="Override the generation model")
def ask(question: tuple, top_k: int, model: Optional[str]):
    """Ask a question and get a RAG-grounded answer."""
    question_text = " ".join(question)
    rag = _get_rag()
    click.echo(click.style("🔍 Searching your garden docs...", dim=True))
    result = rag.ask(question_text, top_k=top_k, model=model)
    click.echo()
    click.echo(click.style("📝 Answer:", bold=True))
    click.echo(result["answer"])
    if result.get("sources"):
        click.echo()
        click.echo(click.style("📚 Sources:", dim=True))
        for s in result["sources"]:
            click.echo(f"   • {s}")
    click.echo()
    if result.get("chunks"):
        click.echo(click.style("📄 Retrieved passages:", dim=True))
        for i, chunk in enumerate(result["chunks"], 1):
            click.echo(f"   [{i}] {chunk[:120]}..." if len(chunk) > 120 else f"   [{i}] {chunk}")


@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("-k", "--top-k", default=5, help="Number of passages to retrieve")
def query(question: tuple, top_k: int):
    """Retrieve relevant passages without generating an answer."""
    question_text = " ".join(question)
    rag = _get_rag()
    results = rag.query(question_text, top_k=top_k)
    if not results:
        click.echo("No documents ingested yet. Use `gardenguide ingest <file>` first.")
        return
    click.echo(click.style(f"🔍 Top {len(results)} passages:", bold=True))
    click.echo()
    for i, (text, score) in enumerate(results, 1):
        click.echo(click.style(f"[{i}] (score: {score:.3f})", dim=True))
        click.echo(f"   {text[:200]}..." if len(text) > 200 else f"   {text}")
        click.echo()


@cli.command("list")
def list_docs():
    """Show ingested documents."""
    rag = _get_rag()
    docs = rag.list_docs()
    if not docs:
        click.echo("No documents have been ingested yet.")
        click.echo("Add one with:  gardenguide ingest <file>")
        return
    click.echo(click.style(f"📚 {len(docs)} document(s) ingested:", bold=True))
    for i, d in enumerate(docs, 1):
        click.echo(f"  {i:3d}. {d}")


@cli.command()
@click.argument("filepath", type=str)
def remove(filepath: str):
    """Remove an ingested document."""
    rag = _get_rag()
    if rag.remove_doc(filepath):
        click.echo(click.style(f"🗑️ Removed: {filepath}", fg="yellow"))
    else:
        click.echo(click.style(f"Not found: {filepath}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def clear():
    """Remove ALL ingested documents and data."""
    rag = _get_rag()
    rag.clear()
    click.echo(click.style("🧹 All ingested data cleared.", fg="yellow"))


@cli.command()
def info():
    """Show database statistics."""
    rag = _get_rag()
    store = rag.store
    click.echo(click.style("📊 GardenGuide Stats", bold=True))
    click.echo(f"   Documents: {store.doc_count}")
    click.echo(f"   Chunks:    {store.chunk_count}")
    click.echo(f"   Store dir: {store.store_dir}")


if __name__ == "__main__":
    cli()