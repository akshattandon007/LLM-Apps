# Decisions — GardenGuide

## 1. CLI tool (not web app)
- **Decision**: Build as a Python CLI using Click.
- **Rejected**: Streamlit/Flask web app — requires a running server, more deps, harder to script. CLI can be piped and automated.
- **Rejected**: Typer — unnecessary abstraction over Click; Click is stable and well-known.

## 2. OpenAI embeddings API (not local models)
- **Decision**: Use OpenAI `text-embedding-3-small` via the `openai` Python package.
- **Rejected**: `sentence-transformers` — requires PyTorch (~1GB+), slow on CPU, heavy dependency. The OpenAI API is already available (key in .env), costs pennies, and is fast.
- **Rejected**: Free HuggingFace Inference API — rate-limited, adds network latency vs the in-project OpenAI endpoint.

## 3. GPT-4o-mini as the generator model
- **Decision**: Use `gpt-4o-mini` for answer generation.
- **Rejected**: GPT-4 — more expensive without meaningful quality gain for structured document QA.
- **Rejected**: Local LLM via llama.cpp — no GPU available, would be too slow for interactive use.

## 4. Numpy-based vector storage (not FAISS/ChromaDB)
- **Decision**: Store embeddings as a `.npy` numpy array and chunks as JSON.
- **Rejected**: FAISS — adds a compiled C++ dependency, overkill for a personal document store with <10K chunks.
- **Rejected**: ChromaDB — adds another service layer, persistent files, complex config. Numpy + JSON is trivially portable.
- **Rejected**: SQLite with sqlite-vec — more complex setup for marginal gain at this scale.

## 5. Sentence-boundary chunking (not RecursiveCharacterTextSplitter)
- **Decision**: Split on sentence boundaries using regex, with overlap.
- **Rejected**: LangChain's RecursiveCharacterTextSplitter — heavy dependency for one utility function.
- **Rejected**: Fixed token-length chunks — breaks mid-sentence, degrades retrieval quality.

## 6. Cosine similarity retrieval (not vector DB query)
- **Decision**: Row-normalize embeddings and use dot-product (= cosine similarity).
- **Rejected**: Euclidean distance — doesn't account for vector magnitude, less effective for embedding similarity.
- **Rejected**: MMR (Maximum Marginal Relevance) — adds complexity, not needed for a personal knowledge base.

## 7. Local store in ~/.gardenguide (not project-relative)
- **Decision**: Store vector data in `~/.gardenguide/`.
- **Rejected**: Project-relative `.gardenguide/` — breaks when the tool is used from different directories.
- **Rejected**: XDG_DATA_HOME — more platform-aware but `~/.gardenguide` is simpler and standard for CLI tools.

## 8. OpenAI API key from environment (not config file)
- **Decision**: Read `OPENAI_API_KEY` from environment variables.
- **Rejected**: `.env` file loader — adds `python-dotenv` dependency. Users likely already have the env var set.
- **Rejected**: Interactive setup wizard — unnecessary overhead for a power-user CLI tool.

## 9. No PDF support out of the box (conditional)
- **Decision**: Support PDF parsing only if PyMuPDF or pdfplumber is installed; fail gracefully with instructions.
- **Rejected**: Bundling PDF parsing as a hard dependency — most gardening documents are text files or markdown.
- **Rejected**: Bundling PyMuPDF — large dependency (includes compiled binaries).

## 10. Single-module CLI (not pip package)
- **Decision**: Single `gardenguide.py` entry point, importable from `src/`.
- **Rejected**: Full `pyproject.toml` package with `pip install -e .` — adds build-system overhead. The flat structure is easier to iterate and move.

## 11. No authentication/authorization
- **Decision**: No user accounts, no sharing. Single-user tool.
- **Rejected**: Multi-user support — scope creep. RAG over personal gardening docs is inherently single-user.

## 12. Interactive mode omitted (initial release)
- **Decision**: No REPL/interactive loop; everything is command-based.
- **Rejected**: Interactive shell — adds complexity (prompt_toolkit, readline). Users can ask questions one at a time.

## 13. `ask` returns both answer and source chunks
- **Decision**: Show the generated answer AND the retrieved passages.
- **Rejected**: Answer-only mode — users need to verify grounding. Transparent RAG builds trust.

## 14. Environment config overrides for model choice
- **Decision**: `GARDENGUIDE_EMBED_MODEL`, `GARDENGUIDE_GEN_MODEL`, `GARDENGUIDE_DIR` env vars.
- **Rejected**: CLI flags for model choice — too verbose. Environment variables are set once per shell.
- **Rejected**: Config file — YAML/TOML adds a parser dependency.