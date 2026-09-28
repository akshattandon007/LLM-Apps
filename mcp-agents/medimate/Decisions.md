# Decisions.md — MediMate

## 1. Why an MCP agent (not a CLI or web app)
- **Chosen:** MCP agent (stdio-based server exposing tools).  
- **Rejected:** CLI tool (adds friction — user must open terminal), standalone web app (requires hosting + domain, overengineered for a drug lookup tool).  
- **Why:** MCP integrates directly into any LLM chat interface, letting users ask "What are the side effects of Drug X?" in plain English. Zero install friction beyond adding the server to their MCP config.

## 2. OpenFDA as the data source
- **Chosen:** OpenFDA (drug/label, drug/event, drug/ndc endpoints).  
- **Rejected:** NIH RxNav/RxNorm (interaction endpoints deprecated in 2026), Drugs@FDA (requires API key), GoodRx (commercial, no free API), insurance claims databases (locked down).  
- **Why:** OpenFDA is free, requires zero authentication, has 262k+ drug labels and 2M+ adverse event reports, and is federally mandated data updated weekly. No rate limit beyond 240 req/min with a User-Agent header.

## 3. Python over Node.js/TypeScript
- **Chosen:** Python 3.10+ with `httpx` and `mcp` Python SDK.  
- **Rejected:** Node.js with Express (heavier setup, more boilerplate for MCP), Rust (compile overhead, minimal benefit for an I/O-bound API wrapper).  
- **Why:** The `mcp` Python SDK provides a concise async server framework with type hints. Faster to prototype, easier to extend.

## 4. Two-layer architecture (client + server)
- **Chosen:** Separate `OpenFDAClient` class (data access) from `server.py` (MCP tool definitions).  
- **Rejected:** Monolithic file mixing API calls and tool handlers (tight coupling, harder to test).  
- **Why:** The client can be unit-tested with a mock HTTP transport; the server can be tested independently. Any tool can be added/modified without touching API logic.

## 5. STDIO transport (not SSE/WebSocket)
- **Chosen:** Standard stdio MCP transport.  
- **Rejected:** SSE-based server (requires an HTTP server + port, more complex deployment).  
- **Why:** STDIO is the canonical MCP transport — every MCP client supports it. The server starts when the client spawns it and stops when done. No port conflicts, no daemon management.

## 6. Markdown-formatted tool outputs
- **Chosen:** Each tool returns a Markdown string with headings, bold labels, and emoji icons.  
- **Rejected:** Raw JSON (unreadable in chat), plain text (hard to scan).  
- **Why:** The tools are consumed by LLMs that render Markdown well. Structured formatting makes the output skimmable for both the model and any human reviewing it.

## 7. Enriched result fields (`_brand_name`, `_warnings`, etc.)
- **Chosen:** The client flattens nested `openfda` dicts and rarely-nested label fields into top-level `_prefixed` keys.  
- **Rejected:** Returning raw OpenFDA JSON (deeply nested `patient.drug.medicinalproduct` paths), expecting every tool handler to navigate the schema.  
- **Why:** The enrichment step normalises the API's idiosyncratic field naming. Each tool handler just calls `_format_result()` without needing to know whether a field lives under `results[i].openfda.brand_name[0]` or `results[i].brand_name`.

## 8. Pagination via skip/limit
- **Chosen:** OpenFDA's native `skip` + `limit` parameters exposed through `browse_drugs(page, limit)`.  
- **Rejected:** Cursor-based pagination (not supported by OpenFDA), rolling our own offset tracking.  
- **Why:** OpenFDA returns `total` in every response, so calculating pages is trivial. Users can move forward/backward without tracking opaque cursors.

## 9. max 100 results per page
- **Chosen:** Hard-capped at `MAX_PAGE_SIZE = 100`.  
- **Rejected:** Unlimited limit (risks huge responses and LLM context overflow).  
- **Why:** OpenFDA itself limits to 100 per query. Our cap matches theirs and keeps tool responses LLM-friendly.

## 10. Async MCP server (anyio)
- **Chosen:** Async `server.py` using `anyio.run(main())`.  
- **Rejected:** Sync HTTP calls with requests library (blocks the async event loop).  
- **Why:** The MCP Python SDK runs an async loop; blocking calls would stall the server. `httpx` supports both sync and async — we use the sync client for simplicity but could migrate to `AsyncClient` if concurrency becomes an issue.

## 11. Five tools, focused surface
- **Chosen:** `search_drug`, `check_adverse_events`, `find_generic_alternatives`, `ndc_lookup`, `browse_drugs`.  
- **Rejected:** Single monolithic `query_drug` tool (too many responsibilities), adding dosage/administration parsing (overengineered — free-text field).  
- **Why:** Each tool maps to a distinct user need. A user asking "is this drug safe with my other meds?" should call `search_drug` for label warnings; someone who got a new prescription should `check_adverse_events`. Separation makes the LLM's intent routing straightforward.

## 12. No write operations
- **Chosen:** Read-only MCP agent.  
- **Rejected:** Add note-taking, report-saving, or alerting capabilities.  
- **Why:** OpenFDA is a read-only API; there's nothing to write. Adding local storage would bloat the agent without clear benefit. Read-only also means no approval gates needed — simpler and safer.

## 13. Slow test marker for live API tests
- **Chosen:** Live integration tests tagged `@pytest.mark.slow`, excluded from default runs.  
- **Rejected:** Mocking every API call (false confidence), skipping integration tests entirely (miss regression).  
- **Why:** Unit tests with mocked HTTP cover routing and formatting. Slow tests run against real OpenFDA to catch API changes. CI runs `pytest -m "not slow"` by default; nightly runs include slow tests.

## 14. User-Agent header
- **Chosen:** `MediMate-MCP/0.1` as the User-Agent.  
- **Rejected:** Default httpx User-Agent (impersonal, could be blocked), no User-Agent (rude).  
- **Why:** OpenFDA request logs identify traffic by User-Agent. A meaningful name helps them contact us if needed and signals legitimate use.

## 15. Error handling: exceptions surface as tool error text
- **Chosen:** The `call_tool` handler catches all exceptions and returns them as `TextContent`.  
- **Rejected:** Letting exceptions propagate to the MCP framework (cryptic stack traces), returning empty results with no explanation (confusing).  
- **Why:** The user sees a clear error message in the chat rather than a failed tool invocation. Network issues, API changes, and timeouts all become understandable "❌ Error: ..." messages.