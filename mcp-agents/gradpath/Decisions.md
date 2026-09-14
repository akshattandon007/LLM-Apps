# Decisions — Every architectural choice and why

## ⚡ Why MCP over a web app?

**Decision:** Model Context Protocol (MCP) server instead of a standalone web
application.

**Why:** Families researching colleges are already in conversational AI
interfaces (Claude Desktop, Cursor, etc.). MCP lets them ask "What can we
afford in California?" directly in their existing chat flow — no new app to
learn, no browser tabs for each college. The server exposes tools that any
MCP host can call, making the data available wherever the family already
works.

The secondary FastAPI/uvicorn wrapper (main.py --http) exists for testing and
for non-MCP HTTP clients, but the primary delivery mechanism is MCP.

## ⚡ Why the College Scorecard API (data.gov)?

**Decision:** [College Scorecard](https://collegescorecard.ed.gov/data/) as
the single data source.

**Why:** It's the most comprehensive free source of US college data:
- 6,300+ institutions
- Net price, tuition, graduation rates, post-grad earnings
- SAT/ACT scores, enrollment, demographics
- Official government data, updated annually
- Free API key from api.data.gov

Alternatives considered and rejected:
- **IPEDS** — most detailed but no public API, data is CSV downloads only
- **PayScale/Celebrity** — earnings by major but paid, no cost data
- **Niche/CollegeBoard** — scraper-hostile, no public API, terms-of-service risk
- **Scraping individual college sites** — fragile, slow, 6,300× more work

## ⚡ Why simulated mode + live mode?

**Decision:** The API client auto-detects whether to use live or simulated
data based on the presence of `COLLEGE_SCORECARD_API_KEY`.

**Why:** Two reasons:
1. **Zero-friction onboarding** — clone, pip install, pytest, everything
   works. No API key hunting for development.
2. **Deterministic tests** — smoke tests always pass because they run against
   the same 8 sample colleges, not a live API that could rate-limit or return
   slightly different results.

Sample data includes 8 colleges spanning community college, public
universities, private liberal arts, and a technical institute — enough to
demonstrate all four MCP tools meaningfully.

## ⚡ Why httpx over requests?

**Decision:** `httpx` for all API calls.

**Why:** Async. The MCP tool functions are async by nature (FastMCP supports
async tools), so the HTTP client needs to be async too. `httpx` provides
identical API surface to `requests` but with `async with` support. No need
for thread pools or event loop coordination.

## ⚡ Why the mcp library (pinned <2.0.0)?

**Decision:** `mcp>=1.0.0,<2.0.0` from PyPI.

**Why:** The official Python MCP SDK. `FastMCP` provides the cleanest
decorator-based API for defining tools. Pinning below 2.0.0 avoids
potential breaking changes while the MCP protocol is still evolving.

## ⚡ Why FastAPI + uvicorn as secondary transport?

**Decision:** FastAPI/uvicorn additionally available for SSE transport.

**Why:** While stdio MCP is the primary mode (for desktop MCP hosts), the SSE
transport enables:
- Remote MCP clients connecting over HTTP
- Cloud deployments (Fly.io, Railway)
- Health checks and monitoring
- Testing with curl

## ⚡ Why four separate modules (searcher, profile, comparer, earnings)?

**Decision:** One file per tool operation, all thin wrappers calling the
scorecard client.

**Why:** Each tool has distinct formatting and logic. Splitting them keeps each
file under ~100 lines, easy to test individually, and easy to change the
output format of one tool without touching the others. The scorecard client
is the shared dependency.

## ⚡ What we're NOT doing (future scope pushed out)

- **Program-level earnings** — Scorecard API v1 only provides institution-level
  median earnings. Program-level data requires a separate API (or IPEDS
  download). We show overall earnings with a caveat.
- **Caching/offline mode** — not needed for v1; 6,300 schools is small enough
  that API calls are fast.
- **Degree maps / 4-year plans** — v1 is search-and-compare only.
- **Financial aid estimator** — net price from Scorecard is sufficient for v1.
- **User accounts / saved lists** — pure query-response is the v1 model.
- **Geographic maps** — text-based output keeps it simple and MCP-friendly.