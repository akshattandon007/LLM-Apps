# MintDocs

SEC Filing & Annual Report Q&A — RAG-powered analysis of 10-K and 10-Q
filings from the SEC EDGAR database.

```shell
mintdocs index AAPL
mintdocs ask "What are Apple's risk factors related to China supply chain?" --ticker AAPL
```

## Quick start (simulated mode — no ML deps)

```shell
pip install -e .

# Index with simulated data
mintdocs index AAPL --simulate

# Ask questions with simulated answers
mintdocs ask "What are Apple's China supply chain risks?" --ticker AAPL --simulate
```

## Full mode (real embeddings)

```shell
pip install -e ".[full]"

mintdocs index MSFT --quarters 8
mintdocs ask "What drove Microsoft's revenue growth?" --ticker MSFT
```

## CLI reference

```
mintdocs index    <ticker>     [--quarters N] [--forms 10-K 10-Q] [--simulate]
mintdocs ask      <question>   --ticker <ticker> [--top-k N] [--simulate]
```

| Flag | Description |
|------|-------------|
| `--simulate` | Demo mode — no sentence-transformers or FAISS needed |
| `--index-dir` | Where indices are stored (default: `~/.mintdocs/index/`) |
| `--quarters` | Number of filing quarters to fetch (default: 8) |
| `--top-k` | Number of source chunks for each answer (default: 5) |

## Architecture

```
User CLI  -->  Fetcher (SEC EDGAR API)
            --> Chunker (Item-section splitting)
            --> Embedder (sentence-transformers / simulated)
            --> Indexer (FAISS / metadata-only)
            --> QueryEngine (similarity search + source citation)
```

## Data flow

1. `mintdocs index AAPL` resolves the ticker to a CIK via SEC's bulk map
2. Searches SEC EFTS API for recent 10-K and 10-Q filings
3. Downloads each filing's full text
4. Chunks by Item sections (Item 1, Item 1A, Item 7, etc.)
5. Embeds chunks with `all-MiniLM-L6-v2`
6. Stores a FAISS flat L2 index + metadata JSON per ticker
7. `mintdocs ask "..." --ticker AAPL` embeds the question, retrieves top-k,
   and returns source-cited answers

## Project structure

```
mintdocs/
  mintdocs/
    __init__.py
    cli.py        — argparse CLI entry point
    fetcher.py    — SEC EDGAR API client
    chunker.py    — Item-section text splitting
    embedder.py   — sentence-transformers integration
    indexer.py    — FAISS index builder/loader
    query.py      — Query engine with source citations
    models.py     — Dataclass models
  tests/
    test_fetcher.py
    test_chunker.py
    test_embedder.py
    test_indexer.py
  setup.py
  requirements.txt
  Decisions.md
  Flow.md
```

## Requirements

- Python 3.10+
- Core: `httpx` (no ML deps for simulated mode)
- Full: `sentence-transformers`, `faiss-cpu`, `numpy`

## SEC API notes

- A `User-Agent` header with a descriptive name and contact email is required
  by the SEC EDGAR terms of service
- Rate-limited to ~10 requests per second; MintDocs uses 150ms delays
- No API key required — all EDGAR data is public