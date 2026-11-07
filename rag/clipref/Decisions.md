# Decisions — ClipRef

> Architectural decisions, trade-offs, and rejected alternatives.

---

## 1. CLI-first vs Web UI

**Chosen:** CLI-first (argparse, no web server)  
**Rejected:** FastAPI + React web app, TUI (Textual)

**Why:** The user runs headless cron jobs and terminal sessions on a VPS. A CLI tool requires no browser, no port binding, no process management. A web UI would add 200+ lines of server code, CORS, and frontend dependencies that would never be used in this environment. TUI was rejected because it adds a dependency (Textual) and doesn't compose well with pipes and scripts.

---

## 2. Python vs TypeScript/Go/Rust

**Chosen:** Python 3  
**Rejected:** TypeScript (Node.js), Go binary, Rust

**Why:** Python has the richest ecosystem for RAG: sentence-transformers for embeddings, ChromaDB for vector storage, and the openai library for LLM calls. TypeScript's embedding ecosystem is less mature. Go and Rust would need bindings or CGo for sentence-transformers. Python also matches the rest of the LLM-Apps monorepo, keeping maintenance uniform. The performance penalty vs Go/Rust is irrelevant for a CLI tool that runs once per query, not in a hot loop.

---

## 3. sentence-transformers vs API-based embeddings

**Chosen:** sentence-transformers (local, all-MiniLM-L6-v2)  
**Rejected:** OpenAI embeddings API, Voyage AI, Jina AI embeddings

**Why:** Local embeddings work offline, cost nothing, have no rate limits, and don't leak data to a third party. all-MiniLM-L6-v2 is 80 MB, runs on CPU, and produces 384-dim vectors — small enough for ChromaDB with thousands of documents. The quality is ~90% of the best API embeddings for semantic search. API embeddings add latency, cost, and a failure mode (API down) that breaks the core feature. The model is downloaded once on first use and cached.

---

## 4. ChromaDB vs FAISS vs SQLite-lancedb

**Chosen:** ChromaDB  
**Rejected:** FAISS (flat index), SQLite + sqlite-vec, LanceDB

**Why:** ChromaDB is already installed in the environment (1.5.9), handles persistence automatically, supports metadata filtering and collection management out of the box. FAISS would need a separate persistence strategy (write/load index files) and doesn't natively associate metadata with vectors. SQLite + sqlite-vec is promising but not installed and adds a build step. LanceDB is heavy for this use case. ChromaDB is the zero-config choice that "just works" for fewer than 100K documents.

---

## 5. 512-char chunks with 64-char overlap vs larger/smaller

**Chosen:** 512 characters / 64 overlap  
**Rejected:** 256/32 (too short), 1024/128 (too long), paragraph-level chunking

**Why:** 512 characters (~100 tokens) is the sweet spot for semantic search on article clippings: long enough to contain a complete idea or paragraph, short enough that the top 5 results fit in a typical LLM context window. The 64-char overlap prevents information loss at chunk boundaries. Paragraph-level chunking was rejected because markdown headings and HTML structure vary wildly across user files — a simple character-based split is more robust.

---

## 6. Recursive directory walk vs explicit file list

**Chosen:** Recursive `Path.rglob()` with glob filtering  
**Rejected:** Explicit file list only, inotify watch

**Why:** Users will dump entire directories of notes. `Path.rglob()` with `*` pattern matching lets them pass one path and index everything. Explicit file lists are supported as an alternative. inotify was rejected because real-time watching is out of scope — ClipRef indexes on demand.

---

## 7. ChromaDB's built-in `query()` vs custom retrieval pipeline

**Chosen:** ChromaDB's `collection.query()` with distance sorting  
**Rejected:** Custom FAISS search + metadata join, hybrid BM25+vector

**Why:** For a personal bookmark index (<10K documents), Chroma's built-in `query()` with cosine distance and `n_results` is fast enough (~10ms per query) and handles the metadata join automatically. A hybrid BM25+vector pipeline (e.g., Reciprocal Rank Fusion) would improve recall for exact-term queries but adds complexity (separate BM25 index, fusion logic). If needed later, hybrid search can be layered on top without breaking the existing API.

---

## 8. OpenAI-compatible API for LLM answers vs local LLM

**Chosen:** Configurable OpenAI-compatible API (OpenRouter/OpenAI)  
**Rejected:** Local LLM (Ollama, llama.cpp)

**Why:** A local LLM requires 4-16 GB RAM and GPU or fast CPU, which may not be available on the target VPS. The OpenAI-compatible interface works with free/cheap API models (Gemini Flash, Llama 3 via OpenRouter) and costs cents per month for light use. The integration is a single API call via the `openai` library — 50 lines of code. Users who want local can point OPENAI_BASE_URL at their own Ollama instance.

---

## 9. Single CLI binary module vs pip package

**Chosen:** `python -m clipref` via `clipref/__main__.py`  
**Rejected:** pip installable package, standalone PyInstaller binary, shell script

**Why:** `python -m clipref` works immediately after cloning — no install step, no PATH management, no PyInstaller build. A pip package needs `pip install -e .` or `pip install .` which adds friction. A standalone binary would need PyInstaller + PyTorch bundling (hundreds of MB). The `-m` pattern matches the rest of the repo (see: `recall`, `manualmate`, etc.).

---

## 10. JSON-based config vs YAML/TOML/INI

**Chosen:** `.env` file (dotenv format) + environment variables  
**Rejected:** YAML config file, TOML, JSON, INI

**Why:** `.env` files are the de facto standard for configuring tools with API keys. They can also set non-secret config. Environment variables take priority, matching the 12-factor app pattern. YAML/TOML/JSON would require an extra dependency or more parsing code. The `.env` format is already familiar from Docker/Heroku/Hermes workflows.

---

## 11. No progress bar vs rich/TQDM

**Chosen:** Simple print statements for progress  
**Rejected:** TQDM progress bar, Rich live display

**Why:** Indexing 100 files takes <5 seconds on a modern CPU. A progress bar adds a dependency (tqdm or rich) for a marginal UX improvement on a headless CLI. Simple `print(f"Indexing {n} files...")` is sufficient. If indexing grows to thousands of files, TQDM can be added without breaking the API.

---

## 12. UUID-based document IDs vs filename-based

**Chosen:** SHA-256 hash of file path + modification time  
**Rejected:** UUID4, filename as ID, sequential integer

**Why:** A hash-based ID ensures idempotent re-indexing: if the same file with the same content is indexed twice, it overwrites rather than duplicating. UUID4 would create a new ID every time, causing duplicates on re-index. Filenames aren't unique (two files with the same name in different dirs). Sequential integers don't survive database resets.

---

## 13. Metadata model (source file, path, timestamp) vs minimal

**Chosen:** Store `source_file`, `source_path`, `file_hash`, `chunk_index`, `indexed_at` per chunk  
**Rejected:** Store only text + distance

**Why:** Citations are the key differentiator — "here's your answer, and here's the exact file it came from." Without source metadata, ClipRef is just a vector search engine. The metadata also enables `clipref stats` to report document counts and `clipref drop` to identify stale entries.

---

## 14. Tests: pytest with fixtures vs unittest

**Chosen:** pytest with temporary directory fixtures  
**Rejected:** unittest.TestCase, doctest, no tests

**Why:** pytest's `tmp_path` fixture makes it trivial to test file I/O without polluting the real filesystem. The `capsys` fixture captures CLI output for testing print statements. unittest.TestCase is more verbose and doesn't compose fixtures as cleanly. No tests was rejected because the RAG pipeline has three distinct stages (scan→chunk→embed→store) that each benefit from regression testing.

---

## 15. Async vs sync IO

**Chosen:** Synchronous (blocking)  
**Rejected:** asyncio with aiofiles

**Why:** The I/O-bound work (reading files, calling the embedding model, querying ChromaDB) is not latency-sensitive — a user waits for the command to complete. Async adds complexity (async/await throughout, need for `asyncio.run()` wrappers) for zero UX benefit. The embedding model call (sentence-transformers) is CPU-bound anyway. If streaming LLM answers are desired later, the LLM call can be async while the rest stays sync.