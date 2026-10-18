# Flow.md — TripTome

## Module Dependency Graph

```
triptome/
├── cli.py             # CLI entry point (Click)
│   ├── calls → ingest_directory()     [indexer.py]
│   ├── calls → index_documents()      [embedder.py]
│   ├── calls → search()               [embedder.py]
│   ├── calls → answer_query()         [generator.py]
│   └── calls → get_stats() / reset()  [embedder.py]
├── models.py          # Data classes (no deps on other modules)
│   └── Document, SearchResult, Answer
├── indexer.py         # File reading + chunking
│   └── depends on → Document [models.py]
├── embedder.py        # ChromaDB vector store
│   └── depends on → Document, SearchResult [models.py]
└── generator.py       # Answer generation
    └── depends on → SearchResult, Answer [models.py]
                    → search() [embedder.py]
                    → httpx (external LLM API)
```

## Execution Flows

### Flow 1: `triptome ingest <path>` — Document Ingestion

```
CLI (cli.py ingest())
  │
  ├── Path(path).exists()?
  │   └── No → exit with error
  │
  ├── ingest_directory(path, chunk_size, overlap)   [indexer.py]
  │   ├── Iterate files in directory
  │   ├── For each .txt/.md:
  │   │   ├── _read_text_file(path) → raw text
  │   │   └── _split_text(text, source, chunk_size, overlap)
  │   │       ├── Split by '\n\n' boundaries (paragraphs)
  │   │       ├── If paragraph > 1.5x chunk_size:
  │   │       │   └── _split_paragraph() by '.!?' sentence boundaries
  │   │       ├── Accumulate paragraphs until chunk_size exceeded
  │   │       │   └── Emit Document(text, source, chunk_id)
  │   │       └── Carry overlap paragraphs into next chunk
  │   │
  │   └── For each .pdf:
  │       ├── _read_pdf(path) → yield (page_text, page_num)
  │       └── _split_text(page_text, ...) → Document[]
  │           └── (same splitting as above)
  │
  ├── index_documents(documents)   [embedder.py]
  │   ├── Get/create ChromaDB "travel-docs" collection
  │   └── For each batch of 100:
  │       ├── Prepare ids = ["{source}__{chunk_id}"]
  │       ├── Prepare documents = [text]
  │       ├── Prepare metadatas = [{source, page, chunk_id}]
  │       └── collection.add(ids, documents, metadatas)
  │           └── ChromaDB ONNX embedder(all-MiniLM-L6-v2)
  │               → Embed each text → 384-dim vector
  │               → Insert into HNSW index (cosine)
  │
  └── Print summary: chunk count, document count
```

### Flow 2: `triptome ask "Best time to visit Tokyo?"` — Query

```
CLI (cli.py ask())
  │
  └── answer_query(query, n_results=5)   [generator.py]
      │
      ├── search(query, n_results)   [embedder.py]
      │   ├── Get ChromaDB collection
      │   ├── collection.query(query_texts=[query])
      │   │   └── ChromaDB ONNX embedder → embed query
      │   │   └── HNSW search → top-N nearest (cosine)
      │   │   └── Returns: ids[], documents[], metadatas[], distances[]
      │   │
      │   └── Convert to SearchResult[]: source, page, score (1-distance)
      │
      ├── if empty results:
      │   └── Return Answer with "no documents indexed" message
      │
      ├── _build_context(results)
      │   └── Format each result as "[Source N: file (page)]\ntext"
      │
      ├── Check for API key (OPENAI_API_KEY / TRIPTOME_API_KEY)
      │   ├── Present:
      │   │   └── _generate_with_openai(context, query, api_key, model, url)
      │   │       ├── POST {base_url}/chat/completions
      │   │       ├── System prompt: "You are TripTome..."
      │   │       ├── User prompt: context + query
      │   │       ├── Parse response → generated answer string
      │   │       └── Return Answer with generated text + citations
      │   │
      │   └── Missing:
      │       └── Return Answer with fallback: show first 3 chunks
      │
      └── CLI prints:
          ├── Panel with Markdown answer
          └── Table of sources (N, Document, Relevance, Page)
```

### Flow 3: `triptome stats` — Collection Stats

```
CLI (cli.py stats())
  │
  └── get_stats()   [embedder.py]
      ├── collection.count() → total_chunks
      ├── collection.get(include=["metadatas"])
      │   └── Extract unique source filenames
      └── Return {total_chunks, sources, source_count}
```

### Flow 4: `triptome clear` — Reset Collection

```
CLI (cli.py clear())
  │
  └── reset()   [embedder.py]
      └── client.delete_collection("travel-docs")
```

## Data Flow Diagram

```
USER INPUT
    │
    ▼
┌─────────────────────────────────┐
│          ingest <path>          │
│  ┌────────────────────────┐     │
│  │ PDF, TXT, MD files     │     │
│  └────────┬───────────────┘     │
│           ▼                     │
│  ┌────────────────────────┐     │
│  │ _split_text()          │     │
│  │ → Paragraph boundaries │     │
│  │ → Configurable overlap │     │
│  └────────┬───────────────┘     │
│           ▼                     │
│  ┌────────────────────────┐     │
│  │ Document[]             │     │
│  │ {text, source, page,   │     │
│  │  chunk_id}             │     │
│  └────────┬───────────────┘     │
│           ▼                     │
│  ┌────────────────────────┐     │
│  │ index_documents()      │     │
│  │ → ChromaDB add()       │     │
│  │ → ONNX embed → HNSW   │     │
│  └────────────────────────┘     │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│        ask "question"           │
│  ┌────────────────────────┐     │
│  │ search()               │     │
│  │ → ChromaDB query()     │     │
│  │ → Cos similarity       │     │
│  │ → SearchResult[]       │     │
│  └────────┬───────────────┘     │
│           ▼                     │
│  ┌────────────────────────┐     │
│  │ API key present?       │     │
│  │  ├─ Yes → LLM call     │     │
│  │  │    → GPT/Claude     │     │
│  │  │    → Generated ans  │     │
│  │  └─ No  → Raw context  │     │
│  │         → Fallback ans │     │
│  └────────┬───────────────┘     │
│           ▼                     │
│  ┌────────────────────────┐     │
│  │ Answer{citations,      │     │
│  │  answer, source_names} │     │
│  └────────┬───────────────┘     │
└─────────────────────────────────┘
          │
          ▼
    USER OUTPUT
    Panel + Table via Rich
```

## Key Call Chains (Function Level)

### Ingest path
```
cli.ingest()
  → ingest_directory(path, chunk_size, overlap)
    → ingest_file(path, chunk_size, overlap)        [per file]
      → _read_text_file(path)                       [.txt/.md]
      → _split_text(text, source, chunk_size, overlap)
        → _split_paragraph(oversized_para)           [large paras only]
      → _read_pdf(path) → pages                     [.pdf]
        → pypdf.PdfReader
        → _split_text(page_text, source, ...)
    → index_documents(documents)
      → get_collection()
        → chromadb.PersistentClient.get_or_create_collection()
      → collection.add(ids, documents, metadatas)   [batches of 100]
```

### Query path
```
cli.ask()
  → answer_query(query, n_results)
    → search(query, n_results)
      → get_collection()
      → collection.query(query_texts=[query], n_results=N)
        → (ChromaDB: embed query → HNSW search → return top-N)
      → build SearchResult[] from response
    → _build_context(results)
      → format "[Source N: file]..." sections
    → check env for API key
      → _generate_with_openai(context, query, api_key, model, url)
        → httpx POST /chat/completions
        → parse response
      → (or build fallback answer with raw context)
    → Return Answer
  → Rich Panel(Markdown(answer))
  → Rich Table(sources)
```