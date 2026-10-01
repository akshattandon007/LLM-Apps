# Flow — GardenGuide

## Module Dependency Graph

```
gardenguide.py (CLI entry point)
    ↓ calls into
src/rag_engine.py
    ├── GardenRAG.ingest()          → doc_loader.load_document()
    │                                → doc_loader.chunk_text()
    │                                → openai.Embeddings.create()  (external API)
    │                                → VectorStore.add_chunks()
    │
    ├── GardenRAG.query()           → openai.Embeddings.create()  (external API)
    │                                → VectorStore.search()
    │
    ├── GardenRAG.ask()             → GardenRAG.query()
    │                                → openai.Chat.Completions.create()  (external API)
    │
    ├── GardenRAG.list_docs()       → VectorStore.list_docs()
    ├── GardenRAG.remove_doc()      → VectorStore.remove_doc()
    └── GardenRAG.clear()           → VectorStore + shutil.rmtree()

src/doc_loader.py
    ├── load_document()             → load_text() / try_load_pdf()
    ├── chunk_text()                → re.split() — sentence-boundary chunking
    └── try_load_pdf()              → pymupdf / pdfplumber / pdftotext (optional)

src/rag_engine.py
    └── VectorStore
        ├── add_chunks()            → numpy.vstack() + JSON persist
        ├── search()                → numpy matrix ops (cosine similarity)
        ├── remove_doc()            → list comprehension filter + numpy slice
        ├── list_docs()             → return dict keys
        └── _load() / _save()       → JSON + .npy disk I/O
```

## Call Chain — `gardenguide ingest seeds.txt`

```
gardenguide.py:cli()
  → ingest(filepath)
    → GardenRAG.ingest(filepath)
      → doc_loader.load_document(filepath)
        → Path.exists() check
        → Path.suffix → dispatch to load_text() (.txt)
        → load_text() — open(), read(), return
      → chunk_text(text, chunk_size=500, overlap=50)
        → re.split(r"(?<=[.!?])\s+", text)  — split at sentence boundaries
        → iterate, build chunks with overlap
        → return List[str]
      → openai.Embeddings.create(model=..., input=chunks)  — batch of 20
        → returns List[embedding vectors]
      → VectorStore.add_chunks(chunks, source, embeddings)
        → numpy.vstack() to concatenate with existing embeddings
        → extend self.chunks, self.doc_sources lists
        → _save() to JSON + .npy
      → VectorStore.store_doc_text(source, text)
        → update _documents dict, write docs.json
      → return {"filepath", "chunks", "characters", "elapsed_seconds"}
    → click.echo() summary
```

## Call Chain — `gardenguide ask "when should I plant tomatoes?"`

```
gardenguide.py:cli()
  → ask(["when", "should", "I", "plant", "tomatoes?"])
    → GardenRAG.ask(question_text, top_k=3)
      → GardenRAG.query(question, top_k=3)
        → openai.Embeddings.create(model=..., input=[question])
          → returns query embedding vector
        → VectorStore.search(q_emb, top_k=3)
          → normalize query embedding → L2 norm
          → normalize stored embeddings → row-wise L2 norm
          → cosine = query_norm @ stored_normed.T
          → argsort, take top-k
          → return [(chunk, score, index)]
        → return [(text, score)]
      → build system prompt + context block
      → openai.Chat.Completions.create(
          model=..., messages=[system, user], temperature=0.3
        )
        → returns generated answer text
      → return {"answer", "sources", "chunks"}
    → click.echo() formatted output
```

## Key Data Flow

```
User Document (seed packet PDF/txt)
    ↓
load_document()  →  raw text string
    ↓
chunk_text()     →  List[str]  (overlapping sentence-boundary chunks)
    ↓
openai API       →  List[ndarray]  (embedding vectors, 1536-dim)
    ↓
VectorStore      →  chunks.json  +  embeddings.npy  +  docs.json
    │
    │  (on query)
    │
User Question    →  openai API  →  query embedding
    ↓
VectorStore.search()  →  top-3 (chunk_text, score) pairs
    ↓
Format context block  →  openai Chat Completions  →  grounded answer
```

## External API Calls

| Call | Endpoint | Model | Purpose | Retries |
|------|----------|-------|---------|---------|
| `client.embeddings.create()` | OpenAI / compatible | `text-embedding-3-small` | Embed chunks & queries | None (1 call per batch) |
| `client.chat.completions.create()` | OpenAI / compatible | `gpt-4o-mini` | Generate answer | None (1 call per ask) |