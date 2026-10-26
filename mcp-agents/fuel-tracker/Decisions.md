# Decisions.md

## Why every architectural choice was made (and what was rejected)

### 1. MCP Server (chosen) vs. standalone web API (rejected)

- **Chosen**: MCP server (stdio-based). Fuel prices are most useful in context — when planning a trip or deciding where to fill up. An MCP server lets any AI assistant ask about prices inline without switching to a separate app.
- **Rejected**: Standalone Flask/FastAPI web service. Would require its own hosting, auth, and a client UI. Adds operational overhead for no benefit — the user's AI assistant is already the best interface.
- **Rejected**: CLI-only tool. No ability for AI agents to query programmatically.

### 2. MCPServer (MCP 2.x) (chosen) vs. low-level Server class (rejected)

- **Chosen**: `MCPServer` with `@server.tool()` decorator. Clean API, handles protocol negotiation, transport, and error serialisation automatically. ~30 lines of boilerplate vs. ~100 for manual JSON-RPC handling.
- **Rejected**: `mcp.server.Server` low-level API. Requires manual request routing, tool registration, and JSON-RPC message framing. More code, more surface for bugs.
- **Rejected**: Third-party MCP frameworks. No need — `MCPServer` is mature, well-documented, and handles everything we need.

### 3. httpx (chosen) vs. urllib / requests / aiohttp (rejected)

- **Chosen**: `httpx`. Modern sync API, connection pooling, timeout handling, native JSON support. Same interface whether sync or async.
- **Rejected**: `urllib.request`. Bare-bones stdlib — no connection pooling, no clean timeout API, verbose error handling.
- **Rejected**: `requests`. Well-understood but unmaintained for new features; `httpx` is its spiritual successor with a near-identical API.
- **Rejected**: `aiohttp`. Would force async-only code. Our MCP server is sync (MCPServer's default), so adding async complexity brings no benefit.

### 4. Lazy global client singleton (chosen) vs. per-call instantiation (rejected)

- **Chosen**: A module-level `_client` variable initialised on first use. Keeps a single connection pool alive across tool invocations without forcing the caller to manage lifecycle.
- **Rejected**: Create a new `FuelWideClient()` per tool call. Each call would open fresh TCP connections — wasteful for a server that may handle many requests.
- **Rejected**: Dependency injection. Over-engineered for a single-file server with three tools.

### 5. Formatted markdown strings (chosen) vs. raw JSON (rejected for overview)

- **Chosen**: `get_fuel_prices` returns human-readable markdown with country names, fuel types, and prices. The AI assistant can read it directly and answer user questions without further processing.
- **Rejected**: Return raw JSON always. AI models can read JSON, but it wastes tokens and the formatting is less useful for conversational answers.
- **Compromise**: `get_country_fuel_prices` returns raw JSON — detailed data with provenance fields needs structure, not prettification.

### 6. FuelWide API (chosen) vs. other fuel price APIs (rejected)

- **Chosen**: FuelWide (fuelwide.com). Free, no API key, CORS-enabled, returns national averages + station-level data, covers 28+ markets, well-documented.
- **Rejected**: EIA/AAA API (USA only). Requires API key registration, US-only data, less useful for global users.
- **Rejected**: OpenStreetMap/Overpass. Can find stations but has no price data. Would need a separate price source.
- **Rejected**: GasBuddy. Requires commercial license and API key — not free for redistribution.

### 7. CLI quick-test mode (chosen) vs. always-serve mode (rejected)

- **Chosen**: `--country DE` flag runs a one-shot lookup instead of starting the MCP server. Useful for debugging and testing without needing an MCP client.
- **Rejected**: Always serve MCP. The user may want to quickly check "does the API work?" without configuring a client.

### 8. Package structure (fuel_tracker/server.py) (chosen) vs. flat file (rejected)

- **Chosen**: Proper Python package (`fuel_tracker/__init__.py` + `fuel_tracker/server.py`). Clean `python -m fuel_tracker.server` invocation, testable imports, pip-installable.
- **Rejected**: Single `server.py` at repo root + `import fuel_tracker.server` fails without sys.path manipulation. The package structure costs one extra file but avoids import headaches.

### 9. Station response capped at 50 (chosen) vs. unlimited (rejected)

- **Chosen**: Cap displayed stations at 50 with an overflow note. Prevents token flooding in AI context windows. The API allows up to 5000 — the cap is display-only, the full list is in the raw response.
- **Rejected**: Show all stations. A user asking "nearby" likely wants the top 50 cheapest or closest, not 5000 entries.

### 10. Synchronous server (chosen) vs. async (rejected)

- **Chosen**: Synchronous tools with `httpx.Client` (sync). MCPServer handles sync functions natively without wrapping or event-loop management.
- **Rejected**: Async with `httpx.AsyncClient` and async tool functions. Adds `asyncio.run()` complexity, no performance benefit for a stateless API wrapper that makes one or two HTTP calls per tool invocation.

### 11. Test doubles via mock (chosen) vs. integration tests (rejected)

- **Chosen**: `unittest.mock` for all tests. Tests run in <1s, no network dependency, deterministic results.
- **Rejected**: Hit the live FuelWide API. Would break in CI, require rate-limit handling, and produce flaky results. Integration testing is a manual step.

### 12. Attribution requirement surfaced (chosen) vs. ignored (rejected)

- **Chosen**: README and docs note that each API response includes an `attribution` field that must be reproduced per the data licence. Not enforced in code but documented.
- **Rejected**: Skip attribution. The data licences explicitly require credit to the original publisher — FuelWide credit alone doesn't satisfy them. Ignoring could create legal exposure for the user.

### 13. Single-module server (chosen) vs. split across files (rejected)

- **Chosen**: All server logic in one `server.py` file (~350 lines). The client wrapper, tools, and entry point are small enough that splitting would add `import` chains without reducing complexity.
- **Rejected**: Separate `client.py`, `tools.py`, `main.py`. Would add 3 extra files and cross-module import management for a project that still fits comfortably in one screen.