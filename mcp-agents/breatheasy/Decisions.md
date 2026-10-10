# breatheasy — Decisions

Every material design choice for breatheasy, in the house format:
**Decision** (what we did), **Rejected** (what we didn't and why),
**Trade-off** (what it costs us). Shipped 2026-10-10, v0.1.0.

## 1. MCP server + CLI, not web app or CLI-only

**Decision** — Ship both an MCP server (stdio) and a plain CLI over one
shared core (`api.py` / `geo.py` / `advice.py`).

**Rejected** — A web app (hosting, auth, frontend maintenance, and no
obvious consumer for a "where should I walk?" tool), and CLI-only (the
primary consumer in this repo is an MCP-capable agent — the CLI exists for
humans and scripts).

**Trade-off** — Two entry surfaces to keep consistent; worth it because
both are thin and share ~100% of logic.

## 2. Python + FastMCP SDK over Node / raw stdio

**Decision** — Python 3.13 with the official `mcp` SDK (1.30.0), using
`mcp.server.fastmcp.FastMCP`.

**Rejected** — The Node MCP SDK (would fork the stack for one tool), and
hand-rolling JSON-RPC over stdin/stdout (reimplementing initialize/handshake
/notification plumbing that the SDK provides and tests).

**Trade-off** — Stuck with the SDK's stdio conventions; acceptable since
stdio is explicitly required.

## 3. FastMCP over the raw `Server` class

**Decision** — `FastMCP` decorators (`@mcp.tool()`) with pydantic-derived
schemas from plain type hints.

**Rejected** — `mcp.server.Server` + manual `Tool` objects, explicit JSON
schemas, and low-level request handlers.

**Trade-off** — Less fine-grained protocol control; far less code, and tool
schemas stay in sync with signatures automatically.

## 4. Sync `httpx.Client` over async

**Decision** — One synchronous `httpx.Client` shared by the API layer;
injected so tests swap in `httpx.MockTransport`.

**Rejected** — `httpx.AsyncClient` / `aiohttp` (async plumbing everywhere,
including the CLI), and `urllib` (no timeouts/retries ergonomics, uglier).

**Trade-off** — No concurrent requests per process; irrelevant at this
scale — each MCP request is one or two HTTP calls.

## 5. Module separation: `api` / `geo` / `advice`

**Decision** — Three focused modules: `api.py` (transport + payload
helpers), `geo.py` (place resolution), `advice.py` (offline knowledge).

**Rejected** — One fat module with everything, and premature DDD layers.

**Trade-off** — Slightly more imports; clean seams for unit tests (advice
and geo test with zero HTTP, api tests mock only transport).

## 6. Open-Meteo (zero-key) over AirNow / IQAir

**Decision** — All data from Open-Meteo's free APIs (geocoding +
air-quality), verified live 2026-10-10, no key, no signup.

**Rejected** — AirNow (key required, US-only), IQAir (key + tight rate
limits), Tomorrow.io (key), any service needing registration.

**Trade-off** — No official-agency alerts or hyper-local monitors; global
coverage + zero ops beats that for v0.1.

## 7. Geocoding strategy + "lat,lon" fast path

**Decision** — Geocode free text with Open-Meteo's geocoding API, take the
first (most relevant) result, and label it "Name, Admin1, Country".
A local regex additionally accepts `"40.71,-74.01"` and resolves it
**without any network call**.

**Rejected** — A bundled gazetteer (huge, stale), require-structured input
(hostile UX), and taking the highest-population result blindly (Open-Meteo
already orders by relevance).

**Trade-off** — Ambiguous queries ("Springfield") can pick the wrong city;
users disambiguate with "Springfield, Illinois".

## 8. US AQI primary, European AQI fallback

**Decision** — Report US AQI when present; when `us_aqi` is NULL use
`european_aqi` and label the source explicitly ("European AQI (US AQI not
reported)"). When both exist, show both.

**Rejected** — Always-European (the bands differ and US users expect US
AQI), or silently picking whichever is present.

**Trade-off** — Two numbers to display; the explicit label keeps the
meaning unambiguous.

## 9. Pollen NULL handling

**Decision** — Pollen is optional: missing variables or all-NULL values
render as "no data for this region/season" per type (or wholesale), never
an exception. Reported value is the peak P/m³ over the requested window.

**Rejected** — Synthesizing values (lying), unit math beyond the API's raw
P/m³, and crashing on NULLs.

**Trade-off** — Some locations show "no data" rows; that is the honest
answer, and regional pollen coverage is mostly Europe anyway.

## 10. Embedded offline band tables over fetching thresholds

**Decision** — EPA AQI bands (name, range, hex color, category, advice,
emoji) and pollen buckets live in `advice.py`, pinned at release and
covered by boundary tests (49/50/51, 100/101, 150/151, 200/201, 300/301).

**Rejected** — Fetching thresholds from a remote source at runtime
(latency, coupling, a second network dependency).

**Trade-off** — Advice is frozen until the next release; documented, and
trivially updated in one file.

## 11. Formatted Markdown tool output over raw JSON

**Decision** — Every MCP tool returns formatted Markdown (headings, emoji,
markdown tables, structured bold fields); the CLI returns plain text.

**Rejected** — JSON tool output (LLM clients render JSON poorly and the
house style is human-readable answers).

**Trade-off** — Programmatic consumers must parse text; the MCP audience is
an LLM, which renders Markdown natively.

## 12. Friendly error strings over exceptions

**Decision** — Tools catch `GeoLookupError` and HTTP/parse failures and
return a friendly string ("Could not find 'Atlantis' …", "Could not fetch
…") — never an exception. The CLI prints the same messages to stderr and
exits 1.

**Rejected** — Propagating exceptions to the MCP client (a crash for the
user) and bare "error" strings without guidance.

**Trade-off** — The client can't branch on error types; fine for a
conversational tool.

## 13. Test approach: fixtures + MockTransport, zero network

**Decision** — Two real Open-Meteo samples (captured today) plus one
synthetic pollen fixture live in `tests/fixtures/`; all HTTP goes through
`httpx.MockTransport`; CLI output is asserted via `capsys`; server tools
run with an injected client.

**Rejected** — Live-API tests (flaky, banned in CI, and the spec demands no
network) and hand-written "fake" payloads that don't resemble the API.

**Trade-off** — We can't detect upstream API schema drift automatically;
mitigated by pinning genuine samples and re-capturing on release.

## 14. Packaging: setuptools pyproject + console script

**Decision** — `pyproject.toml` (setuptools, `name=breatheasy`,
`version=0.1.0`, `packages=["breatheasy"]`), a console script
`breatheasy = breatheasy.cli:entrypoint`, and `python -m breatheasy` via
`__main__.py`.

**Rejected** — Flat script layout (not importable, no entry point), and
poetry/uv lockfile machinery (overkill for two dependencies).

**Trade-off** — Not yet wheel-published; `pip install -e .` or running from
the repo root both work today.

---

*Honesty note:* wildfire checks say pollution "may include wildfire smoke"
at AQI ≥ 151 / PM2.5 ≥ 55.4 µg/m³ — high values have other causes and the
wording never claims confirmed smoke. The README carries a non-medical-advice
disclaimer.