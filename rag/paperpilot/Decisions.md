# Decisions Log — PaperPilot

## Why these decisions were made and what was rejected

### 1. Project scope: Abstract-level RAG instead of full-text PDF RAG

**Context:** arXiv papers are available as PDF. Full-text extraction would give richer answers.

**Decision:** Use paper abstracts (from arXiv API metadata) as the text corpus instead of downloading and parsing full PDFs.

**Rejected:**
- **Full PDF download + OCR/text extraction**: Would require PyMuPDF/pdfplumber, add dependency weight, and dramatically increase latency (downloading + parsing PDFs takes 5-30s per paper). Abstracts are 10-30 sentences — enough for meaningful RAG in this initial version.
- **Hybrid approach**: Start with abstracts, lazily fetch PDF text on demand. Adds complexity without proving the core RAG loop first.

**Trade-off:** Users get well-grounded answers on paper scope/contributions but not on experimental details, code, or results sections. Full-text support is documented as a future enhancement.

### 2. Embedding model: all-MiniLM-L6-v2 over alternative sentence-transformers models

**Context:** Sentence-transformers offers many models with different speed/quality trade-offs.

**Decision:** Use `all-MiniLM-L6-v2` (384-dim, fast, small).

**Rejected:**
- **all-mpnet-base-v2** (768-dim, higher accuracy but 4× slower, larger download). For abstract-length texts, MiniLM's quality is sufficient.
- **BAAI/bge-small-en-v1.5**: Good quality but larger download and less commonly cached.
- **OpenAI embeddings API**: Requires API key, adds latency, creates a network dependency. Defeats the "all local" goal.

**Trade-off:** Slightly lower retrieval accuracy on nuanced queries. Mitigated by using `k=5` context chunks so the LLM has enough signal.

### 3. Similarity search: numpy dot-product over FAISS

**Context:** FAISS is the standard library for vector similarity search at scale.

**Decision:** Use numpy dot-product for cosine similarity (simplest possible approach).

**Rejected:**
- **FAISS**: Requires a separate install (`faiss-cpu`), involves more complex index management, and is overkill for <10K chunks (our expected scale). FAISS starts to matter at 100K+ vectors.
- **scikit-learn cosine_similarity**: Works but adds an import and matrix construction overhead. Numpy dot-product on normalized embeddings is mathematically identical.

**Trade-off:** O(n) scan instead of FAISS's approximate nearest neighbour search. Fine for hundreds to low thousands of chunks.

### 4. Persistence: JSON + numpy .npy over SQLite

**Context:** The index needs to survive between sessions.

**Decision:** Store chunk metadata as JSON and embeddings as numpy .npy files in `~/.paperpilot/`.

**Rejected:**
- **SQLite via sqlite3/sqlite-vec**: Adds a query interface we don't need. JSON is human-readable and the embedding matrix is dense, so .npy is the most compact format.
- **ChromaDB/LanceDB**: Heavy dependencies for a simple single-user local index. Overkill.
- **Pickle**: Security concerns with loading untrusted data.

**Trade-off:** No incremental saving (full save each time). With a max of a few hundred chunks, this is fine.

### 5. LLM integration: OpenRouter via OpenAI SDK over direct API calls

**Context:** The answer generation needs an LLM. OpenRouter provides access to many models through an OpenAI-compatible API.

**Decision:** Use the OpenAI Python SDK configured to point at the OpenRouter/nexos.ai base URL.

**Rejected:**
- **Direct httpx calls to OpenRouter API**: Requires manually constructing request/response handling, auth headers, and error handling. The OpenAI SDK handles all of this.
- **Local model (Ollama/llama.cpp)**: Would require downloading a 7B+ model, significant RAM/disk, and complex setup. Not practical for a clone-and-run project.
- **Anthropic SDK**: Another option but OpenRouter supports more model choices.

**Trade-off:** Requires an API key and internet for answer generation. Search + indexing works fully offline.

### 6. Sentence-chunking over fixed-token or paragraph-level chunking

**Context:** Abstracts range from 2 sentences to 30+ sentences. Chunking strategy impacts retrieval quality.

**Decision:** Group abstract sentences into chunks of 3, splitting on sentence boundaries.

**Rejected:**
- **Fixed-token chunks (e.g., 256 tokens)**: Could split sentences mid-way, making retrieval contexts unnatural.
- **Whole-abstract-as-one-chunk**: Too coarse for retrieval — a single abstract covers multiple topics and the similarity signal dilutes.
- **Recursive character splitting**: Good for variable-length texts but adds complexity. Sentence grouping is simple and produces natural chunks.

**Trade-off:** Chunks are variable length. For very short abstracts (<3 sentences), they become one chunk, which is fine.

### 7. CLI-first over web UI

**Context:** The target user is a developer/researcher who wants quick terminal access.

**Decision:** Build a CLI interface via `__main__.py` using argparse.

**Rejected:**
- **Streamlit/Gradio web UI**: Adds heavy dependencies, requires running a server, and shifts focus from the core RAG functionality. A web UI can be added in a future iteration.
- **FastAPI + React**: Way too heavy for a research tool.

**Trade-off:** Less visual appeal but faster to use. The CLI is scriptable and composable with other tools.

### 8. Mock-based tests over integration tests hitting live APIs

**Context:** Tests need to run offline and be deterministic.

**Decision:** Use `httpx.MockTransport` for HTTP mocking and `unittest.mock.patch` for LLM mocking.

**Rejected:**
- **Live API tests**: Require internet, arXiv rate-limiting compliance (3s delay), and an API key for LLM. Would fail in CI/offline environments.
- **VCR.py-based recording**: Stores cassettes of real API calls. Adds large binary files to the repo.

**Trade-off:** Tests only verify our code, not API compatibility. If arXiv API changes the XML schema, tests pass but real usage breaks. Mitigated by the small surface area (the `_parse_feed` function).

### 9. arXiv API over Semantic Scholar for paper metadata

**Context:** Both arXiv and Semantic Scholar offer free APIs for paper metadata.

**Decision:** Use arXiv API as the primary source.

**Rejected:**
- **Semantic Scholar API**: Returns JSON (easier to parse) and includes citation counts. But it has a 1 req/s rate limit, requires a heavier query structure, and coverage is broader than arXiv (includes non-arXiv papers).
- **Hybrid**: Use arXiv for search, Semantic Scholar for enrichment (citation data). Adds complexity without proving the core flow.

**Trade-off:** No citation counts or recommendation data. Documented as a future enhancement.

### 10. Paper-last-indexing over pre-built academic corpus

**Context:** Building a RAG system typically needs a corpus.

**Decision:** Users build their index from scratch by searching and ingesting papers they choose.

**Rejected:**
- **Pre-packaged corpus of popular arXiv categories**: Would make the initial `pip install` huge (hundreds of MB), and most users want different papers.
- **Cached popular queries**: Could be a future addition but adds cache-invalidation complexity.

**Trade-off:** First use requires a search + ingest step (a few seconds to fetch + embed 10 papers). Not a problem for the target user.