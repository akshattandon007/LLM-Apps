# Decisions — MarketFinder Architecture

## 1. MCP v1 SDK (mcp[cli] < 2.0)

**Decision:** Pin `mcp[cli]>=1.0.0,<2.0.0` in requirements.

**Rationale:** The `FastMCP` constructor signature changed between v1 and v2. The `instructions` parameter on `FastMCP(...)` is v1-only. Pinning avoids silent breakage when a newer major ships.

**Rejected:** No pin — would risk the server failing to import after a `pip install` later.

---

## 2. FastMCP over Low-Level Server

**Decision:** Use `mcp.server.fastmcp.FastMCP` instead of the lower-level `mcp.server.Server`.

**Rationale:** `FastMCP` provides the `@mcp.tool()` decorator pattern that keeps tool definitions minimal, auto-generates schemas from type hints, and handles JSON-RPC plumbing. Faster to build, easier to read.

**Rejected:** Raw `Server` with manual `@server.list_tools()` / `@server.call_tool()` handlers — more boilerplate, no schema inference.

---

## 3. One Tool Per Operation

**Decision:** Four separate tools (`find_markets`, `filter_by_program`, `get_market_details`, `find_csa`) instead of one "universal" tool with branching parameters.

**Rationale:** Each tool has a focused contract with specific parameters and return types. AI clients can discover and invoke them independently. Tool descriptions stay short.

**Rejected:** `search_markets(zip, radius, program, market_id, mode)` — forces the client to know internal mode flags. Reduces discoverability.

---

## 4. set_client() Dependency Injection

**Decision:** Module-level `_client` variable with `get_client()` / `set_client()` accessors in `api.py`.

**Rationale:** Tests need to swap `httpx.Client` for a mock without touching module imports or environment variables. The setter/getter pattern is explicit, zero-config, and works with any httpx mock transport.

**Rejected:** Patching `httpx.Client` in tests with `unittest.mock.patch` — fragile if the import path changes. Relying on environment variables (`$USDA_API_BASE`) — over-engineered for a zero-auth API.

---

## 5. Simulated Fallback (Always Demoable)

**Decision:** If any API call raises an exception (timeout, HTTP error, parse error), return hardcoded simulated data for Portland, OR.

**Rationale:** The server must always respond with something useful — an agent that gets an empty error on every call is useless. Portland-area data is generic enough that any human recognizes it as realistic.

**Rejected:** Returning an error message string — breaks the structured return contract. Raising the exception to the MCP layer — clients can't recover. Empty results — useless for demos.

---

## 6. Pydantic Models for All Return Types

**Decision:** Every API function returns a typed Pydantic model (`MarketSearchResult`, `MarketDetails`, `CSASearchResult`) rather than raw dicts or strings.

**Rationale:** AI agents can iterate on structured fields. Type hints enable auto-complete in editors. Pydantic validation catches malformed API responses early.

**Rejected:** Raw `dict` returns — no validation, no schema, agents guess field names. Named tuples — no JSON schema generation for tool descriptions.

---

## 7. ZIP-Based Geocoding (No External Service)

**Decision:** Pass the user's ZIP code directly to the USDA API as the `zip` query parameter. No geocoding step.

**Rationale:** The USDA API accepts ZIP codes natively and returns results with distance estimates. Adding a geocoding service (Google Maps, OpenStreetMap) adds an API key requirement and a failure point for no benefit.

**Rejected:** Requiring lat/lng input — forces the user or agent to geocode separately. Integrating `geopy` — extra dependency, USDA already handles it.

---

## 8. Markdown-Formatted Tool Output

**Decision:** Tools return Markdown strings (headings, bold, emoji icons) rather than raw JSON or Pydantic JSON.

**Rationale:** MCP tool outputs are typically rendered in chat UIs. Markdown is human-readable in a chat window but still parsable by LLMs. The raw Pydantic models remain available for programmatic use by the agent via `result.markets[0].market_name`.

**Rejected:** Returning JSON — ugly in chat, needs parsing before display. Returning plain text — no visual structure.

---

## 9. httpx Over requests / aiohttp

**Decision:** Use `httpx.Client` (synchronous) for API calls.

**Rationale:** httpx is the modern stdlib-style HTTP client. It's synchronous by default (simpler for MCP tools run by the agent), supports mock transports natively, and has broader Python version support than `requests`.

**Rejected:** `requests` — stable but no native mock transport. `aiohttp` — async adds complexity; MCP v1's tool interface is synchronous.

---

## 10. tests/ Outside Package

**Decision:** Place `tests/test_marketfinder.py` at the repo root level, not inside `marketfinder/`.

**Rationale:** Standard Python project layout. Keeps distribution packages clean. pytest auto-discovers `tests/` without `__init__.py`.

**Rejected:** Inline tests in `marketfinder/tests/` — forces test code into the installable package.

---

## 11. No `__init__.py` in tests/

**Decision:** `tests/` has no `__init__.py`. pytest finds tests via path-based discovery.

**Rationale:** python 3.3+ namespace packages and pytest work without it. One less file.

**Rejected:** Adding `__init__.py` — no benefit, extra file to maintain.

---

## 12. Program as a Pydantic Enum

**Decision:** `Program` is a `str, Enum` subclass with values `SNAP`, `WIC`, `WICcash`, `SFMNP`, `all`.

**Rationale:** Validates filter inputs at the API boundary. Self-documenting. Compatible with Pydantic's schema generation and OpenAPI-like descriptions.

**Rejected:** Plain strings with runtime validation — no schema, no IDE autocomplete, possible typo bugs.

---

## 13. Single `_parse_float()` Helper

**Decision:** One reusable `_parse_float()` that returns `None` for bad values instead of crashing or using sentinels.

**Rationale:** The USDA API occasionally returns empty strings or null for lat/lng fields. A single helper keeps parsing consistent across all model types.

**Rejected:** `float(x) or 0.0` — masks missing data. Per-field try/except blocks — duplicated everywhere.

---

## 14. Portland-Focused Simulated Data

**Decision:** The simulated market set covers 5 Portland-area markets with varied SNAP/WIC acceptance profiles, plus 3 CSAs.

**Rationale:** A single realistic city gives the demo coherence — the same markets appear across all tools. Mixed acceptance profiles exercise all filter paths.

**Rejected:** Generic "Market A, Market B" data — no character, unrealistic. Random US zip codes — confusing without geographic grounding.

---

## 15. `market_link` in Details Only

**Decision:** The `market_link` field appears only on `MarketDetails` (the get-by-id response), not on `Market` (the search response).

**Rationale:** The USDA API returns `market_link` only in the individual detail endpoint. The search-by-zip endpoint doesn't include it. Modeling this accurately avoids confusion.

**Rejected:** Adding `market_link: Optional[str] = None` to `Market` — implies the field should be populated, which it never is in search results. Omitting it entirely from the models — loses a useful field.