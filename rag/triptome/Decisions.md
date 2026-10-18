# Decisions.md — TripTome

## 1. RAG over Travel Documents (instead of yet another chatbot)

**Chosen:** A local-first RAG system that indexes your own travel guides, PDFs, and blog posts, then lets you query them with natural language.
**Rejected:** Building yet another chatbot wrapper around a generic LLM API. TripTome owns no travel data — the user brings their own documents.
**Why:** Generic LLMs hallucinate travel details (hotel prices, local transit quirks, seasonal specifics). A RAG system grounded in curated guides gives authoritative, citeable answers.

## 2. Python + CLI (not a web app)

**Chosen:** A CLI-first tool built with Python and Click.
**Rejected:** A web app (Flask/Next.js). A Docker container. A browser extension.
**Why:** The target user is a developer or traveler who has travel PDFs on their laptop. A CLI is the fastest path to value — no servers, no deployment, no browser. Adding a web UI later is possible as a thin layer.

## 3. ChromaDB for vector storage (instead of FAISS or Pinecone)

**Chosen:** ChromaDB with built-in ONNX embeddings (all-MiniLM-L6-v2).
**Rejected:** FAISS (raw, needs manual embedding management). Pinecone (cloud dependency, needs API key). Sentence-Transformers with FAISS (torch dependency is ~600MB).
**Why:** ChromaDB uses ONNX runtime (~80MB), works offline with zero external API calls, and bundles its own embeddings. The user installs `chromadb` and gets embeddings + vector search in one package. No GPU needed.

## 4. Chunk-by-paragraph with overlap (not fixed-token windows)

**Chosen:** Split text at paragraph boundaries (`\n\n`) with configurable overlap, then sentence-split oversized paragraphs.
**Rejected:** Fixed N-token sliding windows (breaks semantic units). Recursive character splitting from LangChain (heavy dependency).
**Why:** Paragraph boundaries preserve semantic meaning — a single paragraph about "Eiffel Tower opening hours" stays together. Overlap of ~50 words ensures context flows between chunks without repeating large blocks.

## 5. Local persistence (not ephemeral in-memory)

**Chosen:** ChromaDB persistent client storing data at `~/.triptome/chroma/`.
**Rejected:** In-memory ChromaDB (data lost on exit). SQLite-based custom store (more code to maintain).
**Why:** Travel research is iterative — read a guide today, ask questions tomorrow. Persistent storage means the index survives sessions. The user can also have multiple `TRIPTOME_DB_DIR` locations for different trips.

## 6. PyMuPDF (pypdf) for PDF parsing (not pdfplumber or PyMuPDF's fitz)

**Chosen:** pypdf library for PDF text extraction.
**Rejected:** pdfplumber (heavier, slower). PyMuPDF full API (larger binary, GPL license concerns).
**Why:** pypdf is pure Python, well-maintained, and extracts page-by-page text cleanly enough for travel guides (which are mostly prose, not tables). No C extensions needed.

## 7. Rich for CLI output (instead of plain print)

**Chosen:** Rich library for colored, formatted terminal output with panels and tables.
**Rejected:** Plain `print()` with ANSI codes. Textual (too heavy for a CLI tool).
**Why:** Travel answers have structure — a source table plus a Markdown answer. Rich gives us panels, tables, and Markdown rendering with minimal code. Users get clear, scannable output.

## 8. Two-tier answer generation (LLM when available, raw context fallback)

**Chosen:** Check for `OPENAI_API_KEY` or `TRIPTOME_API_KEY` — if present, generate answers via OpenAI-compatible API. If absent, show the raw retrieved chunks.
**Rejected:** Requiring an API key always (hostile to first-time users). Bundling a local LLM (Ollama — adds complexity and GPU requirements).
**Why:** First-time users should be able to try `triptome ingest` and `triptome ask` immediately without configuring anything. The raw context fallback is useful on its own (shows what the system found). Adding an API key unlocks the LLM-powered answers.

## 9. httpx for LLM API calls (not openai-python SDK)

**Chosen:** Direct httpx POST to the OpenAI-compatible `/chat/completions` endpoint.
**Rejected:** openai Python SDK (adds dependency, harder to swap providers). requests (no async future, though unused now).
**Why:** httpx keeps the dependency minimal and lets the user point `TRIPTOME_BASE_URL` at any OpenAI-compatible provider (OpenAI, Anthropic via proxy, local Ollama with OpenAI adapter, etc.) without changing code.

## 10. Configurable chunk size (not hardcoded)

**Chosen:** `--chunk-size` and `--overlap` CLI flags on `ingest`, defaulting to 500/50.
**Rejected:** Hardcoded 300-token chunks (too small for travel prose). Auto-detection based on document structure (unreliable across formats).
**Why:** Different travel guides have different granularity — a city guide wants smaller chunks (specific attractions), a country guide wants larger ones (regional summaries). Users tune per dataset.

## 11. Modular package structure (not a single script)

**Chosen:** Separate modules: `models.py`, `indexer.py`, `embedder.py`, `generator.py`, `cli.py`.
**Rejected:** Single `triptome.py` script. Monolithic `app/` directory.
**Why:** Separation of concerns makes the code testable and composable. You can use the indexer without the CLI, or the generator without the embedder. Each module has ~1-2 responsibilities.

## 12. HNSW cosine similarity (not brute-force or L2)

**Chosen:** ChromaDB's default HNSW index with cosine similarity.
**Rejected:** Brute-force L2 search (slower as index grows). No vector search (keyword-only — misses semantic matches).
**Why:** Cosine similarity is the standard for sentence embeddings — it captures topical relevance. HNSW gives O(log n) search time, which matters when the index grows to thousands of travel guide chunks.

## 13. Click for CLI framework (not argparse or typer)

**Chosen:** Click library with subcommands (ingest, ask, stats, clear).
**Rejected:** argparse (more boilerplate for subcommands). Typer (newer, fewer resources, depends on Click anyway).
**Why:** Click is battle-tested, gives automatic help/version/option parsing, and scales cleanly to our 4 subcommands. The `@click.group` pattern is standard Python CLI design.

## 14. Source deduplication in answer (not showing repeated filenames)

**Chosen:** `source_names` is built with `dict.fromkeys()` to preserve order while removing duplicates.
**Rejected:** Showing every source for every citation (repetitive when multiple chunks come from the same file). Just showing the top source (hides multi-source answers).
**Why:** A user asking "Where should I stay in Tokyo?" might get hits from "tokyo-guide.pdf" across 4 chunks. Showing "tokyo-guide.pdf" once is cleaner than 4 times. If multiple guides matched, all are listed.

## 15. Test-first with pytest (not doctests or unittest)

**Chosen:** pytest with dedicated test files per module.
**Rejected:** doctests (fine for small functions, verbose for module-level tests). unittest (boilerplate-heavy).
**Why:** pytest gives concise assertions, fixture support, and clear failure messages. Each module gets a corresponding test file focusing on its public API. Tests use temporary directories so they don't pollute the user's real collection.