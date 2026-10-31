# Decisions.md — BookWorm MCP

## 1. Project Type: MCP Server (not CLI tool)
- **Chosen:** Python MCP server with FastMCP framework
- **Rejected:** Plain CLI tool, web app, REST API wrapper
- **Why:** The rota category is MCP Agents. MCP servers integrate directly with Claude Desktop and any MCP-compatible client, making the book data accessible through natural language. A CLI-only tool would not count as an MCP agent.

## 2. API: Open Library (not Google Books, not ISBNdb)
- **Chosen:** Open Library (free, zero-auth, generous rate limits)
- **Rejected:** Google Books API (requires API key + OAuth for some features), ISBNdb (rate-limited free tier, API key required), Goodreads API (deprecated key system)
- **Why:** Open Library is free, requires zero authentication, has a well-documented REST API, and provides rich metadata (search, authors, subjects, covers). Rate limit of 3 req/sec with User-Agent header is sufficient for an MCP server serving individual queries.

## 3. Framework: FastMCP (not raw stdio MCP server)
- **Chosen:** `mcp[cli]` package with FastMCP
- **Rejected:** Custom raw stdio JSON-RPC implementation, `mcp` without FastMCP
- **Why:** FastMCP provides automatic tool registration, input validation via Pydantic, and clean error handling out of the box. Raw JSON-RPC over stdio would require manual request parsing, response formatting, and error boundary management — unnecessary complexity for a tool-focused MCP server.

## 4. Transport: stdio (not HTTP/SSE)
- **Chosen:** stdio transport
- **Rejected:** HTTP + SSE transport, streamable HTTP
- **Why:** stdio is the simplest transport for Claude Desktop integration. It requires zero network configuration, no open ports, and works reliably in containerized/headless environments. HTTP transport would be needed only for remote MCP gateways, which is not the primary use case.

## 5. HTTP Client: httpx (not requests, not urllib)
- **Chosen:** httpx
- **Rejected:** `requests` (synchronous only, no native connection pooling config), `urllib` (too low-level, manual connection management)
- **Why:** httpx provides connection pooling, timeout configuration, and clean async support if needed later. It's the de facto standard for modern Python HTTP clients alongside FastMCP.

## 6. Rate Limiting: Token-bucket per-call (not time-window batch)
- **Chosen:** Per-call rate limiter with 3 req/second cap
- **Rejected:** Async batching (adds complexity), no rate limiting (risks 429 errors)
- **Why:** A simple per-call limiter with time tracking ensures we never exceed Open Library's identified rate limit. Async batching would require restructuring the entire client for marginal throughput gain on a tool-by-tool MCP server.

## 7. Module Layout: package (bookworm/) not flat files
- **Chosen:** Package with `server.py` (MCP layer) + `open_library_client.py` (API layer)
- **Rejected:** Single flat file (`server.py` with everything), micro-services (overkill)
- **Why:** Separation of concerns — `server.py` defines MCP tools and data cleaning; `open_library_client.py` handles HTTP communication with Open Library. This makes both layers independently testable and modifiable.

## 8. Tool Surface: 7 focused MCP tools (not 2-3 big tools)
- **Chosen:** 7 tools: search_books, get_book, get_author, search_subject, search_authors, get_book_cover, get_trending
- **Rejected:** 2-3 monolithic tools with many optional parameters, 12+ micro-tools
- **Why:** 7 tools provides a complete book-discovery surface without overwhelming the user. Each tool has a clear single responsibility. The alternative of 2-3 large tools with many optional flags would make tool discovery harder for the LLM; 12+ micro-tools would clutter the tool list.

## 9. Output Format: Cleaned dicts (not raw API responses)
- **Chosen:** Extract and reshape API responses into flat, readable dicts
- **Rejected:** Pass through raw Open Library JSON, return markdown-formatted strings
- **Why:** MCP tools return structured data that the LLM can read and reason about. Raw API responses contain many irrelevant fields and deep nesting. Cleaned dicts include only what the user cares about: title, author, year, cover URL, page count, etc. Markdown strings would lose structured access.

## 10. Testing Strategy: Unit tests with mocks + optional integration tests
- **Chosen:** Mock httpx client for unit tests; integration tests behind `@pytest.mark.integration`
- **Rejected:** Integration-only tests (slow, fail without network), unit-only tests (miss real API behavior)
- **Why:** Mocked unit tests run fast and verify logic for all edge cases (empty results, missing fields, error handling). Integration tests are available for manual verification against the real API but don't run in CI by default.

## 11. User-Agent Identification (not anonymous requests)
- **Chosen:** Identify the application with `BookWormMCP/1.0 (bookworm-mcp; mailto:akshattandon4@gmail.com)`
- **Rejected:** Anonymous requests (no User-Agent), fake User-Agent
- **Why:** Open Library explicitly requests identification for higher rate limits (3/sec vs 1/sec). Including a contact email is the responsible developer practice and ensures the API remains available for legitimate use.

## 12. Cover Images: URL references (not data URIs)
- **Chosen:** Return cover image URLs from Open Library's covers API
- **Rejected:** Download and embed cover images as base64 data URIs, skip covers entirely
- **Why:** URLs are lightweight (no bandwidth/storage cost) and the LLM can access them lazily or present them to the user. Base64 encoding would make responses huge. Skipping covers would make results less useful for visual identification.

## 13. ISBN Handling: Accept both ISBN-10 and ISBN-13
- **Chosen:** Accept any 10- or 13-digit string as an ISBN
- **Rejected:** Validate checksum, reject non-numeric, require specific format
- **Why:** Open Library's API accepts both formats and handles validation. Pre-validating in our code would add complexity with no benefit — the API returns a clean error if the ISBN is invalid.

## 14. Error Handling: Return error dicts (not raise exceptions to client)
- **Chosen:** Return `{"error": "message"}` dicts for API errors/missing books
- **Rejected:** Let HTTP exceptions propagate to FastMCP, return Python exceptions
- **Why:** FastMCP propagates exceptions as server errors. Returning structured error dicts lets the LLM see the error and explain to the user. The alternative (raw exception propagation) produces opaque failure messages that confuse both the LLM and the user.