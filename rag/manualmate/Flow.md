# Flow — ManualMate

## Module Dependency Graph

```
manualmate.py (CLI entry point)
    ↓ calls into
src/cli.py (Click command group)
    ├── ingest <file>        → rag_engine.ingest()
    ├── ask <question>       → rag_engine.ask()
    ├── list_                → rag_engine.list_docs()
    ├── remove <doc>         → rag_engine.remove_doc()
    └── clear                → rag_engine.clear()

src/rag_engine.py (ManualMateRAG class)
    ├── ingest()             → doc_loader.load_document()
    │                          → doc_loader.chunk_document()
    │                          → _embed() → openai.Embeddings.create()
    │                          → vector_store.add_chunks()
    │                          → vector_store.store_doc_text()
    │
    ├── ask()                → query() → _embed_single() → openai.Embeddings.create()
    │                          → vector_store.search()
    │                          → openai.Chat.Completions.create()
    │
    ├── list_docs()          → vector_store.list_docs()
    ├── remove_doc()         → vector_store.remove_doc()
    └── clear()              → vector_store.clear()

src/doc_loader.py
    ├── load_document()      → Path.exists() check
    │                          → _load_pdf() (pypdf) or Path.read_text() (.txt)
    │
    ├── chunk_text()         → re.split() — sentence-boundary splitting
    │                          → long-sentence clause splitting
    │                          → overlap detection (keep trailing sentences)
    │
    └── chunk_document()     → chunk_text() → List[Chunk] objects

src/vector_store.py (VectorStore class)
    ├── add_chunks()         → numpy.vstack() + JSON persist
    ├── search()             → numpy matrix ops (cosine similarity)
    │                          → row-normalize → dot-product → argsort → top-k
    ├── remove_doc()         → list comprehension + numpy slice
    ├── list_docs()          → counter dict from self.chunks
    ├── clear()              → delete data + remove files
    └── _save() / _load()    → JSON + .npy disk I/O

src/models.py
    └── Chunk, SearchResult, QueryResult, IngestResult — dataclasses
```

## Call Chain — `manualmate ingest fridge-manual.pdf`

```
manualmate.py:main()
  → cli()  [Click group]
    → ingest("fridge-manual.pdf")
      → ManualMateRAG.ingest("fridge-manual.pdf")
        → doc_loader.load_document("fridge-manual.pdf")
          → Path.exists() check
          → Path.suffix → ".pdf" → _load_pdf()
            → pypdf.PdfReader → page.extract_text() for each page
            → return (text, "fridge-manual.pdf")
        → chunk_document(text, source="fridge-manual.pdf", doc_id="fridge-manual.pdf")
          → chunk_text(text, chunk_size=600, overlap=80)
            → re.split(r"(?<=[.!?])\s+", text) — sentence boundaries
            → build chunks with overlap tracking
            → return List[str]
          → wrap each string in Chunk(source, doc_id, index, char_positions)
          → return List[Chunk]
        → _embed([chunk.text for chunk in chunks])
          → openai.Embeddings.create(model="text-embedding-3-small", input=batch)
          → return List[List[float]]  (1536-dim per chunk)
        → numpy.array(embeddings)  → (N, 1536) float32
        → VectorStore.add_chunks(chunks, embeddings)
          → self.chunks.extend(chunks)
          → numpy.vstack([self.embeddings, embeddings]) or init
          → _save() → write chunks.json + embeddings.npy
        → VectorStore.store_doc_text("fridge-manual.pdf", text)
          → update self.documents dict
          → write docs.json
        → return IngestResult(filepath, chunks, characters, elapsed)
      → console.print() summary
```

## Call Chain — `manualmate ask "what does error code E24 mean?"`

```
manualmate.py:main()
  → cli()
    → ask(["what", "does", "error", "code", "E24", "mean?"])
      → question_text = "what does error code E24 mean?"
      → ManualMateRAG.ask(question_text, top_k=5)
        → ManualMateRAG.query(question_text, top_k=5)
          → _embed_single(question_text)
            → openai.Embeddings.create(model="text-embedding-3-small", input=[question])
            → returns query embedding vector (1536-dim)
          → VectorStore.search(query_embedding, top_k=5)
            → normalize query → L2 norm
            → normalize stored → row-wise L2 norm
            → cosine_sim = stored_normed @ query_norm  (matrix × vector)
            → np.argsort(scores)[-top_k:][::-1]
            → return [SearchResult(chunk, score)]  (top-5)
          → return list of SearchResult
        → build system_prompt + context from retrieved chunks
        → openai.Chat.Completions.create(
            model="gpt-4o-mini",
            messages=[system + user_prompt],
            temperature=0.3,
          )
          → returns answer text
        → return QueryResult(answer, sources, chunks, scores)
      → console.print(Panel(Markdown(result.answer), title="Answer"))
      → console.print(sources Table)
```

## Call Chain — `manualmate list`

```
manualmate.py:main()
  → cli()
    → list_()
      → ManualMateRAG.list_docs()
        → VectorStore.list_docs()
          → iterate self.chunks, count by doc_id
          → return [(doc_id, count)]  sorted desc
      → console.print(Table of documents)
```

## Key Data Flow

```
User Manual (PDF/TXT)
    ↓
load_document()   → raw text string
    ↓
chunk_document()  → List[Chunk]  (sentence-boundary, overlapping)
    ↓
_embed()          → openai API: text-embedding-3-small
    ↓
VectorStore       → chunks.json + embeddings.npy + docs.json  ⟐ ~/.manualmate/
    │
    │  ─── on ask ───
    │
User Question
    ↓
_embed_single()   → openai API: text-embedding-3-small → query vector
    ↓
VectorStore.search()  → top-5 (chunk, score) pairs
    ↓
System prompt + context block
    ↓
openai Chat Completions (gpt-4o-mini)  → grounded answer
    ↓
Rich formatted output (Panel + Table)
```

## External API Calls

| Call | Endpoint | Model | Purpose |
|------|----------|-------|---------|
| `client.embeddings.create()` | OpenAI / compatible | `text-embedding-3-small` | Embed chunks & queries |
| `client.chat.completions.create()` | OpenAI / compatible | `gpt-4o-mini` | Generate grounded answer |

## Storage Layout (~/.manualmate/)

```
~/.manualmate/
├── chunks.json       # List[Chunk dicts] — text, source, doc_id, index, char offsets
├── embeddings.npy    # numpy array (n_chunks × 1536) float32
└── docs.json         # Dict[doc_id → full document text]
```

The store is append-only: new documents add chunks and grow the `.npy` array. Removals filter in memory and rewrite both files. This is fast for <10K chunks but won't scale to million-scale corpora — intentionally designed for personal use.