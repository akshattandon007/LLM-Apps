"""
main.py
───────
Entry point for SpendLens — RAG-powered personal finance agent.

Two modes:
  1. FastAPI server:  uvicorn main:app --reload
  2. CLI mode:        python main.py --cli

API Endpoints:
  POST /ingest          — Upload PDF/CSV statement
  POST /chat            — Ask a natural-language question
  GET  /stats           — Get spending analytics
  GET  /health          — Health check
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Load .env before importing project modules ────────────────────────────────
load_dotenv()

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from document_loader import load_transactions, transactions_to_documents  # noqa: E402
from vector_store import build_vector_store, get_retriever, load_vector_store  # noqa: E402
from rag_chain import build_rag_chain, SpendLensAgent  # noqa: E402
from analytics import (  # noqa: E402
    category_breakdown,
    monthly_totals,
    top_merchants,
    detect_subscriptions,
    spending_summary,
)

# ─── Global state ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="SpendLens API",
    description="RAG-powered personal finance agent — ingest statements, ask questions, get analytics.",
    version="1.0.0",
)

# CORS: allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (shared across requests)
_agent: Optional[SpendLensAgent] = None
_transactions: list = []
_indexed: bool = False


# ─── Pydantic models ──────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


class StatsResponse(BaseModel):
    summary: dict
    categories: dict
    monthly: dict
    top_merchants: dict
    subscriptions: dict


# ─── Helper: run ingestion pipeline ────────────────────────────────────────────


def run_ingestion(file_paths: list[Path]):
    """Run the full ingestion pipeline on one or more statement files."""
    global _agent, _transactions, _indexed

    from rich.console import Console
    console = Console()

    # 1. Load all transactions
    all_txs = []
    for fp in file_paths:
        txs = load_transactions(fp)
        all_txs.extend(txs)
        console.print(f"  [green]✔[/green] {fp.name}: {len(txs)} transactions")

    if not all_txs:
        raise ValueError("No transactions loaded.")

    _transactions = all_txs

    # 2. Create documents for RAG
    docs = transactions_to_documents(all_txs, group_by_month=True)

    # 3. Build vector store
    vs = build_vector_store(docs, persist=True)
    retriever = get_retriever(vs, k=int(os.getenv("RETRIEVAL_K", "10")))

    # 4. Build RAG chain (if API key is available)
    if os.getenv("ANTHROPIC_API_KEY"):
        _agent = build_rag_chain(retriever)
    else:
        console.print(
            "[yellow]⚠  ANTHROPIC_API_KEY not set — RAG Q&A disabled. "
            "Analytics still work.[/yellow]"
        )
        _agent = None

    _indexed = True
    console.print(f"[bold green]✔  Indexed {len(all_txs)} transactions.[/bold green]\n")


# ─── API Endpoints ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok", "indexed": _indexed, "transaction_count": len(_transactions)}


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """Upload a bank/credit-card statement (PDF or CSV) and index it."""
    global _agent, _transactions, _indexed

    suffix = Path(file.filename or "unknown").suffix.lower()
    if suffix not in (".pdf", ".csv"):
        raise HTTPException(400, f"Unsupported file type: {suffix}. Use .pdf or .csv.")

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        txs = load_transactions(tmp_path)
        _transactions.extend(txs)

        # Rebuild index with all transactions
        docs = transactions_to_documents(_transactions, group_by_month=True)
        vs = build_vector_store(docs, persist=True)
        retriever = get_retriever(vs, k=int(os.getenv("RETRIEVAL_K", "10")))

        if os.getenv("ANTHROPIC_API_KEY"):
            _agent = build_rag_chain(retriever)

        _indexed = True

        return JSONResponse({
            "status": "ok",
            "transactions_loaded": len(txs),
            "total_transactions": len(_transactions),
            "file": file.filename,
        })
    except Exception as exc:
        raise HTTPException(500, f"Ingestion failed: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Ask a natural-language question about your spending."""
    if not _indexed:
        raise HTTPException(400, "No data indexed. Upload a statement first via /ingest.")
    if not _agent:
        raise HTTPException(400, "RAG not available. Set ANTHROPIC_API_KEY in .env.")

    try:
        result = _agent.ask(req.question)
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
        )
    except Exception as exc:
        raise HTTPException(500, f"RAG query failed: {exc}")


@app.get("/stats", response_model=StatsResponse)
async def stats(
    category_filter: Optional[str] = None,
    top_merchants_n: int = 10,
    period_days: Optional[int] = 30,
):
    """Get spending analytics: categories, monthly trends, top merchants, subscriptions."""
    if not _transactions:
        raise HTTPException(400, "No data indexed. Upload a statement first via /ingest.")

    txs = _transactions
    if category_filter:
        txs = [tx for tx in txs if tx.category == category_filter]

    return StatsResponse(
        summary=spending_summary(_transactions, period_days=period_days),
        categories=category_breakdown(_transactions),
        monthly=monthly_totals(_transactions),
        top_merchants=top_merchants(_transactions, top_n=top_merchants_n),
        subscriptions=detect_subscriptions(_transactions),
    )


@app.post("/reset")
async def reset():
    """Clear all indexed data and conversation history."""
    global _agent, _transactions, _indexed
    if _agent:
        _agent.reset_history()
    _agent = None
    _transactions = []
    _indexed = False
    return {"status": "ok", "message": "All data cleared."}


# ─── CLI mode ─────────────────────────────────────────────────────────────────


def run_cli(args: argparse.Namespace):
    """Run SpendLens in interactive CLI mode."""
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.rule import Rule

    console = Console()

    BANNER = """
[bold cyan]
  ███████╗██████╗ ███████╗███╗   ██╗██████╗ ██╗     ███████╗███╗   ██╗███████╗
  ██╔════╝██╔══██╗██╔════╝████╗  ██║██╔══██╗██║     ██╔════╝████╗  ██║██╔════╝
  ███████╗██████╔╝█████╗  ██╔██╗ ██║██║  ██║██║     █████╗  ██╔██╗ ██║███████╗
  ╚════██║██╔═══╝ ██╔══╝  ██║╚██╗██║██║  ██║██║     ██╔══╝  ██║╚██╗██║╚════██║
  ███████║██║     ███████╗██║ ╚████║██████╔╝███████╗███████╗██║ ╚████║███████║
  ╚══════╝╚═╝     ╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝
[/bold cyan]
[dim]  RAG-Powered Personal Finance Agent — Know where your money goes[/dim]
"""

    console.print(BANNER)

    # Collect files
    files = args.files
    if not files:
        console.print(
            Panel(
                "[bold]No statement files provided.[/bold]\n"
                "Usage: python main.py --cli --files path/to/statement.csv",
                border_style="yellow",
            )
        )
        return

    console.print(Rule("[bold cyan]Ingesting Statements[/bold cyan]"))
    run_ingestion([Path(f) for f in files])

    # Show analytics
    console.print(Rule("[bold cyan]Spending Summary[/bold cyan]"))
    summary = spending_summary(_transactions)
    console.print(f"Total spent: [red]${summary['total_spent']:.2f}[/red]")
    console.print(f"Total income: [green]${summary['total_income']:.2f}[/green]")
    console.print(f"Transactions: {summary['transaction_count']}")

    cats = category_breakdown(_transactions)
    console.print("\n[bold]Top Categories:[/bold]")
    for c in cats["categories"][:5]:
        console.print(f"  • {c['category']}: ${c['total']:.2f} ({c['percent']}%)")

    if not _agent:
        console.print("\n[yellow]Set ANTHROPIC_API_KEY for Q&A mode.[/yellow]")
        return

    # Chat loop
    console.print(Rule("[bold cyan]Ask Questions[/bold cyan]"))
    console.print("[dim]Type /help for commands, /quit to exit[/dim]\n")

    while True:
        user_input = console.input("[bold green]You:[/bold green] ").strip()
        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "/q"):
            console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
            break

        if user_input.lower() == "/help":
            console.print(Panel(
                "[bold]Commands:[/bold]\n"
                "  [cyan]/stats[/cyan]   — Show spending summary\n"
                "  [cyan]/cats[/cyan]    — Show category breakdown\n"
                "  [cyan]/subs[/cyan]    — Detect subscriptions\n"
                "  [cyan]/reset[/cyan]   — Clear conversation history\n"
                "  [cyan]/quit[/cyan]    — Exit",
                border_style="cyan",
            ))
            continue

        if user_input.lower() == "/stats":
            s = spending_summary(_transactions)
            console.print(f"\n[bold]Spending Summary[/bold]")
            console.print(f"Total spent: ${s['total_spent']:.2f}")
            console.print(f"Total income: ${s['total_income']:.2f}")
            console.print(f"Daily avg: ${s['daily_average']:.2f}")
            continue

        if user_input.lower() == "/cats":
            cb = category_breakdown(_transactions)
            console.print("\n[bold]Category Breakdown[/bold]")
            for c in cb["categories"]:
                bar = "█" * int(c["percent"] / 2)
                console.print(f"  {c['category']:20s} ${c['total']:>8.2f}  {bar}")
            continue

        if user_input.lower() == "/subs":
            subs = detect_subscriptions(_transactions)
            console.print("\n[bold]Detected Subscriptions[/bold]")
            for s in subs["subscriptions"]:
                conf_color = {"high": "red", "medium": "yellow", "low": "dim"}.get(s["confidence"], "")
                console.print(
                    f"  [{conf_color}]${s['amount']:.2f}[/{conf_color}] "
                    f"{s['merchant']} — {s['occurrences']}× "
                    f"({s['confidence']} confidence)"
                )
            continue

        if user_input.lower() == "/reset":
            _agent.reset_history()
            console.print("[green]✔ History cleared.[/green]")
            continue

        # Ask the agent
        console.print("\n[dim]Retrieving transactions and generating answer…[/dim]")
        try:
            result = _agent.ask(user_input)
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
            continue

        console.print("\n" + Rule("[bold blue]SpendLens[/bold blue]"))
        try:
            console.print(Markdown(result["answer"]))
        except Exception:
            console.print(result["answer"])

        console.print(Rule())


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="SpendLens — RAG-powered personal finance agent")
    parser.add_argument(
        "--cli", action="store_true",
        help="Run in interactive CLI mode (default: start FastAPI server)",
    )
    parser.add_argument(
        "--files", nargs="+",
        help="Statement files to ingest (PDF or CSV)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host for FastAPI server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port for FastAPI server (default: 8000)",
    )
    parser.add_argument(
        "--ingest-on-start", nargs="+",
        help="Files to ingest immediately on server start",
    )
    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        # Pre-ingest files if provided
        if args.ingest_on_start:
            run_ingestion([Path(f) for f in args.ingest_on_start])

        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
