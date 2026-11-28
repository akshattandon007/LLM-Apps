# MintDocs — Data Flow & Module Dependency Graph

## Module dependency graph (static imports)

```
cli.py
  ├── fetcher.py (Fetcher)
  ├── chunker.py (chunk_filings)
  ├── embedder.py (Embedder)
  ├── indexer.py (Indexer)
  └── query.py (QueryEngine)
 
fetcher.py
  └── models.py (FilingMetadata)
 
chunker.py
  └── models.py (Chunk, FilingMetadata)
 
embedder.py
  └── models.py (Chunk)
    └── sentence_transformers [lazy, production only]
 
indexer.py
  ├── models.py (Chunk)
  ├── embedder.py (Embedder)
  └── faiss [lazy, production only]
    └── numpy [production only]
 
query.py
  ├── models.py (Chunk, QueryResult)
  ├── embedder.py (Embedder)
  └── indexer.py (Indexer)
    └── faiss, numpy [lazy, production only]
 
models.py       — standalone (no internal deps)
```

## Data flow: `mintdocs index AAPL --simulate`

```
  User CLI
     │
     ▼
  cli.main()
     │  parse args → Namespace(command='index', ticker='AAPL', simulate=True)
     │
     ▼
  cli.cmd_index(args)
     │
     ├── 1. Fetcher(simulate=True)
     │      │
     │      ├── resolve_cik("AAPL")        → "0000320193" (hardcoded in sim mode)
     │      ├── resolve_company_name("AAPL") → "Apple Inc. (Simulated)"
     │      │
     │      ├── search_filings("AAPL", quarters=8)
     │      │    │  _simulate_search_results()
     │      │    │  returns: [{"cik", "company_name", "ticker", "filing_type",
     │      │    │              "filing_date", "accession_number", "primary_doc"}, ...]
     │      │    │
     │      │    └── fetch_all("AAPL")
     │      │         └── returns list[FilingMetadata]
     │      │
     │      └── fetch_filing_text(filing_dict)
     │           │  _simulate_filing_text()
     │           │  returns: string with Item sections
     │           │
     │           └── (text, FilingMetadata) pairs for each filing
     │
     ├── 2. chunker.chunk_filings([(text, metadata), ...])
     │      │
     │      └── chunk_filing(text, metadata)
     │           │  SECTION_PATTERN regex finds Item headers
     │           │  [('Item 1', 'Business'), ('Item 1A', 'Risk Factors'), ...]
     │           │
     │           └── returns list[Chunk]  (one per substantive Item section)
     │
     ├── 3. Embedder(simulate=True)
     │      │
     │      └── embed_chunks(chunks)
     │           │  _simulate_embed() — SHA-256 → 384-dim deterministic vector
     │           │
     │           └── returns list[(Chunk, list[float])]
     │
     └── 4. Indexer(index_dir, simulate=True)
            │
            └── build_index(chunks_with_emb, ticker="AAPL")
                 │  _build_simulated()
                 │  _write_metadata() → metadata.json
                 │  (no FAISS file in sim mode)
                 │
                 └── ticker_dir  (e.g. ~/.mintdocs/index/AAPL/)
```

## Data flow: `mintdocs ask "What are China supply chain risks?" --ticker AAPL --simulate`

```
  User CLI
     │
     ▼
  cli.main()
     │  parse args → Namespace(command='ask', question='...', ticker='AAPL',
     │  │                          simulate=True, top_k=5)
     │
     ▼
  cli.cmd_ask(args)
     │
     └── QueryEngine(index_dir, simulate=True, top_k=5)
          │
          ├── simulate? YES
          │
          └── _simulate_query(question, ticker)
               │
               ├── Build hardcoded Chunk list (Risk Factors, Business, MD&A)
               │   with realistic metadata and text
               │
               ├── _build_simulated_answer(question, ticker, chunks)
               │    │  keyword-matches on "risk", "china", "supply chain"
               │    │  → returns context-aware paragraph
               │    │  fallback → generic answer
               │    │
               │    └── answer string
               │
               └── QueryResult(answer, sources=chunks)
                    │
                    └── result.format()
                         → "Answer: ...\n\nSources:\n  1. Apple Inc. 10-K (2024-10-31)..."
```

## Data flow: `mintdocs index AAPL` (production mode)

```
  Same as simulated, but:
  
  Fetcher(simulate=False)
    │  _load_cik_map() → httpx GET SEC company_tickers.json
    │  resolve_cik("AAPL") → real CIK lookup
    │  search_filings() → httpx GET efts.sec.gov
    │  fetch_filing_text() → httpx GET filing URL with 150ms delay
    │
  Embedder(simulate=False)
    │  _load_model() → SentenceTransformer('all-MiniLM-L6-v2')
    │  _embed_texts(texts) → model.encode(texts)
    │
  Indexer(simulate=False)
    │  _build_faiss() → faiss.IndexFlatL2(dim) → index.add(embs)
    │  _write_metadata() → metadata.json
    │
    └── ticker_dir with index.faiss + metadata.json
```

## Data flow: `mintdocs ask "risk factors" --ticker AAPL` (production mode)

```
  QueryEngine.query("risk factors", "AAPL")
    │  simulate = False
    │
    └── _production_query(question, ticker)
         │
         ├── indexer.load_index("AAPL")
         │    ├── faiss.read_index(index.faiss)
         │    └── load_metadata() → list[Chunk]
         │
         ├── embedder.embed_text("risk factors")
         │    └── model.encode(["risk factors"]) → [384-dim vector]
         │
         ├── faiss_index.search(question_vector, top_k=5)
         │    └── [(distance, idx), ...]
         │
         ├── Collect top-k Chunk objects
         │
         └── _format_answer(question, chunks)
              └── QueryResult(answer="Based on...", sources=[...])
```

## Key interfaces (function-level call chains)

### Fetcher
```
Fetcher.__init__(user_agent, simulate)
Fetcher.resolve_cik(ticker) → str
Fetcher.resolve_company_name(ticker) → str
Fetcher.search_filings(ticker, forms, quarters) → list[dict]
Fetcher.fetch_filing_text(filing_dict) → str
Fetcher.fetch_all(ticker, forms, quarters) → list[FilingMetadata]
Fetcher.close()
```

### Chunker
```
chunk_filing(text, metadata) → list[Chunk]
chunk_filings([(text, metadata), ...]) → list[Chunk]
```

### Embedder
```
Embedder.__init__(simulate)
Embedder._load_model()  [lazy]
Embedder.embed_chunks(chunks) → list[(Chunk, list[float])]
Embedder.embed_text(text) → list[float]
Embedder._embed_texts(texts) → list[list[float]]
Embedder._simulate_embed(texts) → list[list[float]]
```

### Indexer
```
Indexer.__init__(index_dir, simulate)
Indexer.build_index(chunks_with_emb, ticker) → Path
Indexer._build_faiss(chunks_with_emb, ticker_dir) → Path
Indexer._build_simulated(chunks_with_emb, ticker_dir) → Path
Indexer._write_metadata(chunks_with_emb, ticker_dir)
Indexer.load_index(ticker) → (faiss.Index, list[Chunk])
Indexer.load_metadata(ticker) → list[Chunk]
Indexer.list_indexed_tickers() → list[str]
Indexer.index_exists(ticker) → bool
```

### QueryEngine
```
QueryEngine.__init__(index_dir, simulate, top_k)
QueryEngine.query(question, ticker) → QueryResult
QueryEngine._simulate_query(question, ticker) → QueryResult
QueryEngine._production_query(question, ticker) → QueryResult
QueryEngine._format_answer(question, chunks) → str
QueryEngine._build_simulated_answer(question, ticker, chunks) → str
```

### CLI
```
main() → int
build_parser() → argparse.ArgumentParser
cmd_index(args) → int
cmd_ask(args) → int
```

## Data structures

```
FilingMetadata
  company_name: str
  ticker: str
  cik: str
  filing_type: "10-K" | "10-Q"
  filing_date: date
  accession_number: str
  primary_doc: str

Chunk
  section_header: str    # "Item 1A: Risk Factors"
  section_text: str      # full section text
  metadata: FilingMetadata
  to_dict() → dict
  from_dict(dict) → Chunk

QueryResult
  answer: str
  sources: list[Chunk]
  format() → str          # formatted with citations
```

## Storage layout

```
~/.mintdocs/index/
  AAPL/
    metadata.json     # list[Chunk.to_dict()]
    index.faiss       # FAISS flat L2 (production only)
  MSFT/
    metadata.json
    index.faiss
  ...
```