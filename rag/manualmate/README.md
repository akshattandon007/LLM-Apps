# ManualMate 🛠️

Your home appliance manual assistant — upload PDFs of your appliance manuals and ask questions about error codes, maintenance, parts, and repairs.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest a manual
python manualmate.py ingest fridge-manual.pdf

# Ask questions
python manualmate.py ask "What does error code E24 mean?"
python manualmate.py ask "How often should I clean the condenser coils?"

# See what's indexed
python manualmate.py list

# Remove a manual
python manualmate.py remove fridge-manual.pdf

# Start fresh
python manualmate.py clear
```

## How It Works

1. **Ingest** — Load PDF or TXT manuals, split into sentence-boundary chunks, embed with OpenAI `text-embedding-3-small`
2. **Ask** — Your question is embedded, the top-5 most relevant chunks are retrieved via cosine similarity, and GPT-4o-mini generates an answer grounded in those chunks
3. **Manage** — List, remove, or clear your document collection

## Storage

All data is stored in `~/.manualmate/` — persists between sessions.

## Requirements

- Python 3.10+
- OpenAI API key (set `OPENAI_API_KEY` in environment or `.env`)

## Project Structure

```
manualmate/
├── manualmate.py         # CLI entry point
├── __main__.py           # `python -m manualmate` support
├── src/
│   ├── cli.py            # Click command definitions
│   ├── rag_engine.py     # RAG orchestration (ingest, query, ask)
│   ├── doc_loader.py     # PDF/TXT loading and chunking
│   ├── vector_store.py   # Numpy-based vector storage and search
│   └── models.py         # Data classes
├── tests/
│   ├── test_doc_loader.py
│   ├── test_rag_engine.py
│   └── test_smoke.py
├── Decisions.md
├── Flow.md
└── requirements.txt
```

## Why ManualMate?

Most people have a drawer full of appliance manuals they never read. When something breaks, you dig through papers hoping to find the right page. ManualMate makes every manual searchable instantly — just ask.