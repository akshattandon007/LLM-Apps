# Decisions — WikiPilot

## Why every architectural choice was made (and what was rejected)

### 1. MCP Server vs Standalone CLI
**Chosen:** MCP Server  
**Rejected:** Interactive CLI, Web UI, Python library  
**Why:** The user's repo is organised by agent type, and today's slot is MCP Agents. An MCP server plugs directly into Claude, Cline, and other MCP hosts — no extra UI code to maintain. A CLI would need a separate argument parser, formatting, and pagination. A web UI would balloon scope (auth, routing, CSS). MCP gives the richest integration per line of code.

### 2. FastMCP vs Low-Level Server
**Chosen:** `FastMCP` (from `mcp.server.fastmcp`)  
**Rejected:** Raw `mcp.server.Server` with manual tool schemas and JSON-RPC dispatch  
**Why:** Every other MCP server in the repo (`tvmaze`, `breathesmart`, `ratemate`) uses `FastMCP`. It auto-generates JSON Schema from Python type hints, handles the handshake/list/call protocol, and produces clean `CallToolResult` objects. The low-level `Server` class requires hand-writing every schema dict — error-prone and harder to maintain. Consistent with repo convention.

### 3. Wikipedia REST v1 vs Legacy action=query API
**Chosen:** Both (REST v1 for summaries/content, action=query for search/categories)  
**Rejected:** REST v1 only, action=query only, third-party wrappers (wikipedia-py, etc.)  
**Why:** The REST v1 API (`/page/summary/`, `/feed/onthisday/`) is cleaner — returns ready-to-use JSON with thumbnails, extracts, and structured metadata. But it lacks search and category listing. The legacy `action=query` API handles those. Using both gives the best coverage. Third-party wrappers add dependency overhead and often lag behind API changes.

### 4. urllib vs requests vs httpx
**Chosen:** `urllib.request` (stdlib)  
**Rejected:** `requests`, `httpx`, `aiohttp`  
**Why:** For a simple JSON-over-HTTP client with no streaming, sessions, or async needed, stdlib `urllib` keeps the zero-dependency promise. `requests` and `httpx` would add 2+ transitive deps each for one `urlopen` call per function. The client is short and the Wikipedia API is stable — no need for connection pooling or retry logic.

### 5. Synchronous vs Async Handlers
**Chosen:** Synchronous (blocking) functions with `FastMCP` sync support  
**Rejected:** `async/await` everywhere  
**Why:** The client calls one URL at a time with no I/O concurrency (Wikipedia rate-limits aggressive clients anyway). Sync code is simpler to read, test, and debug. `FastMCP` transparently wraps sync functions as async coroutines for the transport layer. If concurrency were needed later, each tool could be made `async` individually without changing the client.

### 6. Plain-String Returns vs Structured JSON Returns
**Chosen:** Formatted markdown strings  
**Rejected:** Raw JSON dicts, pydantic models  
**Why:** `FastMCP` tools returning `str` render beautifully in Claude's chat — the LLM sees human-readable markdown and can quote/rephrase it. Raw JSON forces the LLM to parse and reformat. Pydantic models would impose a serialization step for little gain. The markdown includes emoji headers, bold titles, and clickable links — zero-effort UX.

### 7. Error Handling Strategy
**Chosen:** Catch all known errors per tool, return user-friendly markdown messages  
**Rejected:** Raise exceptions to the MCP transport layer, return error codes  
**Why:** When an article isn't found, suggesting the user search instead is more helpful than a cryptic `ArticleNotFound` traceback. The pattern is: try → catch → return a helpful string. Network errors show the failure cause but also suggest retrying. Edge-case exceptions (unexpected API changes) still propagate.

### 8. Test Design — Live API vs Mocks
**Chosen:** Tests against the real Wikipedia API  
**Rejected:** Mocked/recorded HTTP responses (VCR.py, responses), fake data  
**Why:** The Wikipedia public API is free, zero-auth, and extremely reliable (>99.9% uptime). Mocking would freeze test data that goes stale (articles get edited, categories change). Live tests give real confidence — if the tests pass, the server works. Network-dependent tests are acceptable for a project whose entire purpose is network calls. One missing-article test is marked as an expected `ArticleNotFound` exception.

### 9. Single Client Module vs Split by Resource
**Chosen:** One `wikipilot_client.py` module with all API functions  
**Rejected:** Separate modules per resource (`search.py`, `summary.py`, `history.py`), one class per endpoint  
**Why:** The client is ~200 lines with 8 functions — splitting it into 8 files would add import overhead and Makefile-like bools for no benefit. Each function is self-contained and takes its own parameters. A class wrapper (`WikipediaClient.search(...)`) would add ceremony without encapsulation benefit since there's no mutable state (no API key, no session).

### 10. Project Structure — Flat vs Package
**Chosen:** Flat: `server.py` + `wikipilot_client.py` at the project root  
**Rejected:** Nested package (`wikipilot/server.py`, `wikipilot/client.py`, `wikipilot/__init__.py`), single file  
**Why:** A flat structure with two files is the simplest thing that works. A nested package needs `__init__.py`, `setup.py`/`pyproject.toml`, and `pip install -e .` for imports to resolve. For a small MCP server that runs via `python -m mcp run server.py`, the flat layout avoids all that. If the project grew to 10+ tools, a package split would be warranted.

### 11. User-Agent Header
**Chosen:** Custom `WikiPilotMCP/1.0` User-Agent with repo link  
**Rejected:** Default `Python-urllib/x.y`, no User-Agent  
**Why:** Wikipedia's API documentation explicitly asks for a descriptive User-Agent so they can identify and contact misbehaving clients. A generic `Python-urllib` string is impolite and risks being rate-limited. Including the repo URL gives the project a responsible contact point.

### 12. Rate Limiting
**Chosen:** No explicit rate limiter (one request per tool call)  
**Rejected:** Token bucket, exponential backoff, queue with delay  
**Why:** The MCP client (Claude, Cline) naturally paces requests — the LLM makes one tool call per reasoning step. Adding an artificial delay would frustrate users for no reason. Wikipedia's public API terms allow several hundred requests per minute; a single user making one call at a time won't come close. If heavy batch usage emerged, backoff could be added to the client module.

### 13. Date Defaulting — On This Day
**Chosen:** Default to today's UTC date if month/day omitted  
**Rejected:** Require both parameters, default to January 1, error if omitted  
**Why:** The most common use case is "what happened today?" — making the user look up today's date is friction. UTC prevents timezone confusion. The parameters accept explicit month/day when the user asks about April 5 or July 20.

### 14. Article Truncation
**Chosen:** 25,000 character truncation for full article content with a truncation notice  
**Rejected:** No truncation, 5,000 char limit, return as multiple chunks  
**Why:** Full articles can be 200K+ chars — exceeding context windows and response limits. 25K chars is enough for deep dives while staying within most model context limits (Claude 100K, GPT-4 32K). The truncation notice is honest. Multi-chunk responses would complicate the MCP message flow and aren't supported by the tool return shape.

### 15. Emoji Prefix Convention
**Chosen:** Emoji-first markdown formatting in tool outputs  
**Rejected:** Plain text, minimal formatting  
**Why:** Following the repo's established style (see `tvmaze`, `breathesmart`), emoji headers make tool outputs scannable and pleasant in chat. They're lightweight (pure text) and universal. Learning from existing repo conventions reduces cognitive load for both the user and the LLM interacting with the server.