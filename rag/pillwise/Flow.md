# Flow.md — PillWise

## Execution trace from CLI entry point through each module to output.

---

## 1. CLI Entry — `pillwise <command> [args]`

```
pillwise ask "What are the side effects of ibuprofen?"
  → cli.py: main()
      → argparse dispatches to cmd_ask()
```

### Command dispatch table

| Command | Handler | Module | Purpose |
|---------|---------|--------|---------|
| `fetch` | `cmd_fetch()` | `cli.py` | Download drug labels |
| `index` | `cmd_index()` | `cli.py` | Build vector index |
| `ask` | `cmd_ask()` | `cli.py` | Semantic search + answer |
| `search` | `cmd_search()` | `cli.py` | Raw retrieval only |
| `info` | `cmd_info()` | `cli.py` | Index statistics |

---

## 2. Fetch Pipeline — `pillwise fetch --limit 100`

```
cmd_fetch(args)
  │
  ├──→ fetcher.fetch_drug_labels(limit=100, skip=0)
  │       │
  │       ├──→ HTTP GET https://api.fda.gov/drug/label.json?limit=100&skip=0
  │       │     ← JSON response with 100 label results
  │       │
  │       ├──→ For each result:
  │       │     ├── _extract_field(result, "openfda.brand_name")      → str | None
  │       │     ├── _extract_field(result, "indications_and_usage")   → str | None
  │       │     ├── _extract_field(result, "adverse_reactions")       → str | None
  │       │     ├── _extract_field(result, "drug_interactions")       → str | None
  │       │     └── ... (all USEFUL_FIELDS)
  │       │
  │       ├──→ Continue pagination (skip += 100) until limit reached
  │       └──→ Return list[dict] — structured drug label records
  │
  ├──→ fetcher.save_labels(records)
  │       └──→ Write data/drug_labels.json (JSON, indent=2)
  │
  └──→ Print summary: "Done. N labels saved."
```

**External dependency:** OpenFDA API (`api.fda.gov`) — free, no auth.

---

## 3. Index Pipeline — `pillwise index`

```
cmd_index(args)
  │
  ├──→ fetcher.load_labels()
  │       └──→ Read data/drug_labels.json
  │       ← list[dict] — previously fetched labels
  │
  ├──→ fetcher.prepare_chunks(records, chunk_size=500)
  │       │
  │       ├──→ For each drug label record:
  │       │     ├── Extract brand name, generic name → drug_id
  │       │     ├── For each field in USEFUL_FIELDS:
  │       │     │     ├── Split field text into 500-word chunks
  │       │     │     └── Append chunk dict:
  │       │     │         {drug_id, drug_name, field, field_label, text, source}
  │       │     └── Skip empty/short chunks
  │       │
  │       └──→ Return list[dict] — all text chunks
  │
  └──→ indexer.build_index(chunks, force_rebuild=True)
          │
          ├──→ Check for cached index (data/faiss_index.bin + data/index_meta.pkl)
          │     └── Cache miss → build from scratch
          │
          ├──→ indexer.get_embedder("all-MiniLM-L6-v2")
          │     └── sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
          │     ← Model loaded (~80MB download on first run)
          │
          ├──→ model.encode(chunk_texts, normalize_embeddings=True)
          │     ← numpy.ndarray shape=(N_chunks, 384)
          │
          ├──→ faiss.IndexFlatIP(384)    # Inner Product = cosine similarity
          │     → index.add(embeddings)
          │     ← FAISS index with N_total vectors
          │
          ├──→ Save index: data/faiss_index.bin
          ├──→ Save metadata: data/index_meta.pkl
          └──→ Return (index, texts, metadata)
```

---

## 4. Query Pipeline — `pillwise ask "What are the side effects of ibuprofen?"`

```
cmd_ask(args)
  │
  ├──→ fetcher.load_labels()
  ├──→ fetcher.prepare_chunks(records)
  ├──→ indexer.build_index(chunks)   # Loads cached index if available
  │
  ├──→ indexer.search(index, texts, metadata, query="What are the side effects of ibuprofen?", k=5)
  │     │
  │     ├──→ get_embedder("all-MiniLM-L6-v2")
  │     ├──→ model.encode([query], normalize_embeddings=True)
  │     │     ← numpy.ndarray shape=(1, 384)
  │     │
  │     ├──→ index.search(query_vec, k=5)
  │     │     ← (scores, indices) — top-5 most similar chunks
  │     │
  │     └──→ Return list[dict]:
  │           [{text, score, drug_id, drug_name, field, field_label, source}, ...]
  │
  └──→ generator.generate(query, results)
        │
        ├─── Is HUGGINGFACE_TOKEN set?
        │   ├── YES → generate_with_huggingface(query, results)
        │   │           ├── _format_context(results) → context string
        │   │           ├── _build_prompt(query, context) → Phi-3 instruction prompt
        │   │           ├── HTTP POST to HuggingFace Inference API
        │   │           └── ← LLM-generated plain-language answer
        │   │
        │   └── NO → generate_retrieval_only(query, results)
        │               └── Format top-k results with relevance scores
        │               ← Retrieval output (no LLM cost)
        │
        └──→ Print answer to stdout
```

---

## 5. Module Dependency Graph

```
cli.py
  ├── fetcher.py        ─── requests (HTTP → OpenFDA API)
  ├── indexer.py        ─── sentence-transformers, faiss, numpy
  └── generator.py      ─── urllib.request (HTTP → HuggingFace API)
```

ASCII tree:

```
pillwise/
│
├── cli.py              # Entry point: argparse → dispatch
│   ├──→ fetcher.py     # OpenFDA API client
│   │   └──→ requests   # HTTP to api.fda.gov
│   │
│   ├──→ indexer.py     # Embedding + vector search
│   │   ├──→ sentence-transformers   # all-MiniLM-L6-v2 encoder
│   │   ├──→ faiss                    # IndexFlatIP (cosine similarity)
│   │   └──→ numpy                    # Array ops
│   │
│   └──→ generator.py   # LLM answer generation
│       └──→ urllib.request           # HTTP to HuggingFace Inference API
│
├── setup.py            # Package config (entry point: pillwise=pillwise.cli:main)
├── requirements.txt    # Dependencies
├── README.md           # User docs
├── Decisions.md        # Architectural decisions
└── Flow.md             # This file
```

---

## 6. Data Flow Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  OpenFDA    │────→│ fetcher.py       │────→│ drug_labels.json│
│  API        │     │ fetch + extract  │     │ (local cache)   │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                                                       ▼
                                               ┌──────────────────┐
                                               │ prepare_chunks() │
                                               │ field-level split│
                                               └────────┬─────────┘
                                                        │
                                                        ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ User Query  │────→│ indexer.py       │←────│ chunk list       │
│             │     │ encode + search  │     └──────────────────┘
└─────────────┘     └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Top-K chunks     │
                    │ (relevance sorted)│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐     ┌──────────────────────┐
                    │ HUGGINGFACE_TOKEN?│────→│ HuggingFace API      │
                    │ (yes)            │     │ (plain-language reply)│
                    └────────┬─────────┘     └──────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │ (no)             │
                    │ retrieval-only   │
                    │ formatted output │
                    └──────────────────┘
```

---

## 7. Function-Level Call Chain

```
main()                                              cli.py:215
  ├── cmd_fetch()                                   cli.py:40
  │     ├── fetch_drug_labels()                     fetcher.py:45
  │     │     ├── requests.get(OPENFDA_BASE, ...)   fetcher.py:57
  │     │     └── _extract_field()                  fetcher.py:36
  │     └── save_labels()                           fetcher.py:89
  │
  ├── cmd_index()                                   cli.py:52
  │     ├── load_labels()                           fetcher.py:97
  │     ├── prepare_chunks()                        fetcher.py:105
  │     └── build_index()                           indexer.py:23
  │           ├── get_embedder()                    indexer.py:12
  │           └── model.encode() + faiss.add()      indexer.py:47-51
  │
  ├── cmd_ask()                                     cli.py:67
  │     ├── load_labels()                           fetcher.py:97
  │     ├── prepare_chunks()                        fetcher.py:105
  │     ├── build_index()                           indexer.py:23
  │     ├── search()                                indexer.py:67
  │     │     ├── get_embedder()                    indexer.py:12
  │     │     ├── model.encode(query)               indexer.py:73
  │     │     └── index.search(query_vec)           indexer.py:74
  │     └── generate()                              generator.py:129
  │           ├── generate_with_huggingface()       generator.py:60
  │           │     ├── _format_context()           generator.py:19
  │           │     ├── _build_prompt()             generator.py:28
  │           │     └── urllib.request.urlopen()    generator.py:94
  │           └── generate_retrieval_only()         generator.py:108
  │
  └── cmd_info()                                    cli.py:96
        ├── load_labels()
        ├── prepare_chunks()
        └── build_index()
```

---

## 8. Key Execution Paths

| Path | Trigger | Files Touched | External Calls |
|------|---------|---------------|----------------|
| **Fetch** | `pillwise fetch` | `fetcher.py`, `requests` → OpenFDA | `api.fda.gov` |
| **Index** | `pillwise index` | `indexer.py`, `sent. transformers` | (none, cached) |
| **Ask (no token)** | `pillwise ask Q` | `indexer.py`, `generator.py` | (none) |
| **Ask (with token)** | `pillwise ask Q` + `HF_TOKEN` | `indexer.py`, `generator.py` | `api-inference.huggingface.co` |
| **Search** | `pillwise search Q` | `indexer.py` | (none) |

---

*Generated as part of the PillWise build pipeline.*
