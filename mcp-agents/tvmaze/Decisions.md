# TVMaze MCP Server — Decisions

## 1. MCP SDK Choice: `mcp[cli]` v1 (not raw stdio)
- **Chosen:** `mcp[cli]>=1.0.0,<2.0.0` (FastMCP interface)
- **Rejected:** Raw stdio server (too much boilerplate), `mcp>=2.0.0` (API breaking changes — FastMCP renamed to MCPServer)
- **Why:** FastMCP provides the cleanest decorator-based tool API, auto-generates JSON schema from type hints, and handles stdio transport. Pinning `<2` avoids the v2 constructor breakage.

## 2. Client Library: httpx (not requests, not aiohttp)
- **Chosen:** `httpx` with synchronous mode
- **Rejected:** `requests` (no mock transport built-in), `aiohttp` (async adds complexity for no benefit in this context)
- **Why:** httpx ships `MockTransport` which lets us inject mock responses in tests without monkey-patching network calls. The TVMaze API is simple REST — no streaming, no WebSockets — so sync is sufficient.

## 3. Dependency Injection for Testability: `set_client()` function
- **Chosen:** Module-level `_client` global with `set_client()` setter and `_get_client()` factory
- **Rejected:** Pass client through every function (noisy API), use environment variable (too implicit)
- **Why:** Tests can inject `httpx.Client(transport=MockTransport(...))` to simulate any API scenario without hitting the real network. Production code calls `_get_client()` which returns the injected client or creates a default one.

## 4. Simulated Fallback Mode
- **Chosen:** Each function wraps real API calls in try/except, falling back to `simulate_*` functions
- **Rejected:** Hard fail on network error (poor UX), use web scraping as backup (fragile)
- **Why:** The MCP server should never crash the agent. Simulated data lets the agent demonstrate the tool's shape and output format even when offline, with a `source="simulated"` field clearly marking fake data.

## 5. Data Models: Dataclasses with `from_dict` constructors
- **Chosen:** `@dataclass` classes with `from_dict()` classmethods
- **Rejected:** Use raw dicts (no type safety), Pydantic models (heavy dependency), attrs (one more dependency)
- **Why:** Dataclasses give type safety and clear structure. The `source` field on every model traces data provenance. `from_dict` keeps the API translation in one place and is easy to test.

## 6. HTML Stripping in Summary Fields
- **Chosen:** Regex-based `<[^>]+>` stripping via `_strip_html()`
- **Rejected:** Use BeautifulSoup (heavy dep for one function), pass raw HTML to the agent (messy output)
- **Why:** TVMaze API returns summaries with `<p>`, `<b>`, `<i>` tags. Stripping them produces clean Markdown-compatible text. A simple regex is sufficient for the limited HTML subset.

## 7. Tool Design: One Tool Per Operation
- **Chosen:** Separate `search_tv_shows`, `get_show_details`, `get_episode_list`, `get_cast_list`, `get_tv_schedule`, `search_celebrities`
- **Rejected:** One mega-tool with a `mode` parameter (hard to discover), fewer tools with complex params (confusing)
- **Why:** MCP agents discover tools by name and schema. Each tool maps to one coherent question the agent might ask. Clear names + focused params = the agent uses the right tool.

## 8. Tool Output Format: Markdown Strings
- **Chosen:** Each tool returns a formatted Markdown string
- **Rejected:** Return raw JSON/dict (agent sees ugly formatted text), return structured data list (agents prefer human-readable text for tools)
- **Why:** MCP tool responses are shown to the LLM as text. Clean Markdown with bold headers, bullet lists, and emoji delimiters produces the best agent comprehension of search results.

## 9. Error Handling: Graceful Degradation
- **Chosen:** Wrap API calls in try/except, return user-friendly error messages, fall back to simulated data for searches/episodes
- **Rejected:** Raise exceptions to the MCP framework (agent gets an opaque error), silent empty returns (confusing)
- **Why:** An agent needs to understand why a tool failed. Friendly error messages let the agent try a different approach or inform the user.

## 10. Project Structure: Flat Module Layout
- **Chosen:** `server.py` + `tvmaze_client.py` + `tests/` in the project root
- **Rejected:** `src/` directory (unnecessary nesting for a single-server project), package with `__init__.py` and submodules (over-engineered)
- **Why:** The server is a single MCP tool collection with a thin client layer. Flat layout keeps imports simple (`from tvmaze_client import ...`) and avoids redundant nesting.

## 11. test Strategy: Client Mocking + Import Verification
- **Chosen:** Mock the httpx transport layer for client tests; verify server tool imports for server tests
- **Rejected:** End-to-end tests hitting real TVMaze API (rate-limited, slow, unreliable), pure unit tests with no network simulation (miss integration bugs)
- **Why:** MockTransport tests every API path deterministically. Server tests verify the tool functions are properly decorated and importable. The combination catches logic bugs and API mapping errors without external dependencies.

## 12. Configuration: No .env File Needed
- **Chosen:** The TVMaze API requires no API key or authentication
- **Rejected:** Add an API key slot "just in case" (YAGNI), require env vars for setup (friction)
- **Why:** The entire value of TVMaze as an MCP server is zero-config. Adding auth infrastructure would defeat that purpose. If TVMaze ever introduces auth, we can add `--api-key` then.

## 13. No Async in Client Layer
- **Chosen:** Synchronous httpx calls in the client, FastMCP wraps them as async tools
- **Rejected:** Full async client with `httpx.AsyncClient` (complexity), use `asyncio.to_thread` everywhere (waste)
- **Why:** FastMCP accepts sync functions and wraps them. The TVMaze API responses are sub-second. Async buys nothing here and adds cognitive overhead.

## 14. Scheduling: Country-Centric, Date-Optional
- **Chosen:** `get_tv_schedule(country="US", date=None)` — defaults to US, today
- **Rejected:** Require both country and date (annoying for the most common query), no default country (agent must always provide)
- **Why:** "What's on TV tonight?" is the most common schedule query. Defaulting to US covers the most frequent use case while allowing any country override.