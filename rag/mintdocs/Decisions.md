# MintDocs — Architectural Decisions

## 1. CLI with argparse (not click, typer, or rich)

**Chosen**: `argparse` (stdlib)  
**Rejected**: Click, Typer, Rich CLI

Reason: argparse is part of the stdlib — zero dependencies for the CLi. For a
thin CLI with two subcommands and a few flags, the ergonomic win of Click/Typer
doesn't outweigh the added dependency. If the CLI grows to 10+ subcommands with
nested groups and autocomplete, migrate to Typer.

---

## 2. httpx over requests

**Chosen**: `httpx`  
**Rejected**: `requests`, `urllib`  

Reason: httpx has a modern API, is async-ready (though we don't use async yet),
and handles redirects cleanly. requests is stable but has no async path if we
ever want parallel filing downloads. urllib is too low-level for a polite API
client.

---

## 3. Simulated mode as a top-level flag (not environment variable)

**Chosen**: `--simulate` on every CLI invocation  
**Rejected**: `MINTDOCS_ENV=dev` env var, separate `mintdocs-sim` binary

Reason: an explicit flag at the command level makes it obvious from the shell
history whether simulation is active. An env var is invisible and can be
forgotten. A separate binary duplicates entry points.

Downside: every command needs the flag. Mitigated by shell aliases
(`alias mintdocs-sim='mintdocs --simulate'`).

---

## 4. sentence-transformers with lazy import (not a separate service)

**Chosen**: Import `sentence_transformers` lazily inside `_load_model()`  
**Rejected**: Separate embedding microservice, ONNX Runtime, llama.cpp

Reason: for a desktop/VPS CLI tool, loading a 90MB model locally is simpler
than running a separate service. Lazy import means `mintdocs --simulate` never
touches the ML deps.

If the project scales to indexing 500+ companies, a separate embedding service
with batching would make sense — but not for v1.

---

## 5. FAISS flat L2 (not IVF, HNSW, or vector DB)

**Chosen**: `faiss.IndexFlatL2`  
**Rejected**: FAISS IVF (IndexIVFFlat), HNSWlib, pgvector, Chroma, Qdrant

Reason: for per-ticker indices with typically 50-200 chunks each, an exact
(brute-force) L2 search is fast enough (microseconds). IVF needs training and
tuning. Running a vector database for a CLI tool is over-engineering.

Flat L2 breaks when a ticker has 10,000+ chunks — but that's ~20 years of
quarterly filings. We'll cross that bridge when we get there.

---

## 6. Per-ticker directories (not a single global index)

**Chosen**: `~/.mintdocs/index/{TICKER}/` with separate FAISS + metadata per ticker  
**Rejected**: Single FAISS index with ticker metadata column

Reason: queries always target one company. A per-ticker structure means fast
load (small files), easy inspection, and no filtering overhead. A single index
would need metadata filtering on every query.

---

## 7. Metadata as JSON (not SQLite, not pickle)

**Chosen**: `metadata.json` per ticker  
**Rejected**: SQLite, pickle, msgpack

Reason: JSON is human-readable, debuggable, and safe to load. It's ~50KB for
200 chunks — perfectly fine for a CLI tool. Pickle is a security risk for a
tool that might share indices. SQLite adds a dep for simple read/write of
structured data.

---

## 8. SEC EFTS over direct RSS/CIK filing scraping

**Chosen**: SEC EDGAR Full-Text Search API (`efts.sec.gov`)  
**Rejected**: SEC RSS feeds, direct index file parsing

Reason: EFTS returns structured JSON with accession numbers, form types, and
companies — no HTML parsing. The RSS feeds have limited history. The CIK bulk
file gives the ticker-to-CIK lookup in a single JSON download.

---

## 9. Chunking by Item headers (not by token count or paragraph)

**Chosen**: Regex-based Item section splitting  
**Rejected**: Fixed-token-window chunking, paragraph splitting

Reason: SEC filings are naturally structured by Item sections (Item 1, Item 1A,
Item 7, etc.). These align with the kind of queries users ask ("what are the
risk factors?" vs "what was revenue?"). Token-window chunking would split a
section across chunks, losing semantic boundaries.

---

## 10. Section titles as chunk metadata (not part of the embedded text)

**Chosen**: Section header stored separately in Chunk metadata, included in
text when embedding  
**Rejected**: Section header excluded from embedding text, stored only in
display metadata

Reason: the header provides critical context for similarity search. "Item 1A:
Risk Factors" embedded alongside the section text helps the query "what are the
risks?" match better than the text alone. The header is also stored separately
in metadata for clean display in source citations.

---

## 11. Simulated embedding with deterministic SHA-256 seeding

**Chosen**: Simulated embeddings derived from SHA-256 of the text  
**Rejected**: Random vectors, all-zeros, unit vectors

Reason: deterministic per-text vectors mean:
- Same query text always gets the same answer
- Different text gets different vectors (preserves relative relationships)
- No random state issues

The values are in [0, 1] range matching typical embedding normalization.

---

## 12. No database for query result caching

**Chosen**: No caching — every query runs embedding + search  
**Rejected**: Redis, SQLite cache, disk cache

Reason: for a CLI tool run interactively, search latency of ~100ms
(embedding + flat L2 on 200 chunks) is fast enough. Caching adds complexity
for marginal gain in a single-user context.

---

## 13. pathlib everywhere (not os.path)

**Chosen**: `pathlib.Path` for all file operations  
**Rejected**: `os.path.join`, `os.makedirs`, string path concatenation

Reason: pathlib is the modern Python standard — composable, readable, and
cross-platform. The requirement is enforced: zero uses of `os.path` in the
codebase.

---

## 14. setup.py with extras (not pyproject.toml only)

**Chosen**: `setup.py` with `extras_require={"full": [...]}`  
**Rejected**: Pure pyproject.toml (PEP 621)

Reason: setup.py provides `pip install -e .` out of the box for development.
The `[full]` extras_require lets users install the heavy ML deps separately.
When the project stabilises, a move to pyproject.toml would be fine.

---

## 15. Flat test structure (not nested conftest-heavy)

**Chosen**: Flat `tests/` directory with one file per module  
**Rejected**: Nested test directories, shared fixtures in conftest.py

Reason: for four modules, a flat structure is easier to navigate than nested
mirrors of the source tree. Shared fixtures go in individual test files to
keep each file self-contained and readable.