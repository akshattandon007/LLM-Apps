# 📚 BookWorm MCP — Book Search & Discovery MCP Server

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![API: Open Library](https://img.shields.io/badge/API-Open_Library_(free,_zero--auth)-orange)](https://openlibrary.org)

**BookWorm MCP** is an MCP server that connects AI agents to the Open Library catalog — 6M+ books, 10M+ editions, 300K+ authors. Search by title/author, look up ISBNs, browse subjects, get author bios, and retrieve cover images. No API keys, no signup, completely free.

> **Perfect for:** "Find me five books like Dune", "What's the author's full name?", "Show me popular fantasy novels", "Get the cover of this edition"

## ✨ Tools

| Tool | Description |
|------|-------------|
| `search_books(query, limit, page)` | Search books by title, author, or keywords |
| `get_book(isbn, olid)` | Get detailed edition info by ISBN (10/13) or Open Library ID |
| `get_author(author_id, include_works)` | Author bio, dates, and notable works |
| `search_subject(subject, limit, page)` | Browse books by topic (fantasy, cooking, space...) |
| `search_authors(query, limit)` | Find authors by name |
| `get_book_cover(olid, size)` | Get cover image URL (S/M/L) |
| `get_trending(limit)` | Recently active/popular books |

## 🚀 Quick Start

### Install

```bash
# Clone the repo
cd mcp-agents/bookworm

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e ".[cli]"
```

### Run

```bash
# Start the MCP server over stdio
bookworm
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bookworm": {
      "command": "python3",
      "args": ["-m", "bookworm"],
      "cwd": "/path/to/LLM-Apps/mcp-agents/bookworm",
      "env": {}
    }
  }
}
```

### Usage Examples

Once connected, you can ask Claude:

- *"Search for books about machine learning"*
- *"Find the author J.R.R. Tolkien and show me his works"*
- *"Look up ISBN 0451526538"*
- *"What are some popular fantasy books?"*
- *"Show me the cover of book OL123M"*
- *"Find books on the subject of astronomy"*

## 🔧 How It Works

BookWorm MCP wraps the [Open Library API](https://openlibrary.org/developers/api) — the free, public book catalog from the Internet Archive. Every request is identified with a custom User-Agent (recommended practice) and rate-limited to 3 req/sec.

The server is built on **FastMCP** (Python MCP framework) with **httpx** for HTTP communication.

## 📁 Project Structure

```
bookworm/
├── bookworm/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── server.py            # MCP tool definitions + data cleaning
│   └── open_library_client.py  # Open Library HTTP client with rate limiting
├── tests/
│   ├── __init__.py
│   └── test_server.py       # Unit tests + optional integration tests
├── requirements.txt
├── pyproject.toml
├── README.md
├── Decisions.md             # Architecture decision record
└── Flow.md                  # Execution trace and data flow
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-mock

# Run unit tests (mocked, fast, no network needed)
pytest tests/ -v

# Run integration tests (hits real API)
pytest tests/ -v -m integration
```

## 📋 API Coverage

| Feature | Status |
|---------|--------|
| Book search (title/author/keywords) | ✅ |
| ISBN lookup (10 & 13 digit) | ✅ |
| Open Library ID lookup | ✅ |
| Author details + bio | ✅ |
| Author works listing | ✅ |
| Author photo URL | ✅ |
| Subject/category browsing | ✅ |
| Book cover images | ✅ |
| Author search by name | ✅ |
| Trending/popular books | ✅ |
| Rate limiting (3 req/sec) | ✅ |

## 📜 License

MIT — feel free to use, modify, and share.

## 📚 Data Source

[Open Library](https://openlibrary.org/) — an open, editable library catalog from the Internet Archive. Contains records for over 45 million books across 300+ languages. Data is CC-BY-SA licensed.