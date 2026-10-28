# Flow.md — MailMerge

## Execution Flow

### 1. Ingest Pipeline

```
__main__.py:cmd_ingest()
  │
  ├─ ingest.py:chunk_emails(mbox_path)
  │   ├─ mailbox.mbox(path)  ← stdlib, opens .mbox
  │   ├─ For each message:
  │   │   ├─ ingest.py:extract_text_from_email(msg)
  │   │   │   ├─ msg.is_multipart() → walk MIME parts
  │   │   │   │   └─ Only text/plain parts extracted
  │   │   │   └─ decode("utf-8", errors="replace") or latin-1
  │   │   └─ ingest.py:chunk_text(body, chunk_size, overlap)
  │   │       ├─ Normalise whitespace
  │   │       ├─ Split by \n\n (paragraph boundaries)
  │   │       ├─ For each paragraph:
  │   │       │   ├─ If short → append to current chunk
  │   │       │   ├─ If long → sentence-split (re.split(r'(?<=[.!?])\s+', ...))
  │   │       │   └─ If still oversized → force split
  │   │       └─ Apply overlap by prepending prev chunk's tail
  │   └─ Yield EmailChunk(metadata, chunk_index, text, chunk_id)
  │
  ├─ For each chunk → build dict:
  │   {id, text, subject, sender, date, labels}
  │
  └─ search.py:add_chunks(chunks, db_dir)
      ├─ search.py:get_or_create_collection()
      │   └─ chromadb.PersistentClient(path).get_or_create_collection()
      ├─ search.py:_get_encoder()
      │   └─ SentenceTransformer("all-MiniLM-L6-v2")  ← cached
      ├─ Batch in groups of 100:
      │   ├─ encoder.encode(texts) → list of vectors
      │   └─ collection.add(ids, embeddings, metadatas, documents)
      └─ Done
```

### 2. Search Pipeline

```
__main__.py:cmd_search()
  │
  └─ search.py:search(query, top_k, db_dir)
      ├─ search.py:get_or_create_collection()  → ChromaDB collection
      ├─ search.py:_get_encoder()  → SentenceTransformer model
      ├─ encoder.encode([query]) → query vector
      ├─ collection.query(query_embeddings, n_results, where)
      │   └─ ChromaDB: ANN search, returns (ids, distances, metadatas, documents)
      └─ For each result:
          ├─ Convert L2 distance → similarity: 1/(1+distance)
          └─ Build SearchResult(chunk_id, subject, sender, date, snippet, score)
```

### 3. Status Pipeline

```
__main__.py:cmd_status()
  │
  └─ search.py:get_or_create_collection().count()
      └─ Returns total chunk count
```

## Module Dependency Graph

```
__main__.py  (CLI entry, argparse)
   │
   ├──→ ingest.py  (mbox parsing, chunking)
   │       │
   │       └──→ models.py  (EmailMetadata, EmailChunk)
   │
   └──→ search.py  (ChromaDB CRUD, embedding, search)
           │
           ├──→ models.py  (SearchResult)
           ├──→ chromadb  (external)
           └──→ sentence_transformers  (external)
```

## Data Flow

```
User command line
      │
      ▼
argparse (__main__.py)
      │
      ├── ingest
      │     │
      │     ▼
      │   .mbox file (on disk)
      │     │
      │     ▼
      │   mailbox.mbox()  ──→ EmailMetadata per message
      │     │
      │     ▼
      │   extract_text_from_email()  ──→ plain text body
      │     │
      │     ▼
      │   chunk_text()  ──→ list of strings (chunks)
      │     │
      │     ▼
      │   SentenceTransformer.encode()  ──→ float[] vectors
      │     │
      │     ▼
      │   ChromaDB PersistentClient.add()  ──→ ~/.mailmerge/chroma/
      │
      └── search
            │
            ▼
          SentenceTransformer.encode(query)  ──→ query vector
            │
            ▼
          ChromaDB collection.query()  ──→ (ids, distances, metadatas)
            │
            ▼
          similarity = 1/(1+distance)
            │
            ▼
          print ranked results
```

## Key Files

| File | Role | Dependencies |
|------|------|--------------|
| `__main__.py` | CLI entry, arg parsing | ingest, search |
| `ingest.py` | MBOX parsing, chunking | mailbox (stdlib), models |
| `search.py` | Embedding, ChromaDB ops | chromadb, sentence-transformers, models |
| `models.py` | Data classes | (none) |
| `tests/test_mailmerge.py` | Unit tests | pytest, ingest, models |

## Concurrency / State

- No concurrent access — single-user CLI tool
- ChromaDB supports single-writer, multiple-reader access patterns
- sentence-transformers model is loaded once (module-level cache in `_get_encoder`)
- ChromaDB client is also cached once (`_get_client`)