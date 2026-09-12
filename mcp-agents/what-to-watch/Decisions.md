# Decisions — WHY every architectural choice

## Why MCP server instead of a standalone web app

WhatToWatch is designed as a tool for LLM agents and MCP hosts (Claude Desktop, Cline, etc.), not as a consumer web app. MCP lets AI assistants call the TV schedule as a native tool — no REST endpoints to hit, no auth to configure. The MCP stdio transport means zero deployment overhead: run the process, pipe it to the host, done.

If we ever need a web frontend, FastAPI is already in the stack from server.py's deps, so adding a `/docs` endpoint would be a small PR.

## Why TVMaze API

TVMaze is the largest free, zero-auth TV schedule API available. 60K+ shows, global schedule data by country, full episode listings, and reliable uptime. No rate limiting under reasonable use, no OAuth, no API key management. Alternatives (TheTVDB, TMDB) require registration, rate limits, or paid tiers for schedule data.

The trade-off: TVMaze has no streaming-availability data (Netflix/Prime/etc.). For v1 that's fine — we tell you what's ON, not where to WATCH it. Streaming metadata can be added later via a secondary provider.

## Why simulated mock data for tests

TVMaze data changes daily (today's schedule today, tomorrow's tomorrow). Asserting against live data produces flaky tests. Instead, we use fixture JSON that mirrors TVMaze's real response shape. Tests verify:
- Pydantic parsing edge cases (null ratings, missing networks, empty genres)
- Formatting logic (genre grouping, rating display)
- Genre filtering (correct inclusion/exclusion)
- Similar-show scoring (genre overlap + rating proximity)

The single integration point (`TVMazeClient._get`) is thin enough that testing with mocks gives high confidence. Live smoke tests can be run manually via the CLI.

## Why httpx over requests

httpx is the modern HTTP library with a clean API, connection pooling, and the same interface for sync and async. Since TVMaze is a simple REST API with no async requirements for v1, we use the sync client. If we add async tool handlers later (MCP supports it), switching to httpx.AsyncClient is a one-line change.

## Why MagicMock over a real mock server

The test suite mocks `TVMazeClient` at the instance level rather than running a real HTTP mock server. This keeps tests fast (< 1s), avoids any network I/O, and lets us test every code path including error handling (client returning empty lists, None responses, etc.). The API client itself is a thin pass-through with no business logic — it doesn't benefit from integration testing.

## Why pin mcp < 2.0.0

The MCP Python SDK is evolving rapidly. Pinning below 2.0 avoids breaking changes from major version bumps while still allowing minor/patch updates. Once the SDK stabilizes, the pin can be relaxed.