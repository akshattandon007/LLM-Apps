# 🤖 API Documentation RAG Agent

> Ask plain-English questions about any API documentation — powered by **Claude** (Anthropic) and **LangChain**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://langchain.com)
[![Claude](https://img.shields.io/badge/LLM-Claude%20Sonnet-purple)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What It Does

This agent takes **any API documentation URL** (e.g. the Facebook Graph API, Stripe, Twilio, GitHub) and makes it conversationally queryable. You can ask technical *or* non-technical questions and receive grounded, citation-backed answers — Claude only uses the fetched documentation as its knowledge source, so it cannot hallucinate API details.

```
📄 API Docs URL  →  🔍 Fetch & Index  →  🤖 Claude RAG  →  💬 Plain-English Answers
```

### Example Interaction

```
Documentation URL: https://developers.facebook.com/docs/graph-api/

You: What is the Graph API and why would I use it?

Claude: The Graph API is Facebook's primary interface for reading and writing data
        to the Facebook social graph — the network of people, pages, groups, and
        the connections between them.

        You'd use it to:
        • Retrieve a user's profile, friends list, or posts
        • Publish content on behalf of a user
        • Access page insights and ad data

        Requests go to `https://graph.facebook.com/{version}/{node-id}`
        and use standard HTTP verbs (GET, POST, DELETE).

        Source: https://developers.facebook.com/docs/graph-api/overview/

You: How do I authenticate? I'm not a developer.

Claude: Authentication uses something called an **Access Token** — think of it as
        a temporary password that proves your app has permission to access data.

        There are three types:
        1. **User token** — acts on behalf of a logged-in Facebook user
        2. **App token** — used for server-to-server calls (no user involved)
        3. **Page token** — manages a Facebook Page

        To get started, you create a free account on the Facebook Developer Portal,
        register your app, and Facebook gives you tokens to test with...
```

---

## Architecture

```
User
 │
 │  1. Provide URL
 ▼
┌─────────────────────────────────────────────────────────┐
│  main.py  (CLI)                                         │
└─────────────────────────────────────────────────────────┘
 │
 │  Ingestion pipeline
 ▼
┌─────────────────────────────────────────────────────────┐
│  document_loader.py                                     │
│  ├─ HTTP fetch (requests + BeautifulSoup)               │
│  ├─ In-domain link crawl (up to 30 pages)               │
│  ├─ Noise removal (nav, footer, scripts)                │
│  └─ RecursiveCharacterTextSplitter (1000 chars, ov=200) │
└─────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────┐
│  vector_store.py                                        │
│  ├─ HuggingFace Embeddings (all-MiniLM-L6-v2, 384-dim) │
│  └─ FAISS in-memory index (MMR retrieval)               │
└─────────────────────────────────────────────────────────┘
 │
 ▼
┌─────────────────────────────────────────────────────────┐
│  rag_chain.py                                           │
│  ├─ LangChain RetrievalQA chain                         │
│  ├─ Claude Sonnet (claude-sonnet-4-5) via Anthropic API │
│  ├─ Conversation memory (last 10 turns)                 │
│  └─ Source URL citation                                 │
└─────────────────────────────────────────────────────────┘
 │
 ▼
Answer + Sources → User
```

### Key design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | `claude-sonnet-4-5` | Best balance of quality and speed; strong instruction-following |
| Embeddings | `all-MiniLM-L6-v2` | Runs on CPU, no extra API key, 384-dim is sufficient for docs |
| Vector store | FAISS (in-memory) | Zero-config, fast for up to ~50k chunks |
| Retrieval | MMR (k=5) | Maximises diversity + relevance; avoids repetitive chunks |
| Splitting | `RecursiveCharacterTextSplitter` | Respects paragraph/sentence boundaries |
| Temperature | 0.2 | Factual answers with minimal creative drift |

---

## Quick Start

### 1. Prerequisites

- Python **3.10+**
- An [Anthropic API key](https://console.anthropic.com/)

### 2. Clone & Install

```bash
git clone https://github.com/your-org/api-rag-agent.git
cd api-rag-agent

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 4. Run

```bash
# Interactive mode (prompts you for URL)
python main.py

# Pass URL directly
python main.py --url https://developers.facebook.com/docs/graph-api/

# Single-page mode (no crawling)
python main.py --url https://stripe.com/docs/api --no-crawl

# Retrieve more chunks per query
python main.py --url https://docs.github.com/en/rest --k 8
```

---

## CLI Options

```
usage: main.py [-h] [--url URL] [--no-crawl] [--k K]
               [--chunk-size CHUNK_SIZE] [--chunk-overlap CHUNK_OVERLAP]

Options:
  --url URL                API documentation URL to load
  --no-crawl               Only index the exact URL (no link following)
  --k K                    Chunks to retrieve per query (default: 5)
  --chunk-size CHUNK_SIZE  Characters per chunk (default: 1000)
  --chunk-overlap OVERLAP  Overlap between chunks (default: 200)
```

### In-session commands

| Command | Action |
|---------|--------|
| `/reset` | Clear conversation history |
| `/sources` | Show source URLs from last answer |
| `/url` | Load a new documentation URL |
| `/help` | Show command reference |
| `/quit` | Exit |

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Model identifier |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `MAX_TOKENS` | `2048` | Max Claude response tokens |
| `RETRIEVAL_K` | `5` | Top-k chunks retrieved per query |
| `CHUNK_SIZE` | `1000` | Character chunk size |
| `CHUNK_OVERLAP` | `200` | Chunk overlap |

---

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Project Structure

```
api-rag-agent/
├── main.py                  # CLI entry point & interaction loop
├── src/
│   ├── document_loader.py   # URL fetch, parse, chunk
│   ├── vector_store.py      # Embedding + FAISS index
│   └── rag_chain.py         # Claude LLM + retrieval chain + memory
├── tests/
│   ├── test_document_loader.py
│   └── test_rag_chain.py
├── docs/
│   └── architecture.md      # Mermaid architecture diagram
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Supported Documentation Sites

Tested and working with:

- ✅ **Facebook / Meta** — `developers.facebook.com/docs/`
- ✅ **Stripe** — `stripe.com/docs/api`
- ✅ **GitHub REST API** — `docs.github.com/en/rest`
- ✅ **Twilio** — `twilio.com/docs`
- ✅ **OpenAI** — `platform.openai.com/docs`
- ✅ **Any publicly accessible HTML documentation site**

> **Note:** Sites behind login walls, heavy JavaScript SPAs, or with aggressive bot protection (Cloudflare) may return limited content. Use `--no-crawl` and target specific sub-pages in those cases.

---

## How RAG Works (For Non-Technical Users)

Think of it like this:

1. **Fetch** — The agent reads the API documentation website, just like you would in a browser.
2. **Chunk** — It splits the content into small, searchable passages (like index cards).
3. **Embed** — Each passage is converted into a numerical "fingerprint" that captures its meaning.
4. **Retrieve** — When you ask a question, the agent finds the index cards most relevant to your question.
5. **Answer** — Claude reads those cards and writes a clear, grounded answer — without making things up.

---

## Extending the Agent

### Swap the embedding model
Edit `.env`:
```
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2   # higher quality, slower
```

### Swap the Claude model
```
CLAUDE_MODEL=claude-opus-4-5    # most capable, higher cost
CLAUDE_MODEL=claude-haiku-4-5   # fastest, lowest cost
```

### Persist the vector store
In `vector_store.py`, after `FAISS.from_documents(...)`, add:
```python
vector_store.save_local("./vector_store")
```
And load on subsequent runs with:
```python
vector_store = FAISS.load_local("./vector_store", embeddings)
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

Pull requests welcome. Please open an issue first to discuss major changes.

1. Fork → branch → commit → PR
2. Run `pytest tests/` and ensure all tests pass
3. Follow existing code style (type hints, docstrings, Rich for console output)
