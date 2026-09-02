# Decisions — WHY every architectural choice

## 1. MCP over standalone CLI

**Decision:** Implement as an MCP server (`mcp.server.fastmcp.FastMCP`) with a parallel CLI (`main.py`) for testing.

**Why:** The brief explicitly calls for "an MCP server that exposes tools for an AI agent." The MCP protocol is the standard for AI-agent tool exposure — any MCP-compatible client (Claude Desktop, Cursor, custom agents) can directly call `scan_statements`, `detect_recurring`, etc. The CLI exists purely for development, debugging, and CI smoke tests.

**Trade-off accepted:** Slightly more code (server.py wraps the same business logic twice — once as MCP tools, once as CLI commands). Worth it because the MCP interface is the product; the CLI is a validation harness.

## 2. FastMCP (FastAPI under the hood)

**Decision:** Use `mcp.server.fastmcp.FastMCP` instead of the low-level MCP SDK or a raw FastAPI server.

**Why:** FastMCP provides:
- Decorator-based tool registration (`@mcp.tool()`) — clean, minimal boilerplate
- FastAPI-backed SSE transport for HTTP-based clients
- stdio transport for CLI-based clients (Claude Desktop)
- Built-in schema generation and argument validation

The low-level SDK would require manual JSON-RPC handling. A raw FastAPI server would mean reimplementing MCP protocol. FastMCP is the right level of abstraction — proven, boring, well maintained.

**Trade-off accepted:** FastMCP is newer than the low-level SDK. If it has edge cases, we can drop to the low-level SDK. For v1 the abstraction saves significant code.

## 3. Merchant-database approach

**Decision:** Hard-code a dictionary of 25+ known subscription services with cancellation URLs, typical pricing, and aliases.

**Why:** A web-scraping approach would require:
- Maintaining scrapers that break as sites change
- API keys for every service
- Handling rate limits and CAPTCHAs
- Unpredictable runtime (seconds to minutes per service)

A static curated database covers the long tail of common subscriptions (Spotify, Netflix, etc.) with zero runtime cost. AI agents can still handle unknown merchants via heuristics (amount + frequency pattern).

**Trade-off accepted:** Unknown merchants won't have cancellation URLs. The user is prompted to suggest additions to the database.

## 4. Simulated bank data, not live bank/email integration

**Decision:** Parse CSV exports (bank statement CSVs and email CSVs) rather than connecting to bank APIs or live IMAP.

**Why:**
- Live bank/email integration requires OAuth flows, API keys, and security reviews
- Most users can export a CSV from their bank or email provider in 30 seconds
- CSV parsing is deterministic — no API failures, rate limits, or auth issues
- The tool is useful immediately, without any setup beyond providing a file path
- Future: IMAP scanning can be added as an optional module when the user provides credentials

**Trade-off accepted:** Requires the user to manually export CSV. This is a classic v1 trade-off — delivered working today vs waiting for perfect integration.

## 5. Tool design: pass data as JSON strings between tools

**Decision:** MCP tools accept and return JSON strings (serialized by the agent), rather than sharing state or using files.

**Why:** MCP protocol uses JSON-RPC. Each tool call is stateless — the agent passes the result of `scan_statements` into `detect_recurring`, etc. This is the natural air-gap in the protocol. JSON strings are self-describing, debuggable, and don't require mutable server state.

**Trade-off accepted:** The agent's context carries intermediate data. This is fine — the agent already has the bandwidth, and the data is small (a user's transaction history is typically <50KB as JSON).

## 6. Recurring detection: simple heuristic (2+ occurrences)

**Decision:** A charge is recurring if the same merchant/appears 2+ times in the statement.

**Why:** The date range of a bank statement CSV is typically 1-3 months. If the same merchant appears twice in that window, it's almost certainly recurring. More sophisticated detection (exact interval matching, fuzzy description matching) adds complexity and edge cases for marginal gain in the v1.

**Trade-off accepted:** A charge that happens annually won't be detected as recurring from a 1-month statement. Adding historical data or explicitly asking the user addresses this case.

## 7. Categorization: merchant-DB-first, heuristics-fallback

**Decision:** Assign category from the merchant database when available. Unknown merchants get `Category.OTHER`.

**Why:** The merchant DB covers the long tail. For unknown merchants, guessing category from description text would require NLP and produce unreliable results. Better to label as "other" and let the agent or user re-categorize.

**Trade-off accepted:** Some known merchants might be in the wrong category. Corrections are simple PRs to merchant_db.py.

## 8. Pydantic models for all data

**Decision:** Use Pydantic v2 models for Charge, Subscription, CategorizedSub, etc.

**Why:** Pydantic provides validation, serialization, and clear schema definitions. The MCP SDK uses Pydantic for tool input/output validation. Keeping models in Pydantic means zero impedance mismatch between the business logic and the MCP layer.

**Trade-off accepted:** Pydantic adds a dependency. It's already required by the MCP SDK and FastAPI, so the cost is zero in practice.

## 9. Thin slice: no persistent state, no database

**Decision:** The server is stateless — no database, no user accounts, no session storage.

**Why:** The use case is "scan my statement, tell me what I'm paying for, help me cancel." This is a session-based interaction — the agent calls tools, gets results, and presents them. Persistent state would require authentication, data privacy considerations, and ongoing infrastructure.

**Trade-off accepted:** The agent must hold intermediate data across tool calls. This is standard MCP protocol behavior.

## 10. Frequency detection: interval averaging

**Decision:** Detect billing frequency by averaging intervals between occurrences of the same merchant.

**Why:** Simple, explainable, and works on 2+ datapoints. Monthly = ~28-35 day gaps. Yearly = ~365. Weekly = ~7. No ML needed.

**Trade-off accepted:** Edge cases (irregular billing, skipped months) can misclassify. The agent can override if needed.