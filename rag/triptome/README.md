# TripTome 🌍

**Travel Knowledge RAG** — ask your travel guides, PDFs, and blog posts anything. Get grounded answers with source citations from your own curated travel library.

TripTome is a CLI-first RAG system that indexes anything you have about a destination — Lonely Planet PDFs, saved blog posts, hotel confirmations, even your own trip notes — then answers natural-language questions about it.

```bash
# What's the best time to visit Bali?
$ triptome ask "When is the best time to visit Bali?"
→ April–October is the dry season (source: bali-travel-guide.pdf, p.12)

# How much should I budget for 7 days in Tokyo?
$ triptome ask "Budget estimate for 7 days in Tokyo"
→ ~$1,200–1,800 excluding flights (sources: japan-budget.md, tokyo-notes.pdf)
```

## Why you'd use it

- You hoard travel PDFs, e-guides, and blog saves but never read them when planning
- You want answers *grounded in your own sources* — no hallucinated hotel names
- You plan with a travel agent/AI assistant and want it quoting *your* research

## Install

```bash
pip install -e /path/to/triptome
```

Needs Python 3.10+. First run downloads a small embedding model (~90 MB).

## Usage

```bash
# 1. Ingest your travel library (PDFs, .md, .txt, .html)
triptome ingest ~/travel/bali-guide.pdf ~/travel/tokyo-notes.md

# 2. Ask questions — gets answers with source citations
triptome ask "What's the best time to visit Bali?"

# 3. Optional: LLM-powered answers (openai-compatible API)
export OPENAI_API_KEY=sk-...
triptome ask --llm "Draft a 3-day Tokyo itinerary under $500"
```

## How it works

| Component | Choice |
|-----------|--------|
| Embeddings | `fastembed` (all-MiniLM-L6-v2 via ONNX) — free, local, CPU-only |
| Vector store | FAISS (HNSW) — fast nearest-neighbor search, no server |
| Answer mode | Two-tier: LLM when `OPENAI_API_KEY` set, raw context fallback otherwise |
| CLI | Click + Rich — `triptome ingest` / `triptome ask` |

## Two-tier answers

- **Without API key** — returns the top matching source passages verbatim with citations (always works, offline)
- **With `OPENAI_API_KEY`** — a generative answer synthesized from the retrieved context, with the source filenames cited

## Files

```
triptome/
├── triptome/
│   ├── cli.py        # CLI entry point (Click + Rich)
│   ├── indexer.py    # ingest pipeline: parse → chunk → embed → index
│   ├── embedder.py   # fastembed wrapper
│   ├── generator.py  # two-tier answer generation (LLM + fallback)
│   └── models.py     # data classes
├── tests/            # 21 tests (indexer, embedder, generator, CLI)
├── Decisions.md      # 15 architectural decisions with rejected alternatives
├── Flow.md           # execution trace + module dependency graph
└── requirements.txt
```

## Tests

```bash
python -m pytest tests/ -v    # 21/21 passing
```

## Data sources

- **Your own files** — no external API required for search
- **Optional LLM** — any OpenAI-compatible endpoint for generative answers