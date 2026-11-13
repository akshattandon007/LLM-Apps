# Flow — Hacker Mentor

## Function-Level Call Chains

### A. Ingestion Pipeline (`ingest.py` / `hacker_mentor.py ingest`)

```
ingest.main()
  │
  ├── VectorStore.load()                    # Try to load existing index
  │     └── faiss.read_index()              # Read binary FAISS index
  │     └── json.load()                     # Read metadata JSON
  │
  ├── hn_fetcher.fetch_story_comments_batch(topic, story_limit, comments_per_story)
  │     ├── hn_fetcher.search_stories(topic, limit)
  │     │     └── requests.get(ALGOLIA_URL/search)     # Search HN stories
  │     │
  │     └── [for each story]
  │           └── hn_fetcher.fetch_comments_for_story(story_object_id, max_comments)
  │                 └── requests.get(ALGOLIA_URL/search)  # Search comments for story
  │
  ├── Embedder.embed_batch(texts)
  │     └── SentenceTransformer.encode(texts, normalize_embeddings=True)
  │
  └── VectorStore.add(embeddings, documents)
        ├── faiss.IndexIDMap.add_with_ids()  # Add vectors to FAISS index
        └── self.metadata[id] = doc          # Store document metadata
```

### B. Query Pipeline (`query.py` / `hacker_mentor.py query`)

```
query.main()
  │
  ├── VectorStore.load()
  │     └── faiss.read_index()
  │     └── json.load()
  │
  ├── Embedder.embed(query_text)
  │     └── SentenceTransformer.encode(text, normalize_embeddings=True)
  │
  ├── VectorStore.search(query_embedding, k)
  │     └── faiss.IndexIDMap.search()          # Inner product search
  │
  └── [for each result]
        └── query.format_result(score, doc, rank)
              └── Pretty-print: score, title, URL, author, excerpt
```

## Module Dependency Graph

```
hacker_mentor.py (CLI entry point)
    │
    ├── ingest.py
    │     ├── hn_fetcher.py
    │     │     └── requests (external)
    │     ├── embedder.py
    │     │     └── sentence_transformers (external)
    │     └── vector_store.py
    │           ├── faiss (external)
    │           └── numpy (external)
    │
    └── query.py
          ├── embedder.py
          │     └── sentence_transformers
          └── vector_store.py
                ├── faiss
                └── numpy
```

## Data Flow

```
[Algolia HN API]
      │
      ▼
hn_fetcher.py ──► documents (list of dicts)
      │
      ▼
embedder.py ──► numpy array (N × 384)
      │
      ▼
vector_store.py ──► data/faiss_index.bin + data/metadata.json
      │
      ▼ (on query)
query.py ──► formatted results to stdout
```

## File System Layout

```
hacker-mentor/
├── hacker_mentor.py    # CLI entry point (dispatches to ingest/query)
├── ingest.py           # Ingestion pipeline
├── query.py            # Query pipeline
├── hn_fetcher.py       # HN API client
├── embedder.py         # Embedding model wrapper
├── vector_store.py     # FAISS vector store
├── README.md           # Project documentation
├── Decisions.md        # Architecture decisions
├── Flow.md             # This file
├── requirements.txt    # Python dependencies
└── data/               # Created on first ingest
    ├── faiss_index.bin # FAISS binary index (gitignored)
    └── metadata.json   # Document metadata (gitignored)
```

## Test Coverage

```
tests/test_hacker_mentor.py
  ├── test_hn_fetcher_search_stories()
  ├── test_hn_fetcher_fetch_comments()
  ├── test_embedder_single()
  ├── test_embedder_batch()
  ├── test_vector_store_add_and_search()
  ├── test_vector_store_save_load()
  └── test_full_ingest_query_pipeline()
```
