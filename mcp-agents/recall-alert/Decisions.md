# Decisions — Recall Alert 🚨⚠️

## 1. MCP vs Standalone CLI

**Decision:** Build as an MCP server.
**Rejected:** Standalone CLI tool.
**Why:** The user's repo already has 25 MCP agents and the daily rota specifically targets MCP Agents. An MCP server integrates directly into any MCP-compatible AI agent, making it more useful as a tool than a standalone CLI. The user's pipeline targets MCP as the primary delivery format for this category.

## 2. FastMCP (v1 SDK) vs Raw stdio MCP

**Decision:** Use `FastMCP` from the `mcp` v1 SDK (`mcp<2`).
**Rejected:** Raw JSON-RPC over stdio, or the newer `MCPServer` from MCP v2.
**Why:** `FastMCP` provides clean decorator-based tool definitions with automatic JSON Schema generation from type hints — minimal boilerplate. MCP v2 (`MCPServer`) renamed the API and changed the constructor; pinning `mcp<2` avoids a moving target. No raw stdio needed when the SDK handles transport.

## 3. Data Sources — openFDA + NHTSA vs Others

**Decision:** openFDA for consumable products (food, drugs, devices) and NHTSA for vehicles.
**Rejected:** CPSC API (Consumer Product Safety Commission — less structured, returns HTML), single-source approach, paid recall APIs.
**Why:** openFDA provides a well-documented REST API (JSON) that covers the broadest range of everyday recalls — food, drugs, medical devices, cosmetics — with no API key required and 240 req/min. NHTSA covers vehicle safety by VIN, which is a completely different domain. Together they cover the two most common recall scenarios people face daily. CPSC lacks a free structured JSON API.

## 4. Python 3 vs Node.js / Go

**Decision:** Python 3.
**Rejected:** Node.js (TypeScript), Go.
**Why:** The `mcp` Python SDK is mature and well-documented. `httpx` provides first-class async HTTP with mock transport for hermetic testing. The project needs no Node.js ecosystem tools. Python is already installed on the target VPS.

## 5. httpx vs requests vs aiohttp

**Decision:** `httpx`.
**Rejected:** `requests` (synchronous only), `aiohttp` (heavier, less ergonomic).
**Why:** `httpx` supports both sync and async, has a clean API matching `requests`, and provides `MockTransport` for completely hermetic unit tests without network calls. No reason to add `aiohttp` when the current usage is synchronous.

## 6. Single-File vs Multi-Module Structure

**Decision:** Split into `recall_client.py` (API client) + `server.py` (MCP layer) + `test_recall_alert.py` (tests).
**Rejected:** All-in-one `server.py`, or fully separated `clients/fda.py`, `clients/nhtsa.py` hierarchy.
**Why:** Two modules keeps the separation of concerns clean without over-engineering. `recall_client.py` owns all HTTP and data parsing — testable independently. `server.py` owns only the MCP tool definitions and formatting. Full hierarchy (`clients/` package) adds unnecessary nesting for a 400-line project.

## 7. Data Provenance — `source` Field on RecallResult

**Decision:** Every `RecallResult` has a `source` field (`"openFDA"` or `"NHTSA"`).
**Rejected:** Omitting source (assumed from context), inferring from method name.
**Why:** The AI agent calling the tool needs to know where the recall data came from to judge its authority. Two data sources means explicit provenance is essential. The field is set at creation, not inferred.

## 8. MockTransport for Tests vs Real API Calls

**Decision:** Use `httpx.MockTransport` for all tests.
**Rejected:** Tests against real API endpoints (requires internet, rate-limited, slow, flaky).
**Why:** Hermetic tests are deterministic, fast, and work offline. `MockTransport` intercepts at the HTTP layer so the client code runs the full code path — no partial mocking. Real API tests would depend on network availability and rate limits, making them unreliable in CI.

## 9. VIN Validation at Client vs Server Layer

**Decision:** Validate VIN length (17 chars) at the client layer, surface as empty list.
**Rejected:** Validate at the server layer, surface as an error message.
**Why:** The client's `search_vehicle_recall` returns an empty list for invalid VINs, and the MCP tool `check_vehicle_recall` adds a user-facing error message ("Invalid VIN"). This keeps the client pure (no UI concerns) while the server handles user guidance. Separation of concerns.

## 10. Product Recall Output Format

**Decision:** Rich markdown with emoji indicators per recall result.
**Rejected:** Plain text, JSON output.
**Why:** MCP clients render tool outputs as text for the AI agent — markdown improves readability when surfaced to the end user. Emoji (⚠️, 📅, 🔧) provide quick visual scanning. The format is concatenated across multiple results with sections separated by `---`.

## 11. Error Handling Strategy

**Decision:** Catch HTTP errors at the MCP tool layer and return user-friendly error strings.
**Rejected:** Propagate raw exceptions to the AI agent, crash on API errors.
**Why:** API failures should not break the agent's conversation. A human-readable error message ("❌ Error searching FDA recalls: 500 Internal Server Error") is actionable — the agent can report it to the user. Raw exceptions would terminate the tool call.

## 12. Default Result Limit

**Decision:** Default `limit=10`, maximum `50`.
**Rejected:** Unlimited results, default 5.
**Why:** 10 results provides a good overview without flooding the agent's context. The 50 cap prevents abuse/excessive API calls. Users who want a quick check get 10; power users can request 50 explicitly.

## 13. Date Format Normalization

**Decision:** Convert openFDA's `YYYYMMDD` integer format to ISO `YYYY-MM-DD` strings.
**Rejected:** Leave as raw `20251101`, convert to human-readable like "Nov 1, 2025".
**Why:** ISO 8601 is parseable by both machines and humans, and works consistently across both data sources (NHTSA doesn't provide reliable recall dates via its current API, so we use today's date as fallback for NHTSA).

## 14. No API Keys Required

**Decision:** Both data sources work without any API key.
**Rejected:** Using APIs that require registration (Alpha Vantage, Nutritionix, etc.).
**Why:** Zero-friction setup is critical for a tool that people should just run. openFDA and NHTSA are US government APIs with generous or no rate limits and no registration. No `.env` file, no secrets management.
