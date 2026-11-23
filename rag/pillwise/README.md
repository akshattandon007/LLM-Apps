# 💊 PillWise

**RAG-powered medication information assistant.** Ask plain-language questions about FDA-approved drugs — side effects, dosage, interactions, warnings — and get answers grounded in official drug labels.

## What it does

PillWise downloads FDA drug labels via the [OpenFDA API](https://open.fda.gov/apis/drug/label/) (free, no API key needed), indexes them with semantic search, and lets you ask questions in natural language. Instead of reading through dense medical leaflets, just type:

```
pillwise ask "Can I take ibuprofen with my blood pressure medication?"
```

## How it works

```
User Query → Semantic Search → Drug Label Chunks → LLM Answer (optional)
                    ↓
          FAISS + sentence-transformers
                    ↓
          FDA Drug Labels (OpenFDA API)
```

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### 1. Fetch drug labels

```bash
pillwise fetch --limit 100
```

Downloads 100 drug labels from OpenFDA and caches them locally.

### 2. Build the search index

```bash
pillwise index
```

Creates a FAISS index over the fetched drug label chunks using sentence-transformers.

### 3. Ask questions

```bash
pillwise ask "What are the side effects of ibuprofen?"
```

Output (retrieval-only — no LLM needed):

```
📋 PillWise — Medication Information for: What are the side effects of ibuprofen?

Found 5 relevant sections from FDA drug labels:

--- [1] FDA Label — Ibuprofen — Adverse Reactions (relevance: 0.723) ---
...adverse reactions include nausea, dyspepsia, gastrointestinal bleeding...
```

### 4. With an LLM for plain-language answers

Set a HuggingFace token for AI-generated summaries:

```bash
export HUGGINGFACE_TOKEN="hf_..."
pillwise ask "Is it safe to take aspirin with warfarin?"
```

### 5. Quick search

```bash
pillwise search "acetaminophen dosage adults"
pillwise info
```

## Features

- **100% free** — OpenFDA API needs no key; sentence-transformers + FAISS run locally
- **Privacy-preserving** — Drug labels are public data; no user data leaves your machine
- **Semantic search** — Understands intent, not just keywords
- **Source citations** — Every answer shows which drug label section it came from
- **LLM-ready** — Optional HuggingFace Inference API for plain-language summaries
- **CLI-first** — Fast, scriptable, no UI dependencies

## Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
pillwise/
├── pillwise/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point
│   ├── fetcher.py      # OpenFDA API client
│   ├── indexer.py      # FAISS + sentence-transformers index
│   └── generator.py    # LLM answer generation
├── data/               # Cached labels and index (created at runtime)
├── tests/
│   ├── test_fetcher.py
│   └── test_indexer.py
├── Decisions.md
├── Flow.md
├── requirements.txt
├── setup.py
└── README.md
```

## Data Source

All drug label data comes from the [FDA National Drug Code (NDC) Directory](https://open.fda.gov/apis/drug/label/) API, which is in the public domain.

## License

MIT
