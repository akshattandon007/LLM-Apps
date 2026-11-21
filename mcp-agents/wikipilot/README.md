# 📖 WikiPilot — Wikipedia Knowledge MCP Server

**Wikipedia at your fingertips.** WikiPilot is an MCP server that gives any MCP-compatible client (Claude, Cline, Continue, etc.) instant access to Wikipedia's entire knowledge graph — search, summaries, full articles, random discovery, on-this-day history, and related topics — all through a clean tool interface.

🔌 **Zero API keys.** No signup. No tokens. Just the free Wikipedia REST API.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run with any MCP client
python -m mcp run server.py
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wikipilot": {
      "command": "uv",
      "args": ["run", "--with", "mcp", "python", "-m", "mcp", "run", "/path/to/wikipilot/server.py"]
    }
  }
}
```

Or with pip:

```json
{
  "mcpServers": {
    "wikipilot": {
      "command": "python",
      "args": ["-m", "mcp", "run", "/path/to/wikipilot/server.py"]
    }
  }
}
```

---

## 🔧 Tools

| Tool | Description |
|------|-------------|
| `search_wikipedia` | Search articles by keyword. Returns titles, snippets, and links. |
| `summarize_article` | Get the first-paragraph summary of any article. |
| `read_article` | Get the full plain-text content of an article. |
| `random_article` | Discover a random Wikipedia page. |
| `today_in_history` | Historical events on any date (defaults to today). |
| `related_articles` | Find articles related to a given page. |
| `article_categories` | List the categories an article belongs to. |

---

## 💡 Example Queries

Once connected to an MCP client, try:

> "Search Wikipedia for quantum computing"
> "Summarize the article about the Eiffel Tower"
> "What happened on July 20th in history?"
> "Show me a random Wikipedia article"
> "What categories does 'Python (programming language)' belong to?"
> "Find articles related to Marie Curie"

---

## 🏗️ Architecture

```
server.py          ← FastMCP server — tool definitions and handlers
wikipilot_client.py ← Wikipedia REST API client — all network calls
tests/
  test_wikipilot.py ← 14 tests covering search, summary, article, random, on-this-day, categories, related, and edge cases
```

**Data flow:**
```
MCP Client → server.py (FastMCP) → wikipilot_client.py → Wikipedia REST API → JSON → cleaned text → MCP Client
```

---

## 🧪 Running Tests

```bash
cd mcp-agents/wikipilot
python -m pytest tests/ -v
```

Tests hit the live Wikipedia API (no mocking — we test against real data).

---

## 📦 Requirements

- Python 3.10+
- `mcp` (Model Context Protocol SDK)

---

## 📄 License

Same as the parent repo — see [LICENSE](../../LICENSE).