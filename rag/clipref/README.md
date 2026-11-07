# 🔖 ClipRef — Your Personal Bookmark & Clipping Search Engine

> *"I know I saved that article somewhere... ClipRef will find it."*

**ClipRef** is a CLI-first RAG (Retrieval-Augmented Generation) tool that indexes your saved bookmarks, web clippings, article highlights, and reading notes — then lets you ask natural-language questions and get grounded, cited answers.

No more digging through bookmarks folders. No more "I know I read that somewhere." Just ask.

---

## ✨ Features

- **📂 Index any text folder** — markdown, plain text, HTML, even exported bookmarks
- **🔍 Semantic search** — find content by meaning, not just keywords
- **💬 Ask natural questions** — "What was that article about serverless patterns?" — get an answer with sources
- **🔗 Citation-backed answers** — every answer links back to the original source file
- **🧠 Local-first** — embeddings run locally via sentence-transformers; no API key required for search
- **⚡ Optional LLM answers** — bring your own API key for AI-generated answers (OpenAI/OpenRouter compatible)
- **📦 Persistent index** — built on ChromaDB, survives restarts
- **🔧 CLI-first** — fast, scriptable, no bloated UI

---

## 📦 Installation

```bash
# Clone or copy the project
cd rag/clipref/
pip install -r requirements.txt
```

**Requirements:** Python 3.10+, 4 GB RAM (for embedding model).

---

## 🚀 Quick Start

### 1. Index your clippings

```bash
# Index a directory of markdown notes and bookmarks
python -m clipref index ~/my-clippings/

# Or index a specific set of files
python -m clipref index ./articles/ ./highlights/
```

### 2. Search without LLM

```bash
# Just find relevant clips
python -m clipref search "serverless database patterns"
```

### 3. Ask with AI answers (optional — needs API key)

```bash
# Get an AI-generated answer with citations
python -m clipref ask "What did I save about microservices communication patterns?"

# Configure an API key
export OPENAI_API_KEY="sk-..."  # OpenAI or OpenRouter compatible
# Or add to ~/.clipref.env
```

---

## 📖 Usage Guide

### `clipref index <paths...>`

Scans directories/files for text content, chunks them, embeds them, and stores in ChromaDB.

**Options:**
- `--db <path>` — custom database location (default: `~/.clipref/`)
- `--chunk-size <n>` — chunk size in characters (default: 512)
- `--chunk-overlap <n>` — overlap between chunks (default: 64)
- `--model <name>` — embedding model name (default: `all-MiniLM-L6-v2`)
- `--glob <pattern>` — file pattern to match (default: `*.md *.txt *.html`)

### `clipref search <query>`

Searches the indexed clips and returns the most relevant chunks with source metadata.

**Options:**
- `--top-k <n>` — number of results (default: 5)
- `--db <path>` — custom database location

### `clipref ask <question>`

Same as search, but also generates an AI answer grounded in the retrieved clips. Requires an API key.

**Options:**
- Same as search, plus:
- `--model <name>` — LLM model for answers (default: `google/gemini-2.0-flash-exp:free`)
- `--no-llm` — fall back to pure search even if API key is available
- `--system-prompt <text>` — custom system prompt for answer generation

### `clipref stats`

Show index statistics: document count, chunk count, database size.

### `clipref drop`

Delete the entire index and start fresh.

---

## 📁 Supported Formats

| Format | Description | Auto-detected |
|--------|-------------|:---:|
| `.md` | Markdown files (Obsidian, Bear, etc.) | ✅ |
| `.txt` | Plain text | ✅ |
| `.html` / `.htm` | HTML pages (bookmark exports) | ✅ |
| `.bookmarks` | Browser bookmark HTML exports | ✅ |
| `.json` | JSON files with text content | ✅ |

Directories are scanned recursively. Hidden files and binary files are skipped.

---

## 🧪 Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=clipref -v
```

---

## 🔧 Configuration

ClipRef checks these locations for configuration:

1. Environment variables (highest priority)
2. `~/.clipref.env` — a `.env` file in your home directory
3. `./.clipref.env` — a `.env` file in the current directory

**Available env vars:**

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | API key for LLM answers (OpenAI or OpenRouter) |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` | API endpoint base URL |
| `CLIPREF_DB_DIR` | `~/.clipref/` | ChromaDB persistence directory |
| `CLIPREF_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer embedding model |
| `CLIPREF_CHUNK_SIZE` | `512` | Chunk size in characters |
| `CLIPREF_CHUNK_OVERLAP` | `64` | Overlap between consecutive chunks |
| `CLIPREF_TOP_K` | `5` | Default number of search results |

---

## 📂 Project Structure

```
clipref/
├── README.md              # This file
├── Decisions.md           # Architectural decisions & trade-offs
├── Flow.md                # Execution flow & dependency graph
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
├── clipref/
│   ├── __init__.py        # Package init & version
│   ├── __main__.py        # CLI entry point (python -m clipref)
│   ├── cli.py             # Argument parser & command dispatch
│   ├── indexer.py         # File scanning, chunking, embedding, storage
│   ├── searcher.py        # Query embedding, retrieval, LLM answer generation
│   ├── models.py          # Data classes & type definitions
│   └── utils.py           # File I/O, config, hashing helpers
├── tests/
│   ├── test_indexer.py    # Indexer unit tests
│   ├── test_searcher.py   # Searcher unit tests
│   └── test_utils.py      # Utils unit tests
└── examples/
    └── sample_clips.md    # Example clippings file
```

---

## ⚠️ Limitations

- **English-focused** — embedding models perform best on English text
- **Text only** — no image or PDF parsing (PDF must be converted to text first)
- **Single user** — one index at a time per database directory
- **LLM answers require an API key** — retrieval works without one; answer generation doesn't

---

## 📄 License

MIT — do what you want with it.