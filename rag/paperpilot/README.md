# 📄 PaperPilot — arXiv Research Paper RAG

**Ask questions about academic papers. Get grounded, cited answers.**

PaperPilot lets you search arXiv, ingest papers into a local embedding index, and ask natural language questions — all from your terminal. No API keys needed for search (arXiv is free), uses sentence-transformers for local embeddings.

## ✨ Features

- 🔍 **Search arXiv** by keyword, author, category (`cat:cs.LG`)
- 📥 **Ingest papers** into a local embedding index
- ❓ **Ask questions** with citation-grounded answers via LLM
- 📚 **List & summarise** your indexed library
- 💬 **Interactive Q&A mode** for deep dives
- 🏠 **All local** — embedding index stays on your machine

## 📦 Install

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/rag/paperpilot
pip install -r requirements.txt
```

Set your OpenRouter key (for LLM-powered answers):

```bash
export OPENROUTER_API_KEY=sk-...
```

Or set `OPENAI_API_KEY` if using an OpenAI-compatible endpoint.

## 🚀 Usage

### Search and ingest papers

```bash
python -m paperpilot search "transformer attention mechanisms"
```

Search arXiv by category:

```bash
python -m paperpilot search "cat:cs.LG" -n 20 --sort date
```

### Query your index

```bash
python -m paperpilot query "What are the key innovations of the Transformer architecture?"
```

Interactive Q&A session:

```bash
python -m paperpilot query --interactive
```

### List indexed papers

```bash
python -m paperpilot list
```

### Summarise everything

```bash
python -m paperpilot summary
```

## 🔧 CLI Reference

| Command | Description |
|---------|-------------|
| `search <query>` | Search arXiv and ingest papers |
| `query <question>` | Ask a question against indexed papers |
| `query --interactive` | Interactive Q&A session |
| `list` | Show all indexed papers |
| `summary` | Summarise all indexed papers |
| `--version` | Show version |

Search flags: `-n N` (max results), `--sort relevance|date`

Query flags: `-k N` (context chunks, default 5)

## 🧪 Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests use mock HTTP clients so they run offline — no network calls.

## 🛠 How It Works

1. **Search**: Queries the free arXiv API (no auth required, Atom XML response)
2. **Ingest**: Chunks paper abstracts → embeds with `all-MiniLM-L6-v2` (sentence-transformers)
3. **Index**: Stores embeddings as numpy array, persists to `~/.paperpilot/`
4. **Retrieve**: Encodes your question, finds top-K chunks by cosine similarity
5. **Generate**: Sends question + context to an LLM (via OpenRouter) for a grounded answer with source citations

## 📋 Data

Index lives in `~/.paperpilot/`:
- `index.json` — chunk metadata
- `embeddings.npy` — embedding vectors

Delete this directory to reset your index.

## 📄 License

MIT — do what you want with it.