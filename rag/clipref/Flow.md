# Flow — ClipRef

> Execution trace from CLI entry point to query output. Function-level call chains and module dependency graph.

---

## Entry Point

```
python -m clipref <command> [args...]
    │
    ├── clipref/__main__.py
    │     └── calls cli.main()
    │
    └── clipref/cli.py::main()
          └── parses sys.argv[1:] with argparse
                │
                ├── "index"  → cmd_index(args)
                ├── "search" → cmd_search(args)
                ├── "ask"    → cmd_ask(args)
                ├── "stats"  → cmd_stats(args)
                └── "drop"   → cmd_drop(args)
```

---

## Command: `clipref index <paths...>`

```
cmd_index(paths, db, chunk_size, chunk_overlap, model, glob)
    │
    ├── 1. utils.resolve_db_path(db) → Path
    ├── 2. utils.get_embedding_model(model) → SentenceTransformer
    │       └── loads model from ~/.cache/huggingface/ or downloads on first use
    │
    ├── 3. indexer.scan_files(paths, glob) → list[Path]
    │       └── for each path:
    │             │ if directory: Path.rglob(glob)
    │             └── if file: include directly if glob matches
    │
    ├── 4. indexer.chunk_files(files, chunk_size, overlap) → list[dict]
    │       │
    │       └── for each file:
    │             ├── utils.read_file_safe(path) → str (skips binary)
    │             └── indexer.chunk_text(text, path, chunk_size, overlap)
    │                   │
    │                   └── text_slicer(path, text, chunk_size, overlap)
    │                         ├── splits text into chunk_size-char segments
    │                         └── yields {chunk_id, text, source_file, source_path,
    │                                      file_hash, chunk_index, indexed_at}
    │
    ├── 5. indexer.embed_and_store(chunks, model, db_path) → int (count stored)
    │       │
    │       ├── embeddings = model.encode([c["text"] for c in chunks])
    │       │     └── all-MiniLM-L6-v2 → 384-dim float32 vectors
    │       │
    │       └── chromadb_client.get_or_create_collection("clipref")
    │             ├── collection.upsert(ids=hashes, embeddings=vectors,
    │             │                     metadatas=meta, documents=texts)
    │             └── (upsert ensures idempotent re-indexing)
    │
    ├── 6. result: print(f"✓ Indexed {n} chunks from {m} files")
    │
    └── returns: list of ChunkMetadata (see models.py)
```

---

## Command: `clipref search <query>`

```
cmd_search(query, db, top_k, model)
    │
    ├── 1. utils.resolve_db_path(db) → Path
    ├── 2. utils.get_embedding_model(model) → SentenceTransformer
    │
    ├── 3. chromadb_client.get_collection("clipref")
    │       └── raises if missing → shows "run clipref index first"
    │
    ├── 4. query_vector = model.encode(query) → 384-dim vector
    │
    ├── 5. results = collection.query(query_embeddings=[query_vector],
    │                                   n_results=top_k,
    │                                   include=["documents", "metadatas", "distances"])
    │       └── ChromaDB runs cosine similarity search internally
    │
    ├── 6. for each result:
    │       ├── print(f"[{score:.3f}] {metadata['source_path']}")
    │       └── print(document[:200] + "...")
    │
    └── returns: list[SearchResult]
```

---

## Command: `clipref ask <question>`

```
cmd_ask(question, ...)
    │
    ├── 1. cmd_search(question, ...) → list[SearchResult]
    │       └── (same flow as above)
    │
    ├── 2. searcher.generate_answer(question, search_results, model)
    │       │
    │       ├── context = "\n---\n".join(r.document for r in results)
    │       │
    │       ├── messages = [
    │       │     {"role": "system", "content": system_prompt},
    │       │     {"role": "user", "content": f"Context:\n{context}\n\nQ: {question}"}
    │       │   ]
    │       │
    │       ├── client = openai.OpenAI(
    │       │     base_url=config("OPENAI_BASE_URL"),
    │       │     api_key=config("OPENAI_API_KEY"))
    │       │
    │       ├── response = client.chat.completions.create(
    │       │     model=llm_model, messages=messages, temperature=0.3)
    │       │
    │       └── return Answer(text=response.choices[0].message.content, sources=sources)
    │
    ├── 3. print(answer text)
    ├── 4. print("\n--- Sources ---")
    │       └── for each source: print(f"- {source.path} (score: {source.score:.3f})")
    │
    └── returns: Answer object
```

---

## Command: `clipref stats`

```
cmd_stats(db)
    ├── 1. chromadb_client.get_collection("clipref") → collection
    ├── 2. count = collection.count()
    ├── 3. db_size = sum(f.stat().st_size for f in Path(db).rglob("*"))
    ├── 4. print(f"Chunks indexed: {count}")
    ├── 5. print(f"Database size: {db_size / 1024:.1f} KB")
    └── 6. if metadata available: print(f"Source files: {unique_filenames}")
```

---

## Module Dependency Graph

```
clipref/
│
├── __main__.py          ───── depends on → cli
│
├── cli.py               ───── depends on → indexer, searcher, utils, models
│
├── indexer.py           ───── depends on → utils, models, chromadb
│
├── searcher.py          ───── depends on → utils, models, chromadb, openai
│
├── models.py            ───── standalone data classes (no deps on other modules)
│
└── utils.py             ───── depends on → models, sentence_transformers
```

### Data Flow Diagram

```
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌──────────────┐
│  User's  │    │  Scanner   │    │  Embedder   │    │   ChromaDB   │
│  Files   │───▶│ (rglob)    │───▶│ (sentence-  │───▶│   (vector    │
│          │    │ + Chunker  │    │ transformer) │    │    store)    │
└──────────┘    └───────────┘    └────────────┘    └──────────────┘
                                                         │
                ┌──────────────────────────────────────────┤
                │                                          │
                ▼                                          ▼
         ┌───────────┐                             ┌──────────────┐
         │  CLI      │                             │   Searcher   │
         │ "search"  │◀────────────────────────────│(query embed) │
         │  prints   │                             │ + Chroma ret │
         │ results   │                             │ + optionally │
         └───────────┘                             │   LLM call   │
                                                   └──────────────┘
```

### Key Call Chains

| Entry | Chain |
|-------|-------|
| `index` | `cli.main → cmd_index → indexer.scan_files → indexer.chunk_files → indexer.embed_and_store` |
| `search` | `cli.main → cmd_search → utils.get_embedding_model → vector query → format results` |
| `ask` | `cli.main → cmd_ask → cmd_search → searcher.generate_answer → print answer + sources` |
| `stats` | `cli.main → cmd_stats → collection.count → print metrics` |
| `drop` | `cli.main → cmd_drop → chromadb.delete_collection → confirm` |