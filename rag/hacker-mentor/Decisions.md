# Decisions — Hacker Mentor

## 1. Use Algolia HN API over Firebase API
- **Decision:** Use the Algolia HN Search API for fetching stories and comments
- **Alternatives considered:** HN Firebase API (real-time, but requires walking the entire comment tree)
- **Why:** Algolia provides structured search with ranking, pagination, and filtering out of the box. Firebase API would require recursive fetching of every comment child, which is slower and more complex. Algolia also returns HTML-stripped text (mostly), reducing preprocessing.

## 2. Use sentence-transformers for embeddings
- **Decision:** Use `all-MiniLM-L6-v2` via sentence-transformers for generating embeddings
- **Alternatives considered:** OpenAI Embeddings API (paid, requires API key), TF-IDF (no semantic understanding), local LLM embeddings (too slow)
- **Why:** all-MiniLM-L6-v2 is small (~80MB), fast, free, and produces 384-dim embeddings that work well with FAISS. No API key needed — fully offline after model download.

## 3. Use FAISS IndexFlatIP (Inner Product) for vector search
- **Decision:** Use IndexFlatIP with normalized embeddings (equivalent to cosine similarity)
- **Alternatives considered:** IndexFlatL2 (Euclidean distance), HNSW (approximate, faster but less accurate)
- **Why:** With normalized embeddings, inner product = cosine similarity, which is the standard metric for semantic similarity. FlatIP is exact (no approximation errors) and sufficient for our dataset size (<10K documents). HNSW would add complexity without meaningful benefit at this scale.

## 4. Separate ingest and query as independent scripts
- **Decision:** Split ingest and query into separate Python modules with a unified CLI wrapper
- **Alternatives considered:** Monolithic script, Streamlit web app, FastAPI backend
- **Why:** Separation of concerns — ingestion is a batch operation, query is interactive. A CLI-first approach keeps it simple, testable, and composable. Users can ingest once and query many times without re-fetching data.

## 5. Store index and metadata as files in a `data/` directory
- **Decision:** Save FAISS index as binary file and metadata as JSON in `data/` subdirectory
- **Alternatives considered:** SQLite, in-memory only, pickle serialization
- **Why:** FAISS has its own efficient binary format for indices. JSON for metadata is human-readable, debuggable, and can be edited if needed. The `data/` dir is gitignored to avoid committing large binary files.

## 6. Use IndexIDMap for document identity
- **Decision:** Wrap the FAISS index in IndexIDMap to associate integer IDs with embeddings
- **Alternatives considered:** Sequential array indexing, UUID-based mapping
- **Why:** IndexIDMap provides a clean mapping between FAISS internal vectors and our metadata dictionary. Sequential indexing would work but is less explicit about the mapping.

## 7. Skip LLM answer synthesis for v1
- **Decision:** Return ranked document excerpts without LLM-generated answers
- **Alternatives considered:** Use Ollama or an API to synthesize an answer from retrieved chunks
- **Why:** v1 focuses on retrieval quality. LLM synthesis adds latency, cost, and potential hallucination. Users can read the actual HN comments directly. A future version can add optional LLM synthesis.

## 8. Strip HTML from Algolia comment text
- **Decision:** Replace HTML tags with markdown equivalents in comment text
- **Alternatives considered:** Use BeautifulSoup for full HTML parsing, keep raw HTML
- **Why:** Algolia returns comments with HTML tags (<p>, <i>, <code>, etc.). Replacing them with markdown equivalents preserves readability without adding an external dependency. The conversion is simple enough that a few `str.replace()` calls suffice.

## 9. Filter comments by points > 0
- **Decision:** Only include comments with at least 1 point
- **Alternatives considered:** Include all comments, filter by > 2 points
- **Why:** Zero-point comments are often unanswered questions, spam, or low-effort replies. Excluding them improves index quality. >2 would be too aggressive for newer stories where even good comments may have few points.

## 10. Batch embedding with progress bar
- **Decision:** Use sentence-transformers' batch encoding with `show_progress_bar=True`
- **Alternatives considered:** Embed one document at a time, use multiprocessing
- **Why:** sentence-transformers handles batching internally with efficient GPU/CPU utilization. A progress bar gives user feedback during the (potentially slow) embedding step. Multiprocessing would add complexity with minimal gain since the model already uses multiple cores.

## 11. Normalize embeddings for cosine similarity
- **Decision:** Pass `normalize_embeddings=True` to sentence-transformers and use inner product search
- **Alternatives considered:** Store unnormalized vectors and use cosine similarity in search
- **Why:** Normalizing at encode time means the FAISS inner product search directly gives cosine similarity scores. This avoids having to compute cosine similarity manually during search, keeping query time fast.

## 12. Use `data/` as default data directory
- **Decision:** Default data directory is `data/` relative to the project root
- **Alternatives considered:** `~/.hacker-mentor/`, `/tmp/`, configurable path
- **Why:** Relative path keeps the project self-contained. Users who want a different path can symlink. The directory is in .gitignore so the index doesn't get committed.

## 13. Rate limit API calls with time.sleep
- **Decision:** Add 0.3s delay between story fetches
- **Alternatives considered:** No rate limiting, exponential backoff on 429
- **Why:** The Algolia API is generous but being polite avoids issues. 0.3s between stories = ~3s for 10 stories = negligible. For 200 stories it's a minute, which is still fast enough.
