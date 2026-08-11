# 🧭 Code Compass

> **Find the code you need by describing what it does, not by remembering what it's called.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204-CC774D?style=flat-square&logo=anthropic)](https://anthropic.com)
[![FAISS](https://img.shields.io/badge/FAISS-1.8%2B-6559C5?style=flat-square)](https://github.com/facebookresearch/faiss)
[![sentence-transformers](https://img.shields.io/badge/sentence--transformers-all--MiniLM--L6--v2-FF6F00?style=flat-square)](https://sbert.net)
[![tree-sitter](https://img.shields.io/badge/tree--sitter-AST-4FC08D?style=flat-square)](https://tree-sitter.github.io/tree-sitter/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=next.js)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

---

## 🗺️ What is Code Compass?

Code Compass is a **codebase RAG app** that lets you search your source code using natural language. Instead of guessing filenames or grepping for variable names, just describe what the code does.

**Example queries that work out of the box:**

| You ask | Code Compass finds |
|---------|-------------------|
| *"Where do we validate JWT tokens?"* | The JWT validation function/middleware with exact file + line numbers |
| *"Find the payment retry logic"* | The retry handler, its exponential backoff, and where it logs failures |
| *"How do we connect to the database?"* | The connection setup, config, and pool management |
| *"Show me the user registration flow"* | The full registration pipeline from validation to DB insert |
| *"What's the schema for the Order model?"* | The model definition with all fields, types, and relationships |

Each answer comes with **file paths, line numbers, and code snippets** so you never have to guess where something lives.

---

## 🏗️ Architecture

Code Compass follows a classic **Ingest → Chunk → Embed → Retrieve → Generate** pipeline:

```
┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│  Ingest   │ →  │  Chunk    │ →  │    Embed     │ →  │ Retrieve │ →  │ Generate │
│ (walk     │    │ (tree-    │    │ (sentence-   │    │ (FAISS   │    │ (Claude  │
│  dirs)    │    │  sitter   │    │  transformers)│    │  IP      │    │  Sonnet) │
│           │    │  AST)     │    │              │    │  search) │    │          │
└──────────┘    └───────────┘    └──────────────┘    └──────────┘    └──────────┘
```

### 1. 📂 Ingest — `code_loader.py`
Walks a directory tree, skipping `node_modules`, `.git`, `__pycache__`, and other noise. Picks up `.py`, `.js`, `.ts`, `.jsx`, `.tsx` files. Files over 1 MB get skipped.

### 2. ✂️ Chunk — `chunker.py`
The secret sauce. Uses **tree-sitter AST parsing** to split source code at **function and class boundaries** — you get whole, meaningful units, not arbitrary line slices. Extracts docstrings and metadata along the way. Falls back to line-based heuristics if tree-sitter isn't available for a language.

Supported languages: **Python**, **JavaScript**, **TypeScript** (more coming).

### 3. 🧬 Embed — `embedder.py`
Each code chunk is turned into a 384-dimensional vector using **`all-MiniLM-L6-v2`** (sentence-transformers). The embedding text includes the docstring, file path, function/class name, and the code itself, so semantic meaning is preserved.

### 4. 🔍 Retrieve — `vector_store.py`
A **FAISS** index (`IndexFlatIP` — inner product for cosine similarity) stores the vectors. When you ask a question, the query is embedded with the same model and the top-5 most similar chunks are retrieved with relevance scores.

### 5. 🤖 Generate — `rag_chain.py`
The retrieved chunks plus your question are sent to **Claude Sonnet 4** (via `langchain-anthropic`) with a system prompt that tells it to cite exact file paths, line numbers, and code snippets. No API key? A fallback mode returns structured results from the vector search alone.

### 🌐 Frontend
A lightweight **Next.js** chat UI at `frontend/` provides a clean conversational interface. Ingest a codebase with the 📂 button, ask questions in the chat box, and see answers with source references.

---

## 🚀 Setup

```bash
# 1. Clone the repo (if you haven't already)
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/rag/code-compass

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Anthropic API key (optional — works without it in fallback mode)
cp .env.example .env
# Edit .env and paste your key: ANTHROPIC_API_KEY=sk-ant-...
```

### Start the API server

```bash
uvicorn main:app --reload --port 8000
```

The API docs are available at http://localhost:8000/docs.

### Start the frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:3000.

---

## 🧪 Try It Out

We've included a **sample project** under `data/sample-project/` so you can experiment right away.

```bash
# After starting the server, ingest the sample project:
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "./data/sample-project"}'

# Then ask a question:
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How are todos validated?", "top_k": 5}'
```

Or use the **Next.js frontend** at http://localhost:3000 for a chat-based experience.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Server status, indexed file/chunk counts |
| `/api/ingest` | POST | Ingest a codebase directory |
| `/api/query` | POST | Ask a question about the codebase |
| `/api/clear` | POST | Clear the index and start fresh |

---

## 🧠 Why This Approach?

- **AST-aware chunking** beats line-based splitting because functions and classes are the atomic units of code understanding. A question like "find the retry logic" maps to a function — not a random 50-line slice.
- **Semantic search** means you find code by *what it does*, not by what someone decided to name it five months ago.
- **Citations in every answer** means you can jump directly to the relevant file and line — no treasure hunts.
- **Fallback without an LLM key** means the retrieval layer works standalone; Claude just adds the natural-language explanation on top.

---

## 🧰 Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Chunking:** tree-sitter (Python, JavaScript, TypeScript grammars)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector Search:** FAISS (IndexFlatIP, 384-dim)
- **LLM:** Claude Sonnet 4 via langchain-anthropic
- **Frontend:** Next.js 15, React
- **Models:** Pydantic v2

---

## 📁 Project Structure

```
code-compass/
├── main.py                 # FastAPI server (ingest, query, status, clear)
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── src/
│   ├── __init__.py         # Package init
│   ├── models.py           # Pydantic schemas (Chunk, Query, etc.)
│   ├── code_loader.py      # Directory walker with ignore rules
│   ├── chunker.py          # AST-based chunking (tree-sitter)
│   ├── embedder.py         # sentence-transformers wrapper
│   ├── vector_store.py     # FAISS index + persistence
│   └── rag_chain.py        # RAG pipeline + Claude generation
├── frontend/               # Next.js chat UI
│   ├── pages/
│   │   ├── index.js        # Chat interface
│   │   └── api/proxy.js    # API proxy for CORS
│   └── package.json
├── data/
│   └── sample-project/     # Sample codebase to test with
└── tests/
    └── test_smoke.py       # Smoke tests
```

---

## 📜 License

MIT — go build something cool.