# Decisions.md — MealWizard architecture rationale

## Why an MCP server, not a web app?
The user needs to ask "what can I make with what I have?" from wherever they
are — a CLI, a chat app (Telegram/Discord/Slack), or an AI agent workflow.
Building a standalone web app would lock the tool into a browser and require
hosting a full frontend. An MCP server decouples the recipe logic from the
presentation layer: any MCP client (Claude Desktop, Hermes, Cursor, custom
scripts) can plug into it via stdio or HTTP. It's the smallest unit that
solves the problem for the widest range of callers.

## Why TheMealDB?
Zero-auth, free, RESTful, no rate limit drama at practical request volumes.
Returns structured JSON with exactly the fields we need (ingredients, measures,
instructions, category, area, image). Alternatives like Spoonacular require API
keys and paid tiers for the same data. TheMealDB's coverage (~300+ recipes) is
modest but enough for a v1 — the user gets working results on day one. The
abstraction in `src/mealdb.py` makes swapping to another provider a single-file
change.

## Why static substitution + seasonal data instead of another API?
Ingredient substitutions and seasonal produce are stable knowledge — butter
always substitutes with oil, strawberries are always in season in June in the
US. Hitting an API for this adds latency, network dependency, and auth overhead
for data that doesn't change. A curated static table (~24 ingredients, 12
months x 3 regions) is faster, more reliable, and trivially extensible. When
you need a swap, you get it in microseconds, not 200ms + API call.

## Why MCP SDK (mcp library) instead of rolling raw FastAPI?
The `mcp` library handles the protocol plumbing — tool registration, input
validation, transport negotiation (stdio vs. SSE), and response formatting.
Rolling this manually would mean reimplementing the MCP spec. The library is
well-maintained and used by the community. We pin <2.0.0 to avoid breaking
changes until the SDK stabilises.

## Why httpx over requests?
httpx has a native async API (relevant for future parallelism if we batch API
calls) and modern HTTP/2 support. For a library that makes ~10 requests per
tool invocation, httpx's connection pooling and timeouts are cleaner than
requests. Both work; httpx is the pragmatic default for new Python projects
in 2024+.

## Why FastAPI + uvicorn as the HTTP transport?
MCP servers can run over stdio (for desktop/local clients) or SSE (for remote
clients). FastAPI/uvicorn provides the SSE transport path, which is useful
when the server runs on a VPS and clients connect remotely. The MCP package
handles the protocol layer; FastAPI just serves it. This is the standard
stack for MCP-over-HTTP.

## Architecture: module-per-capability, not monolithic
- `src/mealdb.py` — single responsibility: talk to TheMealDB
- `src/recipes.py` — find, filter, and format recipes
- `src/substitutes.py` — ingredient swap logic + static table
- `src/mealplanner.py` — meal plan generation
- `src/season.py` — seasonal produce lookup + static table
- `src/scaler.py` — serving scaling logic
- `src/models.py` — shared Pydantic schemas
- `server.py` — MCP glue (tools -> handlers -> domain modules)

Each module is testable in isolation. Swapping TheMealDB for another provider
touches exactly one file. Adding a new MCP tool is one handler + one schema.

## Why Pydantic v2?
Type-safe model validation, alias support (TheMealDB's `strMeal` -> `name`),
and serialisation for downstream use. Pydantic v2 is the standard for modern
Python API work and is already installed by the MCP SDK.

## Why 6 MCP tools, not more?
These 6 cover the full user story from "what's for dinner?" to "I have these
ingredients" to "I'm out of something" to "what's in season?" to "how much
do I need for 6 people?". Adding more tools before shipping v1 would violate
the thin-slice principle. Each tool has a clear, single purpose.

## Decisions Summary Table

| Decision | Choice | Rationale |
|---|---|---|
| Architecture | MCP server | Client-agnostic, works with any MCP host |
| Recipe API | TheMealDB | Free, zero-auth, structured JSON |
| Substitutions | Static table | Fast, reliable, no network dependency |
| Seasonal data | Static table | Stable knowledge, no API needed |
| HTTP client | httpx | Async-capable, modern, good defaults |
| Transport | FastAPI/uvicorn (SSE) + stdio | Supports remote and local clients |
| Models | Pydantic v2 | Validation, aliases, ecosystem standard |
| Module layout | Per-capability modules | Testable in isolation, one-change swaps |
| Tool count | 6 | Covers full user story without over-scoping |