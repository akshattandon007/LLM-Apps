# HomeFix — Architectural Decisions

## Why MCP over a Web App

**Decision**: Build as an MCP server (Model Context Protocol) rather than a web app.

**Why**: Home service discovery is an information-gathering and decision-making
problem — finding pros, comparing quotes, checking licenses, and booking. AI
agents (chatbots, copilots, assistants) are the natural interface for this:
users describe their problem in natural language, the agent calls tools to
research, and returns structured answers. A web app would require yet another
signup, yet another search UI, and users bouncing between tabs. MCP lets any
MCP-compatible AI agent (Claude Desktop, Copilot, custom agents) access HomeFix
as a toolset without building a custom UI per platform.

Trade-off: requires an MCP client. But the ecosystem is growing fast, and the
MCP server is a single ~300-line file that any agent can consume.

---

## Simulated License DB (Phase 1)

**Decision**: Use an in-memory mock database for license verification, reviews,
and professional data rather than integrating live APIs on day one.

**Why**: The brief calls for a working v1 today. Real license verification
requires negotiated API access with 50 state licensing boards (CSLB in CA,
NYCDCA in NY, etc.) — that's months of integration work and legal. A mock DB
lets us ship the tool contract and UX patterns immediately. The mock returns
realistic statuses (active/expired/suspended, valid/lapsed, bonded/not_bonded)
exercising all code paths.

When live APIs are wired up, the `check_license` function swaps the mock call
for the real HTTP client (httpx) without changing the tool interface.

---

## Tool Design per Service Type

**Decision**: Parameterize tools by `service_type` (enum) rather than exposing
one tool per type.

**Why**: 7 tools instead of 42 (6 service types × 7 tools). A single
`find_pros(service_type, zip_code)` is simpler for agents to discover and call
than `find_plumber(zip)`, `find_electrician(zip)`, etc. The service type enum
validates input at the Pydantic/MCP layer so agents get clear error messages
when they pass invalid types.

Trade-off: The agent must specify a service type. But service type is natural
user input ("my pipe burst" → plumber) that the LLM infers easily.

---

## In-Memory Booking (No Persistence)

**Decision**: Bookings are stored in a Python list, not a database.

**Why**: Phase 1 doesn't require cross-session persistence. Appointments are
generated and returned as confirmation strings. A real deployment would hook
into Calendly, ServiceTitan, or Google Calendar APIs. The in-memory store lets
us test the booking flow end-to-end without spinning up a Postgres instance.

---

## Regional Pricing via ZIP→State Mapping

**Decision**: Map ZIP codes to rough state regions using prefix ranges, then
apply state-level multipliers.

**Why**: Real estate and labor costs vary enormously by region (plumber in
Manhattan costs 2× a plumber in rural Texas). A full ZIP→metro lookup would
require a 40K+ row database. A simplified prefix→state mapping covers ~80% of
use cases with a ~20-line function. The data model supports swapping in a
proper geocoding service later.

---

## Reviews as Summaries, Not Raw Text

**Decision**: Return review sentiment summaries rather than streaming raw
review text.

**Why**: Raw reviews can be hundreds of paragraphs. An agent context window
fills fast. Summaries (3-4 sentences covering praise, complaints, and bottom
line) give the user what they need to decide in 1 second of reading. The LLM
calling the tool can always ask for more detail if needed.

---

## FastMCP over Raw MCP SDK

**Decision**: Use FastMCP (the high-level wrapper) rather than the low-level
`mcp.server.Server` class.

**Why**: FastMCP provides a `@server.tool()` decorator that auto-generates JSON
schemas from Python typehints and docstrings. No manual JSON-RPC dispatch, no
schema boilerplate. It's the recommended way to build MCP servers in Python.

---

## CLI for Testing Without an MCP Client

**Decision**: Ship `main.py` with subcommands that call the same business logic
functions as the MCP tools.

**Why**: Not every developer has an MCP client installed. A standard argparse
CLI means you can `python main.py find plumber 10001` and see results
immediately. The CLI and MCP server share the same `src/` modules, so tests
cover both paths simultaneously.

---

## .env.example Over .env

**Decision**: Commit `.env.example` with placeholders; never commit `.env`.

**Why**: API keys for license boards, review aggregators, and booking APIs will
be needed eventually. The `.gitignore` blocks `.env` from being committed. The
example file documents what keys are needed without exposing real credentials.