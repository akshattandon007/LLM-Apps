# Decisions.md — PillWise

## Why of every architectural choice, trade-offs, and rejected alternatives.

---

### 1. **CLI over web UI**

- **Chosen:** Command-line interface with `argparse`
- **Rejected:** Streamlit web app, Flask API, TUI with Textual
- **Why:** CLI is zero-dependency for the frontend, scriptable, composable in pipelines, and faster to build. No need for a browser or port management. Streamlit was rejected because it adds deployment complexity (must keep a server running) and the primary user is a developer running this locally.

### 2. **FAISS over ChromaDB / Pinecone / Qdrant**

- **Chosen:** FAISS (Facebook AI Similarity Search)
- **Rejected:** ChromaDB (simpler API but heavier), Pinecone (paid cloud service), Qdrant (requires running a server)
- **Why:** FAISS is local, fast, free, and mature. For a dataset of hundreds of drug labels (~thousands of chunks), FAISS in-memory search completes in milliseconds. ChromaDB was the runner-up but adds a server process dependency. Pinecone costs money — rejected outright for a free tool.

### 3. **sentence-transformers over OpenAI / Cohere embeddings**

- **Chosen:** `all-MiniLM-L6-v2` via sentence-transformers
- **Rejected:** OpenAI `text-embedding-ada-002` (paid, per-token), Cohere (paid)
- **Why:** Sentence-transformers runs locally, needs no API key, and `all-MiniLM-L6-v2` is 80MB — small enough to download and embed on any machine. Quality is within 2-3% of ada-002 for retrieval tasks. Zero ongoing cost.

### 4. **OpenFDA over other drug databases**

- **Chosen:** OpenFDA Drug Label API
- **Rejected:** DailyMed (similar but XML-heavy), Drugs@FDA (less accessible API), Wikipedia scraping (unreliable, no structure)
- **Why:** OpenFDA is free, requires no API key, returns clean JSON, and covers the complete set of FDA-approved drug labels. DailyMed's API requires pagination through XML and has slower response times. Wikipedia data is user-edited and not authoritative.

### 5. **Normalized embeddings (cosine similarity) over raw dot product**

- **Chosen:** L2-normalize embeddings, use `IndexFlatIP` (inner product = cosine similarity)
- **Rejected:** `IndexFlatL2` (Euclidean distance), raw embeddings without normalization
- **Why:** Cosine similarity is the standard metric for semantic text search — it measures angle between vectors, not magnitude. `IndexFlatIP` on normalized vectors is mathematically identical to cosine similarity and is FAISS's fastest exact search method.

### 6. **Hybrid retrieval (semantic-only in v1) over hybrid keyword+semantic**

- **Chosen:** Semantic search only (dense retrieval)
- **Rejected:** Hybrid BM25 + semantic search, re-ranking stage
- **Why:** For drug label data where each chunk is a self-contained medical fact (side effects, dosage, interaction), semantic search alone achieves strong recall. Hybrid retrieval adds complexity (need to run both indexes and fuse results) with marginal gain for this domain. Re-ranking was rejected for v1 — it's a future optimization.

### 7. **Field-level chunking over document-level or sliding-window**

- **Chosen:** Chunk by FDA label field (indications, warnings, interactions, etc.)
- **Rejected:** Whole-document embedding, fixed-size sliding window chunks
- **Why:** Drug labels have natural section boundaries (active ingredient, dosage, contraindications, adverse reactions, drug interactions). Chunking by field means a query about "side effects of ibuprofen" directly retrieves the adverse reactions section — no crossing between unrelated content. Fixed sliding windows would split sections mid-paragraph and dilute relevance.

### 8. **HuggingFace Inference API over local LLM (default)**

- **Chosen:** HF Inference API as primary LLM backend, no-LLM fallback as default
- **Rejected:** Ollama local (requires installation, 4-7GB download), OpenAI API (paid)
- **Why:** The tree is valuable even without an LLM — semantic search over drug labels is itself useful. The LLM is an optional enhancement for plain-language summarization. HF Inference API is free (rate-limited) with a token. Local models (Phi-3, TinyLlama) are documented but not required, keeping the install lightweight.

### 9. **Modular package structure over single-file script**

- **Chosen:** Separated modules: `fetcher`, `indexer`, `generator`, `cli`
- **Rejected:** Monolithic `pillwise.py` script
- **Why:** Separation of concerns — each module does exactly one thing and can be tested independently. `fetcher` handles API calls, `indexer` handles vector search, `generator` handles LLM interaction, `cli` handles I/O. Makes the code testable and maintainable.

### 10. **`setup.py` entry-point over running as `python -m`**

- **Chosen:** Console script entry point (`pillwise=pillwise.cli:main`)
- **Rejected:** `python -m pillwise`, shell wrapper script
- **Why:** After `pip install -e .`, `pillwise` becomes a system command. The user doesn't need to remember `python -m` or navigate to the project directory. Cleanest UX for a CLI tool.

### 11. **JSON local cache over live API calls on every query**

- **Chosen:** Cache fetched labels to `data/drug_labels.json`; persist FAISS index to disk
- **Rejected:** Live API call on every query, SQLite database
- **Why:** OpenFDA has rate limits and latency. Caching means `pillwise ask` completes in milliseconds after the initial fetch+index. JSON was chosen over SQLite to keep the data human-readable and easily inspectable.

### 12. **User-provided HF token via env var, not config file**

- **Chosen:** `HUGGINGFACE_TOKEN` environment variable
- **Rejected:** `.env` file, `~/.pillwise/config.yaml`, interactive prompt
- **Why:** Environment variables are the standard for API tokens — works in CI/CD, Docker, and production. No config file to maintain or accidentally commit. The token is optional, so no `--token` flag needed after export.

### 13. **Single-drug label fetch over generic search in v1**

- **Chosen:** Fetch N most common FDA labels as a batch
- **Rejected:** On-demand fetch by drug name, search-by-query API
- **Why:** The OpenFDA `/label.json?search=...` endpoint requires structured queries (e.g., `generic_name:ibuprofen`). A batch fetch of the most prescribed drugs gives broad coverage in one API call. On-demand by name requires the user to know the exact generic name — bad UX.

### 14. **`pytest` over `unittest`**

- **Chosen:** pytest for test discovery and assertions
- **Rejected:** unittest standard library
- **Why:** pytest requires less boilerplate, has better fixture support, and produces more readable failure output. The test files use plain `assert` statements with no test class scaffolding.

### 15. **pip installable package over flat scripts**

- **Chosen:** `setup.py` + `requirements.txt` for packaging
- **Rejected:** Flat `.py` files in a directory, single script
- **Why:** A pip-installable package means clean imports, version tracking, and dependency management. The `requirements.txt` makes it reproducible across environments.
