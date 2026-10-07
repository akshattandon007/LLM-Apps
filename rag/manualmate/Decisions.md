# Decisions — ManualMate

## 1. CLI tool (not web app)
- **Decision**: Build as a Python CLI using Click.
- **Rejected**: Streamlit/Flask web app — requires a running server, more deps, harder to script. CLI can be piped, automated, and used headless.
- **Rejected**: Typer — unnecessary abstraction over Click; Click is stable, well-documented, and the team already uses it in prior RAG projects.

## 2. OpenAI embeddings API (not local models)
- **Decision**: Use OpenAI `text-embedding-3-small` via the `openai` Python package.
- **Rejected**: `sentence-transformers` — requires PyTorch (~1GB+), slow on CPU, heavy dependency for a document Q&A tool. The OpenAI API key is already configured for the project environment, costs pennies, and provides 1536-dim embeddings instantly.
- **Rejected**: HuggingFace Inference API — rate-limited, adds network latency, and requires an additional API key.

## 3. GPT-4o-mini as generator (not GPT-4, not local LLM)
- **Decision**: Use `gpt-4o-mini` for answer generation.
- **Rejected**: GPT-4 — more expensive (20x cost) without meaningful quality gain for structured document QA where the answer is extractive from provided context.
- **Rejected**: Local LLM via llama.cpp/ollama — no GPU on this VPS, would be too slow for interactive use.

## 4. Numpy-based vector store (not FAISS, not ChromaDB)
- **Decision**: Store embeddings as `.npy` numpy arrays with chunk metadata as JSON.
- **Rejected**: FAISS — adds a compiled C++ dependency, overkill for a personal document store with expected <10K chunks. The M1 Mac / Linux compatibility is not guaranteed.
- **Rejected**: ChromaDB — adds another service layer, persistent files, complex config. Numpy + JSON is trivially portable, zero-install.
- **Rejected**: SQLite with sqlite-vec — more complex setup for marginal gain at this scale.

## 5. Sentence-boundary chunking (not RecursiveCharacterTextSplitter)
- **Decision**: Split on sentence boundaries using regex, with overlap.
- **Rejected**: LangChain's RecursiveCharacterTextSplitter — heavy dependency for one utility function. LangChain pulls in dozens of transitive deps.
- **Rejected**: Fixed token-length chunks — breaks mid-sentence, degrades retrieval quality. Appliance manuals contain step-by-step instructions where sentence integrity matters.
- **Rejected**: Paragraph-level chunks — too coarse for manuals where a single step may be 1-2 sentences.

## 6. Cosine similarity retrieval (not Euclidean, not MMR)
- **Decision**: Row-normalize embeddings and use dot-product (= cosine similarity).
- **Rejected**: Euclidean distance — doesn't account for vector magnitude, less effective for embedding similarity with OpenAI's normalized output space.
- **Rejected**: MMR (Maximum Marginal Relevance) — adds complexity, not needed for a small-scale personal knowledge base where diversity is naturally handled by top-k.
- **Rejected**: Hybrid TF-IDF + embedding search — adds complexity without proven benefit for full-text manuals.

## 7. Local store in ~/.manualmate (not project-relative)
- **Decision**: Store vector data and documents in `~/.manualmate/`.
- **Rejected**: Project-relative `.manualmate/` — breaks when the tool is used from different directories or multiple manual collections.
- **Rejected**: XDG_DATA_HOME — more platform-aware but `~/.manualmate` is simpler, standard for CLI tools, and consistent with the existing GardenGuide pattern.

## 8. OpenAI API key from environment (not config file)
- **Decision**: Read `OPENAI_API_KEY` from environment variables, with `.env` file fallback.
- **Rejected**: Hardcoded config file — security risk, accidentally committed to git.
- **Rejected**: Interactive prompt — breaks automation and headless use.
- **Rejected**: Only `.env` (not env var) — breaks existing setups where the key is already exported.

## 9. pypdf for PDF extraction (not pdfplumber, not pdftotext)
- **Decision**: Use `pypdf` (pure Python) for extracting text from PDF manuals.
- **Rejected**: `pdfplumber` — heavier dep (Pillow, etc.), better for table extraction which this tool doesn't need.
- **Rejected**: `pdftotext` (poppler) — requires system-level install, not portable.
- **Rejected**: `marker-pdf` or `pymupdf` — feature-rich but heavy. For well-typed appliance manuals, pypdf is sufficient.

## 10. Rich for CLI output (not plain print)
- **Decision**: Use the `rich` library for formatted console output (tables, panels, markdown).
- **Rejected**: Plain `print()` — no formatting, hard to distinguish answer from metadata.
- **Rejected**: Colorama — ANSI-only, no table rendering. Rich gives us markdown rendering for answers and tables for sources.

## 11. Standalone project under rag/ (not in extensions/)
- **Decision**: Place in `/data/LLM-Apps/rag/manualmate/`.
- **Rejected**: Root-level new repo — no need for a standalone repo; this is a standard RAG project fitting the rag/ category.
- **Rejected**: Under extensions/ — wrong category for a RAG tool.

## 12. Skipped vector store cleanup on failed ingest
- **Decision**: Keep the vector store append-only — failed ingests don't roll back partial embeddings.
- **Rejected**: Transactional ingest (all-or-nothing) — adds complexity. If an ingest fails mid-way, the user can `remove` the partial doc.
- **Rationale**: Ingests are fast (<1s for typical manuals). Partial state is acceptable for a CLI tool.

## 13. CLI command naming (short, consistent)
- **Decision**: Use imperative verbs: `ingest`, `ask`, `list`, `remove`, `clear`.
- **Rejected**: `add`, `query`, `show`, `delete`, `reset` — less descriptive for a document Q&A context.
- **Rejected**: `learn`, `teach`, `chat` — too anthropomorphic for a utility tool.

## 14. ManualMate name (not ApplianceRAG, not DocQuery)
- **Decision**: Name it "ManualMate" — suggests a companion for your manuals.
- **Rejected**: `appliance-rag` or `manual-rag` — too generic, not memorable.
- **Rejected**: `DocQuery` or `ManQa` — doesn't convey the home-appliance use case.