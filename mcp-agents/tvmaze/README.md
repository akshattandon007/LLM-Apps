# 📺 TVMaze MCP Server

Search TV shows, browse episodes, check cast, and look up TV schedules — all through natural conversation with your AI agent. Powered by the free [TVMaze API](https://www.tvmaze.com/api) (no API key required).

## ✨ What It Does

- **Search shows** — find any TV show by name with ratings, genres, networks, and status
- **Show details** — get full metadata: air dates, network, summary, poster images
- **Episode lists** — browse all episodes, filter by season
- **Cast info** — who played who in any show
- **TV schedule** — what's airing tonight in any country
- **Celebrity search** — find actors, writers, and producers by name

## 🚀 Quick Start

```bash
# Install
pip install "mcp[cli]>=1.0.0,<2.0.0" httpx

# Run (stdio mode — for Claude Desktop, Cursor, etc.)
python -m mcp run server.py

# Or with uv
uv run --with mcp python -m mcp run server.py
```

### Claude Desktop Config

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tvmaze": {
      "command": "uv",
      "args": [
        "run",
        "--with", "mcp",
        "--with", "httpx",
        "python", "-m", "mcp", "run",
        "/path/to/tvmaze/server.py"
      ]
    }
  }
}
```

_or with pip:_

```json
{
  "mcpServers": {
    "tvmaze": {
      "command": "python",
      "args": [
        "-m", "mcp", "run",
        "/path/to/tvmaze/server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/tvmaze"
      }
    }
  }
}
```

## 🎯 Available Tools

| Tool | What it does |
|------|-------------|
| `search_tv_shows(query)` | Search shows by name |
| `get_show_details(show_id)` | Full details for a show |
| `get_episode_list(show_id, season?)` | Episodes, optionally filtered by season |
| `get_cast_list(show_id)` | Cast members for a show |
| `get_tv_schedule(country, date?)` | TV schedule by country and date |
| `search_celebrities(name)` | Find actors, writers, producers |

## 💬 Example Queries

> "What shows are about dragons?"
> → `search_tv_shows("dragons")`

> "Tell me about House of the Dragon"
> → `get_show_details(show_id=53078)`

> "What's on TV tonight in the UK?"
> → `get_tv_schedule(country="GB")`

> "Who played Tyrion Lannister?"
> → `get_cast_list(show_id=82)` then look for the character

## 🧪 Running Tests

```bash
cd tv-maze-mcp
pip install "mcp[cli]>=1.0.0,<2.0.0" httpx pytest pytest-asyncio
python -m pytest tests/ -v
```

## 📁 Project Structure

```
tvmaze/
├── server.py            # MCP server — tool definitions
├── tvmaze_client.py     # API client + data models
├── requirements.txt     # Python dependencies
├── Decisions.md         # Architectural decisions log
├── Flow.md              # Execution flow documentation
├── README.md            # This file
└── tests/
    └── test_tvmaze.py   # Tests (client mock + server import checks)
```

## ⚡ Features

- **Zero config** — no API keys, no .env, no signup
- **Graceful degradation** — returns simulated data when the API is unreachable
- **Testable** — MockTransport injection for deterministic testing
- **Fast** — synchronous httpx, sub-second typical responses

## 📜 License

MIT — free to use, modify, and share.