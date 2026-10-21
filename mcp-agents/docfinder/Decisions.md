# Decisions — DocFinder

This file documents the architectural and design decisions made during the development of DocFinder, the MCP agent for healthcare provider search.

---

## 1. NPPES NPI Registry as data source (vs other provider databases)

**Chosen:** CMS NPPES NPI Registry API (`npiregistry.cms.hhs.gov`)

**Rejected alternatives:**
- **BetterDoctor API** — Requires API key with rate limits; free tier is very limited (50 calls/day). Not zero-auth.
- **OpenStreetMap/Nominatim** — Only finds physical locations, not licensed healthcare providers. No taxonomy/specialty data.
- **Healthgrades / Vitals / Zocdoc** — No public API. Scraping would be brittle and violate ToS.
- **Scraping state medical boards** — 50 different websites, each with different formats. Not buildable in a session.

**Why:** NPPES is the official US government provider registry, free, zero-auth, returns structured JSON, and covers every provider who bills Medicare/Medicaid (~10M records). It's the canonical source.

---

## 2. MCP protocol (vs direct CLI / web app)

**Chosen:** MCP server (Model Context Protocol over stdio)

**Rejected alternatives:**
- **CLI tool** (`docfinder --specialty dentist --city Chicago`) — Easy to build but not composable. Can't be used inside an AI conversation.
- **FastAPI web app** — Overkill for a data-lookup tool. Requires hosting, auth, uptime management.
- **Python library only** — Useful for developers but not end-users.

**Why:** MCP is the standard for LLM tool integration. An MCP server works with any MCP client (Claude Desktop, Cursor, custom agents), and the user's ecosystem is already MCP-native (RecallGuard, Inbox Commander, etc. follow this pattern).

---

## 3. Python MCP SDK (vs building from scratch)

**Chosen:** `mcp` PyPI package (v2.3+ with `Server.add_request_handler`)

**Rejected alternatives:**
- **Custom stdio protocol implementation** — Would match the MCP spec exactly but adds weeks of work. No benefit over the SDK.
- **Older MCP SDK (v1.x with decorators)** — Less code but uses a deprecated API pattern. The v2.3 API is cleaner and future-proof.

**Why:** The official SDK handles protocol framing, JSON-RPC, capability negotiation, and error handling. Using `add_request_handler` (the v2.3 pattern) is more explicit about the handler lifecycle than the old decorator approach.

---

## 4. `httpx` over `requests` for API client

**Chosen:** `httpx` (async-ready, connection pooling, HTTP/2)

**Rejected alternatives:**
- **`requests`** — Sync-only, no HTTP/2, would need `requests-futures` for async.
- **`aiohttp`** — More complex setup, needs nested event loops in sync contexts.
- **`urllib`** — Too low-level; no connection pooling.

**Why:** `httpx` provides an `httpx.Client()` with built-in connection pooling and timeout management, works in both sync and async contexts, and is already used in the project's other MCP agents (RecallGuard).

---

## 5. Single NppesClient class (vs multiple service-specific clients)

**Chosen:** One `NppesClient` class with multiple methods

**Rejected alternatives:**
- **Separate clients for search vs details** — The NPPES API is a single endpoint with different query parameters. Splitting would duplicate the base URL, client initialization, and error handling.
- **Function-based module** — No connection reuse. Every call creates a new HTTP session.

**Why:** A single client class shares the `httpx.Client` connection pool, provides a clean API surface, and makes resource cleanup explicit with `close()`.

---

## 6. Thread-safe sync client (vs full async HTTP)

**Chosen:** Sync `httpx.Client()` wrapped in sync methods

**Rejected alternatives:**
- **Full async with `httpx.AsyncClient`** — The MCP server runs in async context, but the NPPES API calls are I/O-bound and fast (<200ms). Making them async adds complexity (event loop management) with negligible performance gain for a lookup service.
- **Cached responses** — Provider data changes infrequently (updates take days/weeks). Cache would need invalidation logic that's out of scope.

**Why:** Sync code is simpler, easier to test, and for 5-10 fast API calls per request, the latency difference is imperceptible. If performance becomes an issue, converting to async is straightforward since the API surface is already clean.

---

## 7. Provider model with typed dataclasses (vs raw dicts)

**Chosen:** `Provider`, `ProviderAddress`, `ProviderTaxonomy` dataclasses with `from_api` factory

**Rejected alternatives:**
- **Raw dicts throughout** — Brittle. Every consumer must know the API's camelCase field names and nested structure.
- **Pydantic models** — Adds a dependency just for validation. The API output is well-structured; type-checked dataclasses are sufficient.
- **Protobuf/Thrift** — Completely wrong tool. Over-engineered for a data transform layer.

**Why:** Dataclasses provide self-documenting types, IDE autocompletion, and a clear boundary between the API's messy format and the server's clean interface. The `from_api` factory method isolates API format changes to one place.

---

## 8. Taxonomy search by description (vs taxonomy code)

**Chosen:** `taxonomy_description` free-text search (default), `taxonomy_code` exact match as optional

**Rejected alternatives:**
- **Taxonomy code search only** — Codes are 10-character alphanumeric (e.g. `1223G0001X`). No user knows these.
- **Hardcoded taxonomy-to-description mapping** — 2,000+ taxonomy codes. Maintaining a full map is scope creep.

**Why:** The NPPES API supports fuzzy text search on taxonomy descriptions. "Dentist" matches dentists, "cardiology" matches cardiologists. Users can type natural terms. The `taxonomy_code` parameter is still available if someone knows the exact code.

---

## 9. `postal_code` field for ZIP search (not `zip`)

**Chosen:** The NPPES API parameter is `postal_code` (not `zip`)

**Rejected alternatives:**
- Using the ambiguous `zip` parameter — The API also accepts `zip` but with different matching behavior.
- Doing client-side geocoding — Adds latency and dependency on a geocoding API.

**Why:** `postal_code` is the documented field name in the NPPES API. Using the correct field name ensures the API handles the search as intended. Verified via direct API testing.

---

## 10. Individual vs organization provider display

**Chosen:** `display_name` property that handles both types

**Rejected alternatives:**
- Always show `authorized_official_name` — Doesn't make sense for individual practitioners.
- Always show `first_name last_name` — Fails for organizations that have no individual names.

**Why:** NPI-1 (individual) providers have `first_name`/`last_name`; NPI-2 (organization) providers have `organization_name`. The `display_name` property checks `enumeration_type` and shows the appropriate name, with credential suffix for individuals.

---

## 11. Test approach — mock API responses

**Chosen:** Mock the `httpx.Client` in unit tests; no live API calls

**Rejected alternatives:**
- **Live API integration tests** — Would fail offline and introduce flaky tests from API rate limits or downtime.
- **VCR.py cassette recording** — Adds a dependency; the mock is trivially simple since the API returns deterministic JSON.

**Why:** The NPPES API is a straightforward GET → JSON pipeline. Mocking the HTTP client lets us test all code paths including error handling, edge cases, and parsing without network dependency.

---

## 12. `_raw` data attachment for full reports

**Chosen:** Attach the raw API dict as `_raw` on each Provider instance

**Rejected alternatives:**
- Full denormalization of every API field into the Provider model — Most fields (medicare IDs, state license codes, NPWP numbers) are rarely needed. Denormalizing adds clutter.
- Separate API call for full details — The NPPES API returns the full record in every search result; a separate call for "details" would be redundant.

**Why:** `full_report()` needs access to identifiers (Medicare, Medicaid, commercial payer IDs) that aren't in the core dataclass. Attaching the raw dict as `_raw` is a lightweight escape hatch for the 5% use case without polluting the core model.

---

## 13. Error handling — Catch and format in server

**Chosen:** Centralized error handling in `_handle_call_tool`

**Rejected alternatives:**
- Try/catch in every handler — Duplicates error formatting code across 5 handlers.
- Let exceptions propagate to the MCP framework — The framework sends a generic error. Custom formatting helps the user understand what went wrong.

**Why:** A single try/except in the dispatch function catches both handler-specific errors (missing args, invalid NPI format) and unexpected exceptions (network timeouts, JSON parse errors) with consistent user-facing messages.

---

## 14. No authentication layer

**Chosen:** No auth — the NPPES API is public

**Rejected alternatives:**
- Configurable API key — Would add complexity with no benefit since there's no key.
- Approval-gated writes — MCP has no write operations for this service. All tools are read-only.

**Why:** The NPPES API is a public government database with no authentication. Adding auth would be security theater.