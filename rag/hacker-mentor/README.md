# 🧠 Hacker Mentor — Hacker News Semantic Q&A

Turn Hacker News into your personal tech mentor. Ask questions in natural language and get the most relevant discussions, insights, and advice from decades of HN comments and stories.

## What it does

Hacker News has some of the best tech discussions on the internet — debugging war stories, architecture debates, career advice, tool recommendations. But finding *relevant* content buried in 15+ years of threads is nearly impossible with keyword search alone.

**Hacker Mentor** ingests HN stories and comments, embeds them semantically, and lets you ask questions like:

- *"What are the common pitfalls of microservices?"*
- *"How do I negotiate a startup offer?"*
- *"Best practices for handling database migrations"*
- *"What's the sentiment on Rust vs Go for backend services?"*

It returns the most relevant HN threads with excerpts and direct links — no hallucinated answers, just the wisdom the community already wrote.

## How it works

```
                    ┌─────────────────┐
                    │  HN Algolia API │
                    └────────┬────────┘
                             │ fetch stories + comments
                             ▼
                    ┌─────────────────┐
                    │  Ingestion      │
                    │  (chunk + embed)│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  FAISS Index    │
                    │  (vector store) │
                    └────────┬────────┘
                             │
  ┌────────┐         ┌───────┴────────┐
  │ User   │ ──────► │  Query Engine  │
  │ Query  │         │  (embed +      │
  └────────┘         │   search)      │
                     └───────┬────────┘
                             │ top-k results
                             ▼
                    ┌─────────────────┐
                    │  Results        │
                    │  (ranked        │
                    │   excerpts +    │
                    │   links)        │
                    └─────────────────┘
```

## Installation

```bash
# Clone and enter directory
cd rag/hacker-mentor

# Install dependencies
pip install -r requirements.txt
```

**Note:** `sentence-transformers` and `faiss-cpu` require about 200MB of download on first run. The embedding model (`all-MiniLM-L6-v2`) downloads automatically on first use (~80MB).

## Usage

### 1. Ingest HN data (fetch and build index)

```bash
# Fetch top stories about a topic and build the vector index
python ingest.py --topic "microservices" --limit 50
```

Options:
- `--topic` — Search topic (default: "programming")
- `--limit` — Number of stories to fetch (default: 30, max: 200)
- `--reindex` — Force rebuild even if index exists

### 2. Query the index

```bash
python query.py "What are common microservice pitfalls?"
```

The query tool:
1. Embeds your question
2. Searches the FAISS index
3. Returns top 5 results with relevance scores, excerpts, and HN links

### 3. Run both in one shot

```bash
python hacker_mentor.py --ingest --topic "rust vs go" --limit 50
python hacker_mentor.py --query "Which is better for backend services?"
```

## Example

```bash
$ python query.py "How do I negotiate a salary at a startup?"

  ────────────────────────────────────────────────
  Top 5 HN Discussions
  ────────────────────────────────────────────────

  1. [Score: 0.89] Ask HN: How to negotiate equity at an early-stage startup?
     https://news.ycombinator.com/item?id=12345678
     > "The key is understanding dilution. If they offer 1%,
     > ask what the current option pool size is..."
     ────────────────────────────────────────────────

  2. [Score: 0.84] Salary negotiation advice from a recruiter
     https://news.ycombinator.com/item?id=23456789
     > "Always have a BATNA. The best leverage is another offer..."
     ────────────────��───────────────────────────────
```

## Project Structure

```
hacker-mentor/
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── Decisions.md            # Architecture decisions
├── Flow.md                 # Function-level call chains
├── hacker_mentor.py        # Main CLI entry point
├── ingest.py               # Data ingestion pipeline
├── query.py                # Query/search engine
├── hn_fetcher.py           # HN Algolia API client
├── embedder.py             # Embedding model wrapper
├── vector_store.py         # FAISS index wrapper
└── tests/
    └── test_hacker_mentor.py  # Unit tests
```

## Tests

```bash
# Run tests
python -m pytest tests/ -v
```

## Data

The vector index is stored in `data/faiss_index.bin` and document metadata in `data/metadata.json`. Both are gitignored — rebuild on each machine.

## License

MIT
