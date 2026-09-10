# Decisions.md — WHY Behind Every Choice

## Why an MCP server instead of a web app?

Career answers are consumed by AI agents, not humans browsing a dashboard. An MCP server lets an agent call `salary_by_role()` the same way it calls a Python function — no UI, no API key management for the end user. The agent handles the conversation; Career Compass handles the data.

## Why BLS data instead of scraping job boards?

BLS data is:
- **Authoritative**: government-collected, audited, publicly available
- **Structured**: SOC codes, wage percentiles, growth projections — all machine-readable
- **Free**: no API rate limits for research use
- **Consistent**: every occupation uses the same methodology

Job boards (Indeed, Glassdoor, LinkedIn) have self-selection bias (only people who took the survey speak), inconsistent job titles, and opaque aggregation. BLS data gives you the ground truth.

## Simulated vs live data

Two modes:
1. **Database (default)**: ~25 occupations seeded from BLS OEWS 2023 + projections 2022-2032. Always works, no API key needed. Every tool returns instantly.
2. **Live**: when `BLS_API_KEY` is set, salary data is fetched live from the BLS Public API v2. Falls back to database on failure.

The `data_source` field on every result tells the consumer which mode was used.

## Why these 6 tools?

Each covers a distinct career decision:

| Decision | Tool |
|---|---|
| "What does this job pay?" | `salary_by_role` |
| "Where should I work?" | `growing_industries` |
| "What do I need to learn?" | `skills_gap` |
| "Where will I be in 5 years?" | `career_path` |
| "Should I take this offer?" | `compare_offer` |
| "Is this job growing or dying?" | `job_outlook` |

These six cover 90%+ of career questions a knowledge worker asks.

## Why the directory structure?

`src/` vs flat files keeps the service layer importable and testable without mucking around with `sys.path` hacks. `tests/` mirrors `src/` for discoverability. `server.py` and `main.py` sit at the root because they're entry points — they consume the `src.` package, not the other way around.

## Why FastAPI + uvicorn?

MCP SDK 1.x ships with a FastMCP class that provides an SSE transport (`sse_app()`). FastAPI + uvicorn gives us a production-grade HTTP server to host that transport with health checks and minimal ceremony. No Flask, no Django — just what's needed.

## Why mcp < 2.0.0?

The MCP SDK 2.x has breaking changes. Pinning < 2.0.0 keeps the dependency stable. The pin is explicit in requirements.txt so there's no ambiguity.

## Why not use httpx for all data sources?

httpx is used for the BLS API call. All other data is local — no external HTTP dependencies for the core tools themselves.

## Skills gap data strategy

Skills maps are curated for common transitions (support → developer, analyst → data scientist, etc.). For less common transitions, a generic gap analysis generates education level and industry-knowledge recommendations. This gives good answers for the 80% case without maintaining an impossible mapping table.

## Cost-of-living approach

ZIP-code level data from C2ER (Council for Community & Economic Research). 25 representative ZIP codes covering major metro areas. Missing ZIP codes fall back to the 2-digit prefix or national average (100). This is granular enough for any MCP consumer to give useful answers without maintaining a 40,000-row database.