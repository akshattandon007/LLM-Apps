# Decisions.md — RecallGuard

## 1. Project: RecallGuard MCP Agent
**Decision**: Build an MCP agent that checks vehicle safety recalls via the NHTSA public API.
**Rejected**: Standalone web app (overkill for an AI-tool use case), CLI tool (not composable), or library-only (no AI interface). MCP was chosen because the AI assistant becomes the interface — the user asks in natural language and gets answers.

## 2. Use NHTSA Public API (Zero-Auth)
**Decision**: Use `api.nhtsa.gov` endpoints which require no API key, no registration, and no auth headers.
**Rejected**: Aftermarket APIs (require paid keys, rate-limited), web scraping NHTSA's site (fragile, slow). The NHTSA endpoints are documented at nhtsa.gov/datasets-and-apis, return clean JSON, and have permissive rate limits for individual vehicle lookups.
**Trade-off**: The NHTSA API has a bulk-VIN anti-abuse policy (HTTP 429 if you exceed rate limits). For single-vehicle lookups (the MCP use case), this is fine.

## 3. Python + MCP SDK over Alternative Stacks
**Decision**: Build in Python using `mcp` (the official Python MCP SDK) with `httpx` for async HTTP.
**Rejected**: Node/TypeScript MCP SDK (would fragment the LLM-Apps Python ecosystem), raw stdio protocol (redundant with the SDK), FastAPI SSE wrapper (MCP already defines the transport). Python keeps consistency with the existing repo.

## 4. Five Tools over Monolithic One
**Decision**: Expose 5 granular tools (`get_recall_years`, `get_recall_makes`, `get_recall_models`, `check_vehicle_recalls`, `get_recall_by_campaign`) instead of a single `do_everything` tool.
**Rejected**: Single tool with branching logic (bigger surface area, harder for AI to discover discovery endpoints). The discovery->select->check flow matches how users actually think: "Check my 2020 Toyota Corolla" → need to verify the make/model strings first.
**Trade-off**: More tool definitions, but each is focused and self-documenting.

## 5. Sync httpx.Client over Async
**Decision**: Use synchronous `httpx.Client` rather than `AsyncClient`.
**Rejected**: `asyncio` overhead for a stateless API wrapper with no concurrent streaming. The NHTSA responses are small JSON payloads that resolve in <500ms. Sync keeps the code simpler and avoids async propagation through the test suite.

## 6. Deduplicate API Results Client-Side
**Decision**: Deduplicate `get_makes` and `get_models` results in the client.
**Rejected**: Passing raw duplicates to the AI (confusing), or asking NHTSA to fix their data (not our problem). The API returns duplicate entries for vehicles that appear in multiple recall campaigns — deduplicating by name is the pragmatic fix.

## 7. Format Output as Readable Text, Not Raw JSON
**Decision**: All tools return formatted markdown text (headings, icons, structured fields) rather than raw API JSON.
**Rejected**: Returning raw JSON (requires the AI to reformat for the user — wasted tokens, worse UX). The formatted text is both human-readable and AI-readable.

## 8. Empty Results Return a Friendly Message, Not an Error
**Decision**: When no recalls are found, return "✅ No open recalls found" with an encouraging message.
**Rejected**: Raising an exception or returning empty JSON (confusing for non-technical users). "No news is good news" — the positive framing reassures the user.

## 9. RecallRecord as Dataclass over Dict
**Decision**: Model recall data as a typed `@dataclass` with a factory method and display methods.
**Rejected**: Raw dicts everywhere (no IDE support, fragile keys), Pydantic models (overkill for a simple data shape). The dataclass provides `.short_summary()` and `.full_report()` for clean formatting.

## 10. No Caching Layer
**Decision**: No in-memory or file-based caching for NHTSA responses.
**Rejected**: Redis/file cache (complexity for marginal gain). Recall data changes at most daily (manufacturers file new recalls), and each MCP call is a single HTTP request. If rate-limiting becomes an issue we can add a simple TTL cache later.

## 11. Stdio Transport over HTTP/SSE
**Decision**: Use stdio transport (pipe) as the default MCP transport.
**Rejected**: HTTP/SSE transport (requires a running server, port allocation, restart management). Stdio is the standard MCP pattern — clients spawn the server as a subprocess and communicate over stdin/stdout.

## 12. Test Strategy: Unit Tests with Mocked HTTP + Live Integration Tests (Skipped by Default)
**Decision**: Write unit tests that mock `httpx.Client.get()` and a live integration test gated behind `--live` flag.
**Rejected**: Only unit tests (could miss real API changes), only live tests (flaky in CI). The hybrid approach means CI runs fast unit tests while developers can verify real API behavior on demand.

## 13. Guard: Park-It / Park-Outside Flags Are Rendered
**Decision**: Surface the `parkIt` and `parkOutSide` flags from the NHTSA API prominently in recall reports.
**Rejected**: Ignoring them (these are critical safety instructions — "park your car outside" is actionable). The NHTSA API returns these per-recall; we render them with emoji and bold text so the AI highlights the urgent action.

## 14. Project Structure: Package Under `recallguard/` with `server.py` Entry Point
**Decision**: Single Python package with the module as `recallguard.server:main` CLI entry.
**Rejected**: Flat module (no namespace isolation), Django-style app (overkill). The package structure supports `pip install -e .` and `pyproject.toml` entry points consistently with other projects in the repo.