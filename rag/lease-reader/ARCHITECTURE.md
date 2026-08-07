# Lease Reader — Architecture

> A RAG application that lets users upload a lease/rental agreement PDF and ask
> natural-language questions about their rights and obligations.

**Version:** 0.1.0
**Stack:** Python FastAPI / Next.js + Tailwind / FAISS / sentence-transformers / Claude (langchain-anthropic)

---

## Table of Contents

1. [High-Level System Design](#1-high-level-system-design)
2. [Data Flow: PDF Ingestion](#2-data-flow-pdf-ingestion)
3. [Data Flow: Query & Answer](#3-data-flow-query--answer)
4. [Component Details](#4-component-details)
   - 4.1 PDF Loader (`document_loader.py`)
   - 4.2 Chunker (`chunker.py`)
   - 4.3 Embedder (`embedder.py`)
   - 4.4 Vector Store (`vector_store.py`)
   - 4.5 Classifier (`classifier.py`)
   - 4.6 RAG Chain (`rag_chain.py`)
   - 4.7 API Server (`main.py`)
   - 4.8 Frontend
5. [Classification-First Retrieval](#5-classification-first-retrieval)
6. [Caveat Engine](#6-caveat-engine)
7. [API Endpoints](#7-api-endpoints)
8. [Key Design Decisions & Trade-offs](#8-key-design-decisions--trade-offs)

---

## 1. High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                       Next.js Frontend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  FileUpload   │  │  ChatPanel   │  │  AnswerCard          │  │
│  │  (drag-drop)  │  │  (messages)  │  │  (clause citations   │  │
│  └──────┬───────┘  └──────┬───────┘  │   + caveat display)  │  │
│         │                  │          └──────────────────────┘  │
│         └──────────┬───────┘                                    │
│                    │  /api/proxy/*                               │
│                    ▼                                             │
│         ┌─────────────────┐                                     │
│         │  proxy.js       │  Next.js API route → FastAPI        │
│         └─────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
                    │  HTTP
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend (main.py)                  │
│                                                                 │
│  POST /ingest  ────►  PDFLoader  ──►  Chunker  ──►  Embedder   │
│                           │                │             │       │
│                           ▼                ▼             ▼       │
│                      PyMuPDF       section-boundary    all-      │
│                      (fitz)        + domain tagging    MiniLM   │
│                                                         L6-v2    │
│                           ┌────────────────────────────────┐     │
│                           │          FAISS Index           │     │
│                           │  (IndexFlatIP + domain map)    │     │
│                           └────────────────────────────────┘     │
│                                                                 │
│  POST /query  ────►  Classifier  ──►  FAISS (domain-filtered)  │
│                         │                    │                   │
│                     keyword-based          sub-index            │
│                     domain prediction     per domain            │
│                           │                    │                │
│                           ▼                    ▼                │
│                      ┌──────────────────────────────────┐       │
│                      │  RAG Chain (rag_chain.py)        │       │
│                      │  Claude Sonnet 4 (langchain)     │       │
│                      │  + caveat engine                 │       │
│                      └──────────────────────────────────┘       │
│                                                                 │
│  GET  /health  ────►  {"status": "ok"}                         │
└─────────────────────────────────────────────────────────────────┘
```

The system is a two-tier web application:

- **Backend** (Python FastAPI): Handles PDF ingestion, text extraction, chunking,
  embedding, indexing, query classification, retrieval, and LLM-based
  answer generation.
- **Frontend** (Next.js + Tailwind CSS): Provides a drag-and-drop upload
  interface and a chat-style question-and-answer UI.

---

## 2. Data Flow: PDF Ingestion

```
PDF file  ──►  PyMuPDF (fitz) ──► RawPage[] ──► chunker ──► Chunk[]
                  │                                         │
              page-by-page                           section-boundary
              text extraction                        split, domain tag
                                                          │
                                                          ▼
                                              sentence-transformers
                                                    (all-MiniLM-L6-v2)
                                                          │
                                                          ▼
                                              FAISS IndexFlatIP
                                              (384-dim, normalized)
                                                          │
                                                          ▼
                                              Persist to disk:
                                                lease_index.faiss
                                                lease_meta.json
```

### Step-by-step

1. **PDF upload:** User uploads a PDF file via `POST /ingest` (multipart/form-data).
   The backend validates the file extension (`.pdf` only) and saves to a temporary
   file.

2. **Text extraction** (`document_loader.py`): PyMuPDF (`fitz`) extracts text
   page by page. Each page is scanned for section headers using a regex pattern
   that matches formats like `Section 4.2`, `7. PETS`, or `VI.` — accommodating
   both numbered and Roman-numeral sectioning schemes.

3. **Chunking** (`chunker.py`): The raw pages are split into chunks along
   section boundaries. Each detected section header starts a new chunk. Pages
   without clear section headers are split on paragraph boundaries
   (>3 sentences or ~500 characters). Each chunk is tagged with a legal domain
   (see [Section 4.2](#42-chunker)).

4. **Embedding** (`embedder.py`): Chunk texts are embedded using
   `sentence-transformers/all-MiniLM-L6-v2`, a lightweight model (~80 MB) that
   produces 384-dimensional normalized vectors. Fast on CPU, suitable for
   VPS deployment.

5. **Indexing** (`vector_store.py`): Embeddings are added to a FAISS
   `IndexFlatIP` (inner product) index. Since embeddings are L2-normalized,
   inner product search is equivalent to cosine similarity. A domain-to-index
   mapping (`_domain_map`) is built for filtered retrieval. The index and
   chunk metadata are persisted to disk.

6. **Singleton swap:** The module-level store singleton is replaced with the
   freshly indexed store, making it available for query requests.

---

## 3. Data Flow: Query & Answer

```
User question  ──►  classifier ──►  predicted domain (e.g. "ACCESS")
                         │
                         ▼
              FAISS search (domain-filtered)
                         │
                     top-k Chunks
                         │
                         ▼
              RAG chain (Claude via langchain-anthropic)
                         │
                     ┌────────────────────────────┐
                     │  Answer with:              │
                     │  • Plain-English answer    │
                     │  • Clause citations        │
                     │  • Caveat (if applicable)  │
                     └────────────────────────────┘
```

### Step-by-step

1. **Question arrives** via `POST /query` with `{"question": "...", "top_k": 5}`.

2. **Domain classification** (`classifier.py`): A keyword-based classifier
   predicts the legal domain (RENT, TERMINATION, ACCESS, etc.) without any
   LLM call. See [Section 5](#5-classification-first-retrieval).

3. **Domain-filtered retrieval** (`vector_store.py`): The FAISS index is
   searched only within the predicted domain's vectors. A sub-index is built
   on-the-fly by reconstructing vectors from the master index for the
   candidate domain, then `top_k` nearest neighbors are retrieved. If the
   predicted domain has no results, falls back to GENERAL or all chunks.

4. **Context assembly** (`rag_chain.py`): Retrieved chunks are formatted as
   `[Clause X — Page N]` blocks for the LLM prompt.

5. **Caveat analysis** (`rag_chain.py`): The retrieved chunks are scanned for
   external law references (e.g. "state law", "ordinance"). If found, or if
   multiple clauses apply, additional caveat instructions are injected into the
   prompt. See [Section 6](#6-caveat-engine).

6. **LLM generation** (`rag_chain.py`): Claude Sonnet 4 (via
   `langchain-anthropic`) receives the system prompt with retrieval context
   and caveat rules, then generates a plain-English answer with clause
   citations.

7. **Response assembly** (`rag_chain.py`): The LLM's text is parsed for the
   `**Caveat**` section, which is extracted into a structured field. The top 3
   cited clauses are included with their reference, text (truncated to 300
   chars), and page number.

---

## 4. Component Details

### 4.1 PDF Loader (`document_loader.py`)

**File:** `src/document_loader.py`

**Purpose:** Extract text from a lease PDF while preserving section structure.

**Key details:**
- Uses PyMuPDF (`fitz`) — a standalone PDF parser with no external dependencies
  (no Poppler, no Ghostscript).
- Processes pages sequentially, extracting text via `page.get_text("text")`.
- Scans each line for section headers using a regex:
  ```python
  r"^\s*(?i:section\s+)?(?:\d+(?:\.\d+)*|(?i:[ivxlcdm])+\.?)[\s.\-–:]+([A-Z][A-Za-z &'\-/]{3,})"
  ```
  This catches: `Section 4.2`, `4.2`, `VII.`, `7. PETS`, `Section 10 — Default`.
- Returns a list of `RawPage` dataclasses, each containing the page text and
  detected header lines.

**Why PyMuPDF?** It's a single pip install, fast on CPU, and produces clean
text output from PDFs that have text layers. For scanned PDFs (images only),
this pipeline would need an OCR layer (not implemented).

### 4.2 Chunker (`chunker.py`)

**File:** `src/chunker.py`

**Purpose:** Split extracted lease text into semantically meaningful chunks,
each tagged with a legal domain.

**Chunking strategy:**
- Section-boundary splitting: each detected section header starts a new chunk.
- Pages without clear section headers are split on paragraph boundaries
  (>3 sentences or ~500 characters).
- The first chunk before any header is labeled "Preamble".
- Returns a list of `Chunk` objects (Pydantic model): `text`, `domain`,
  `clause_ref`, `page_number`.

**Domain tagging:**
- A keyword-based matcher assigns one of 9 legal domains to each chunk.
- **Header-first priority:** The section header is checked first; only if no
  domain matches the header does the matcher fall back to the chunk body text.
  This prevents a section titled "SECURITY DEPOSIT" from being misclassified
  as RENT just because the body mentions "one month's rent".
- Domain keywords are ordered from most specific to least specific within each
  pattern.

**Supported domains:**
| Domain | Keywords |
|--------|----------|
| RENT | rent, late fee, due date, grace period, rent increase |
| TERMINATION | termination, early termination, holdover, abandon |
| ACCESS | access, enter, entry, inspect, show unit, landlord right |
| MAINTENANCE | maintenance, repair, damage, upkeep, pest control, habitability |
| PETS | pet, animal, dog, cat, service animal, ESA, emotional support |
| SUBLETTING | sublet, sublease, assignment |
| DEPOSIT | deposit, security deposit, refund, deduction |
| UTILITIES | utility, electric, water, gas, internet, trash, sewer |
| GENERAL | Fallback for unclassified content |

### 4.3 Embedder (`embedder.py`)

**File:** `src/embedder.py`

**Purpose:** Convert text chunks into vector embeddings for similarity search.

**Key details:**
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional output).
- Singleton pattern: model loaded once, reused across all requests.
- `normalize_embeddings=True`: all output vectors are L2-normalized, enabling
  cosine similarity via inner product.
- `embed_texts()`: batch-embeds a list of strings → `ndarray` shape `(N, 384)`.
- `embed_query()`: embeds a single query string → `ndarray` shape `(1, 384)`.

**Why all-MiniLM-L6-v2?** It's ~80 MB, runs well on CPU, and produces
384-dim vectors that are compact enough for efficient FAISS search. At this
scale (a single lease = 15-30 chunks), embedding quality trade-offs are
negligible.

### 4.4 Vector Store (`vector_store.py`)

**File:** `src/vector_store.py`

**Purpose:** FAISS-based vector index with domain-scoped retrieval and disk
persistence.

**Key details:**
- **Index type:** `faiss.IndexFlatIP` — exact (brute-force) inner product
  search. No quantization, no loss. At this scale (<100 chunks), exact search
  is instant and avoids any recall-vs-speed trade-off.
- **Domain map:** `_domain_map: dict[str, list[int]]` maps each domain to the
  indices of chunks belonging to it. Built during ingestion.
- **Domain-filtered search:** `search(query, domain, top_k)`:
  1. Looks up candidate indices for the domain.
  2. Reconstructs vectors from the master index for those indices.
  3. Builds a temporary `IndexFlatIP` sub-index.
  4. Searches with the query embedding.
  5. Returns unique `Chunk` objects.
- **Persistence:** `_persist()` writes the FAISS index to `lease_index.faiss`
  and chunk metadata (text, domain, clause_ref, page_number) to
  `lease_meta.json` as JSON. `load()` reconstructs the store from disk.
- **Singleton:** `get_store()` returns a module-level `LeaseVectorStore`
  instance. On ingest, `main.py` creates a fresh store and replaces the
  singleton — a pragmatic approach for a single-tenant app.

### 4.5 Classifier (`classifier.py`)

**File:** `src/classifier.py`

**Purpose:** Predict the legal domain of a user's natural-language question
using keyword heuristics.

**Key details:**
- Pure regex-based, no LLM calls. Fast (~microseconds), cheap, and
  deterministic.
- 8 domain-specific regex patterns, ordered by specificity (RENT first,
  UTILITIES last).
- Each pattern covers multiple phrasings (e.g., ACCESS matches `landlord
  enter`, `enter without notice`, `right of entry`, `access unit`, `show the
  unit`, `inspect apartment`).
- `classify_query()` returns the first matching domain, or `"GENERAL"`.
- `classify_query_with_confidence()` also returns a confidence score:
  - 0.9 if the question starts with a primary subject pattern
    (e.g., "How much...", "Can my landlord...")
  - 0.7 for secondary keyword matches
  - 0.3 for GENERAL fallback

**Why keyword-based?** An LLM-based classifier would add latency, cost, and
a dependency on the LLM being available. The 9 domains are distinct enough
that keyword overlap is rare, and the header-first priority in the chunker
compensates for edge cases. If the classifier sends a query to the wrong
domain, the fallback to GENERAL provides a safety net.

### 4.6 RAG Chain (`rag_chain.py`)

**File:** `src/rag_chain.py`

**Purpose:** Wire together retrieval, generation, and the caveat engine.

**Key details:**
- **LLM:** Claude Sonnet 4 (`claude-sonnet-4-20250514`) via
  `langchain-anthropic.ChatAnthropic`. Temperature 0.2 (low — favors
  consistent, factual answers over creativity). Max tokens 2048.
- **System prompt:** Instructs Claude to answer in plain English, cite exact
  clauses, and add caveats when needed. The prompt includes the retrieved
  chunks as context.
- **Human prompt:** Directs Claude to answer based ONLY on the provided lease
  clauses. If the clauses don't cover the question, Claude must say so rather
  than invent terms.
- **Caveat checklist:** A dynamic instruction (see
  [Section 6](#6-caveat-engine)) is appended to the human prompt when the
  retrieved chunks reference external laws or when multiple clauses apply.
- **Chain:** `prompt | llm | StrOutputParser()` — standard LangChain LCEL.

### 4.7 API Server (`main.py`)

**File:** `main.py`

**Purpose:** FastAPI application entry point.

**Key details:**
- Three endpoints: `GET /health`, `POST /ingest`, `POST /query`.
- CORS middleware configured to allow all origins (documented as "tighten in
  production").
- File upload validation: only `.pdf` files accepted, checked by extension.
- Temporary file management: uploaded PDFs are saved to a tempfile, processed,
  and deleted in a `finally` block.
- Error handling: 400 for validation errors, 500 for processing failures.

### 4.8 Frontend

**Directory:** `frontend/`

**Stack:** Next.js 14, React 18, Tailwind CSS 3.

**Pages:**
- `pages/index.js` — Main page: upload section on top, chat panel below
  (visible only after successful ingest).
- `pages/api/proxy.js` — Next.js API route that proxies all requests to the
  FastAPI backend. Handles both JSON and multipart/form-data. This avoids
  CORS issues in production while keeping the frontend dev server independent.

**Components:**
- `FileUpload.jsx` — Drag-and-drop PDF upload zone with visual feedback
  (hover state, loading spinner, success/error indicators).
- `ChatPanel.jsx` — Chat interface with message list, auto-scroll, typing
  indicator, and text input. Renders user messages as right-aligned bubbles
  and assistant responses as `AnswerCard` components.
- `AnswerCard.jsx` — Displays the LLM's answer with:
  - A colored domain badge (color-coded per legal domain)
  - The answer text (rendered with markdown line breaks)
  - Cited clauses section (clause ref, page number, truncated text)
  - Caveat box (amber-colored warning with a ⚠️ icon)

**Styling:** Tailwind CSS with custom component classes in `globals.css`.
Each domain has a distinct badge color (RENT = blue, TERMINATION = red,
ACCESS = purple, etc.).

---

## 5. Classification-First Retrieval

This is the most distinctive architectural decision in Lease Reader. Unlike
standard RAG systems that:

1. Embed the query
2. Search the entire vector index
3. (Optionally) filter or re-rank results

Lease Reader **classifies the query first**, then searches only within the
predicted domain's vectors.

### Why this approach

| Concern | Standard RAG | Classification-First |
|---------|-------------|---------------------|
| Search scope | All chunks | Domain-filtered subset |
| Relevance | Broader, may find related content | Tighter, domain-specific |
| Context cost | More chunks = more tokens | Fewer, focused chunks = cheaper |
| Leakage risk | Low | Very low — cross-domain confusion is prevented |

### How it works

```
Question: "Can my landlord enter without notice?"

  │
  ▼
Classifier (regex)  ──►  "ACCESS"
  │
  ▼
Domain map lookup:  _domain_map["ACCESS"] = [4, 5, 6, ...]
  │
  ▼
Reconstruct vectors for ACCESS indices from master FAISS index
  │
  ▼
Build temporary sub-index, search with query embedding
  │
  ▼
Return top-k chunks → all guaranteed to be ACCESS domain

If "ACCESS" has no results → fallback to "GENERAL" → fallback to all chunks
```

### Trade-offs

- **Pros:** Prevents cross-domain contamination (a question about pet policies
  won't accidentally retrieve rent-related clauses). Reduces context window
  usage. Faster retrieval on small sub-indexes.
- **Cons:** If the classifier mispredicts, the user gets results from the wrong
  domain (mitigated by the GENERAL fallback). Multi-domain questions
  (e.g., "Can I sublet and keep my deposit?") will only search one domain.
- **Acceptance:** The 9 domains are distinct enough that multi-domain questions
  are rare. When they do occur, the user can ask separate questions. The
  fallback chain ensures the system degrades gracefully.

---

## 6. Caveat Engine

The caveat engine is a two-part design that ensures answers include appropriate
disclaimers and warnings.

### Part 1: Static System Prompt Rules

The system prompt instructs Claude to ALWAYS add a caveat in these situations:

- The answer depends on state or city law
- Clauses are ambiguous or conflicting
- The answer is not a definitive yes/no
- The lease is silent on the issue

These rules are hard-coded into the system prompt, so Claude applies them
even without dynamic analysis.

### Part 2: Dynamic Chunk Analysis (`_build_caveat_instruction`)

Before sending the prompt to Claude, the RAG chain analyzes the retrieved
chunks:

```python
def _build_caveat_instruction(chunks: list[Chunk]) -> str:
    instructions = []
    # Check if chunks reference external laws
    texts = " ".join(c.text.lower() for c in chunks)
    if any(kw in texts for kw in ["state law", "local law", "ordinance", "statute"]):
        instructions.append("Warn user to check local tenant laws.")
    if len(chunks) >= 3:
        # Multiple chunks may indicate complexity
        instructions.append("Check for consistency and flag ambiguity.")
    return instructions
```

These instructions are appended to the human prompt as a **Caveat checklist**,
giving Claude specific guidance beyond the static system prompt.

### Caveat display

The caveat is displayed in the frontend as an amber-colored warning box
with a ⚠️ icon, visually distinct from the main answer.

### Example output

```
Answer: No — Section 6 requires your landlord to give at least 24 hours'
written notice before entering, except in emergencies (fire, flood, gas leak).

Caveat: Check your local tenant laws — some states require 24-48 hours'
notice and your local law may provide additional protections.
```

---

## 7. API Endpoints

### `GET /health`

Returns server status.

```json
{"status": "ok", "version": "0.1.0"}
```

### `POST /ingest`

Upload a lease PDF for indexing.

**Request:** multipart/form-data with a `file` field (PDF only).

**Response (200):**
```json
{
  "status": "ok",
  "num_chunks": 18,
  "domains_found": ["RENT", "DEPOSIT", "ACCESS", "PETS", "TERMINATION", ...],
  "message": "Successfully indexed 18 chunks across 9 legal domains."
}
```

**Error (400):** `{"detail": "Only PDF files are accepted."}`

### `POST /query`

Ask a natural-language question about the indexed lease.

**Request:**
```json
{
  "question": "Can my landlord enter without notice?",
  "top_k": 5
}
```

- `question` (required): 1–2000 characters
- `top_k` (optional, default 5): 1–20, number of chunks to retrieve

**Response (200):**
```json
{
  "answer": "**Answer:** No — Section 6 requires your landlord to give...",
  "domain": "ACCESS",
  "cited_clauses": [
    {"clause_ref": "6", "text": "Landlord may enter the premises...", "page_number": 1}
  ],
  "caveat": "Check your local tenant laws..."
}
```

**Error (400):** `{"detail": "No lease has been indexed yet. Upload a PDF first."}`

---

## 8. Key Design Decisions & Trade-offs

### Decision 1: Keyword-based classifier over LLM-based

**Chosen:** Regex keyword matching for query domain classification.

**Rejected:** Using Claude or a smaller LLM to classify questions.

**Rationale:** The 9 legal domains are distinct enough that keyword overlap is
rare. A regex classifier runs in microseconds, costs nothing, and has no
external dependency. An LLM-based classifier would add 1-3 seconds of latency
and $0.001-0.003 per query. The fallback to GENERAL on no match provides
graceful degradation.

### Decision 2: Section-boundary chunking over fixed-size windows

**Chosen:** Split on section headers detected by regex.

**Rejected:** Fixed-size token windows (e.g., 512 tokens with overlap).

**Rationale:** Lease agreements are structured documents with clear section
boundaries. Fixed-size windows would split clauses across chunks, requiring
reassembly or causing context loss. Section-boundary chunking preserves
semantic units and makes clause citation straightforward.

### Decision 3: Domain-filtered sub-index over FAISS metadata filtering

**Chosen:** Reconstruct vectors and build a temporary sub-index per domain.

**Rejected:** Using FAISS's `IDSelector` or storing metadata in the index.

**Rationale:** At the scale of a single lease (<100 chunks), reconstructing
vectors and building a sub-index is effectively instant. The code is simpler
and more readable than working with FAISS filter infrastructure. For larger
corpora (1000+ chunks), this approach would need to be revisited.

### Decision 4: FAISS IndexFlatIP (exact) over HNSW/IVF

**Chosen:** Exact brute-force inner product search.

**Rejected:** Approximate nearest neighbor (ANN) indexes.

**Rationale:** With <100 vectors, exact search completes in microseconds.
ANN indexes add complexity (parameter tuning, memory overhead) with no
benefit at this scale.

### Decision 5: Module-level store singleton with replace-on-ingest

**Chosen:** A global `_store` variable that gets replaced on each ingest.

**Rejected:** Database-backed persistence, multi-tenant store management.

**Rationale:** Lease Reader is a single-tenant, single-lease application.
The singleton pattern keeps the code simple. The explicit "hack" comment
in the code signals that this is a deliberate choice for the current
deployment model, not a design recommendation for multi-tenant scaling.

### Decision 6: LangChain over direct Anthropic SDK

**Chosen:** `langchain-anthropic` with `ChatPromptTemplate` and
`StrOutputParser`.

**Rejected:** Calling the Anthropic API directly.

**Rationale:** LangChain provides prompt templates, output parsing, and a
standardized interface. The chain is simple enough that the LangChain overhead
is minimal. If the LLM provider changes, switching is a single import change.

### Decision 7: No streaming

**Chosen:** Request-response (no SSE/WebSocket streaming).

**Rejected:** Streaming the LLM response token by token.

**Rationale:** Adds significant frontend complexity (SSE parsing, incremental
rendering, interruption handling). The current non-streaming approach is
simple, reliable, and the 2-5 second generation time is acceptable for a
research/utility tool. Streaming can be added as a future enhancement.

### Decision 8: Next.js proxy pattern over direct CORS

**Chosen:** `/api/proxy/` route in Next.js forwards to FastAPI.

**Rejected:** Having the frontend call the FastAPI backend directly.

**Rationale:** The proxy pattern avoids CORS configuration entirely in
production. The frontend and backend can be deployed on different ports during
development (Next.js: 3000, FastAPI: 8000) without issues. The proxy handles
both JSON and multipart uploads correctly.

---

## Project Structure

```
rag/lease-reader/
├── main.py                       # FastAPI server entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── .gitignore
├── README.md                     # Quick start guide
├── ARCHITECTURE.md               # This file
├── src/
│   ├── __init__.py
│   ├── models.py                 # Pydantic request/response models
│   ├── document_loader.py        # PyMuPDF text extraction
│   ├── chunker.py                # Section-boundary chunking + domain tagging
│   ├── embedder.py               # sentence-transformers embedding
│   ├── vector_store.py           # FAISS index + domain-filtered search
│   ├── classifier.py             # Query-to-domain classification
│   └── rag_chain.py              # Retrieval, generation, caveat engine
├── tests/
│   ├── __init__.py
│   └── test_smoke.py             # 20 unit + integration + e2e tests
├── data/
│   ├── generate_sample_lease.py  # Synthetic 15-clause lease PDF generator
│   └── sample_lease.pdf          # Generated sample lease
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── pages/
    │   ├── _app.js
    │   ├── index.js              # Upload + chat UI
    │   └── api/proxy.js          # Next.js → FastAPI proxy
    ├── components/
    │   ├── FileUpload.jsx         # Drag-and-drop PDF upload
    │   ├── ChatPanel.jsx          # Chat message list
    │   └── AnswerCard.jsx         # Answer with citations + caveat
    └── styles/
        └── globals.css            # Tailwind + custom component classes
```

---

## Testing

The test suite (`tests/test_smoke.py`) contains 20 tests organized into:

| Test Class | Type | Count | Description |
|-----------|------|-------|-------------|
| `TestDocumentLoader` | Unit | 2 | Page extraction, header detection |
| `TestChunker` | Unit | 3 | Chunk count, domain coverage, refs |
| `TestEmbedder` | Unit | 1 | Shape and normalization of embeddings |
| `TestClassifier` | Unit | 8 | Parametrized domain classification |
| `TestVectorStore` | Unit | 1 | Ingest and domain-filtered search |
| `TestAPI` | Integration | 4 | Health, ingest, query, error handling |
| `TestEndToEnd` | Integration | 1 | Full RAG pipeline (skipped without API key) |

The end-to-end test is automatically skipped if `ANTHROPIC_API_KEY` is not
set, allowing the unit/integration tests to run in CI without credentials.

---

## Future Considerations

- **Multi-tenant store:** Replace the singleton with a user-scoped or
  session-scoped store.
- **Streaming responses:** Add SSE support for real-time token streaming.
- **OCR support:** Add Tesseract or similar for scanned PDFs.
- **State-law database:** Link caveats to state-specific tenant law databases
  for more precise warnings.
- **Multi-document support:** Index multiple leases and add a document selector
  to the UI.
- **Hybrid search:** Combine dense embeddings with sparse (BM25) retrieval
  for improved recall on specific terms.