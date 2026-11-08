# Decisions.md — NameSage Architectural Decision Record

## 1. CLI over web interface

**Decision:** Build a CLI tool (argparse), not a web app.

**Context:** The project needs a simple, scriptable analytics tool. A web app would require a server, frontend, and deployment overhead.

**Rejected:** Flask/FastAPI web app — too much ceremony for a single-query tool. Streamlit/Gradio — heavy dependencies and slower startup.

**Consequence:** Zero deployment friction; pipeable output; easy to integrate with shell scripts.

---

## 2. Python over other languages

**Decision:** Use Python 3.10+.

**Context:** Fast to prototype, excellent async HTTP libraries, rich ecosystem for CLIs (argparse, Rich).

**Rejected:** Rust/Crystal — faster but slower to develop and no Rich-like terminal library. Node.js — less mature async HTTP ergonomics for this use case. Go — no built-in async for concurrent API calls.

**Consequence:** Easy onboarding; uses existing Python skills across the team.

---

## 3. Async HTTP over synchronous requests

**Decision:** Use `httpx.AsyncClient` with `asyncio.gather` for parallel API calls.

**Context:** Four independent API calls should run concurrently, not serially.

**Rejected:** Synchronous `requests` library — simple but serial (4× latency). ThreadPoolExecutor — awkward cleanup and harder to test. `aiohttp` — equally valid but `httpx` has a friendlier API and is better integrated with `pytest-httpx`.

**Consequence:** Aggregate latency ≈ max(individual API latency) instead of sum. Tests can mock individual calls.

---

## 4. Rich over custom ANSI formatting

**Decision:** Use the `rich` library for terminal output (Panels, Tables, Text styling).

**Context:** Output must be readable, colorized, and structured.

**Rejected:** Manual ANSI escape codes — verbose, error-prone, hard to maintain. `colorama` — only handles colors, not layout/structure.

**Consequence:** Maintainable formatting code; consistent cross-platform color support; easy to add new output sections.

---

## 5. Free, zero-auth APIs (Agify/Genderize/Nationalize/Datamuse)

**Decision:** Use these four APIs — all free, no API key required, no rate limits for low-volume use.

**Context:** Need age, gender, nationality, and wordplay data without operational cost.

**Rejected:** Paid encyclopedic APIs (Wikipedia API, Wikidata SPARQL) — more data but require auth, heavier queries, slower. Proprietary name databases — licensing concerns.

**Consequence:** No auth setup needed; works out of the box; limited to single-name queries per request.

---

## 6. OpenRouter for LLM synthesis

**Decision:** Use OpenRouter API (free models like MythoMax) for name profile generation, gated behind an optional env var.

**Context:** LLM synthesis is a "nice to have" enhancement, not a core requirement.

**Rejected:** Local LLM (llama.cpp, Ollama) — adds GBs of dependencies and hardware requirements. OpenAI API — requires paid account and API key setup. No LLM at all — output is just raw data, less engaging.

**Consequence:** LLM profiles are opt-in. Without the key, the tool still works, just without the narrative section.

---

## 7. Package layout: flat module namespace

**Decision:** All four Python modules (`api.py`, `cli.py`, `llm.py`, `formatter.py`) live in the `namesage/` package directory.

**Context:** Small codebase (< 500 lines total); subpackages would add unnecessary hierarchy.

**Rejected:** `namesage/sources/` subpackage for API wrappers — premature decomposition. Single monolithic file — poor separation of concerns.

**Consequence:** Easy to navigate; modules are small enough to understand at a glance.

---

## 8. `pyproject.toml` over `setup.py`

**Decision:** Use `pyproject.toml` as the sole build configuration.

**Context:** Modern Python packaging standard (PEP 517/518/621). No need for dynamic fields.

**Rejected:** `setup.py` — legacy, less declarative, encourages arbitrary code in build scripts.

**Consequence:** Declarative config; `pip install -e .` works; CLI entry points defined cleanly.

---

## 9. Graceful error handling with structured error dicts

**Decision:** API calls return either valid data or `{"error": "description"}`. The formatter checks for the `error` key and displays a warning panel.

**Context:** External APIs can fail (network, rate limits, server errors). The tool should never crash.

**Rejected:** Raising exceptions — harder to propagate cleanly through the async pipeline. Returning `None` — loses diagnostic information.

**Consequence:** Every section gracefully degrades; the user sees which data points failed and why.

---

## 10. LLM fallback to raw data display

**Decision:** If `OPENROUTER_API_KEY` is unset or the LLM call fails, the formatter still prints all API data, just without the narrative section.

**Context:** The LLM profile is additive — the core tool works without it.

**Rejected:** Hard failure ("API key required") — would prevent using the tool without extra setup. Fake/sample profile — misleading.

**Consequence:** The tool is always usable. Users can decide whether to configure the LLM integration.

---

## 11. pytest-httpx for HTTP mocking

**Decision:** Use `pytest-httpx` to mock all external HTTP calls in tests.

**Context:** Tests must run offline, deterministically, and without hitting rate limits.

**Rejected:** Responses library — Python-only, but less maintained. VCR.py — records real requests, which introduces flakiness from network-dependent cassettes. `unittest.mock.patch` — verbose, doesn't integrate with `httpx.AsyncClient` well.

**Consequence:** Clean, declarative mocks per test case; automatic matching on URL, method, and params.

---

## 12. `asyncio_mode = "auto"` in pytest config

**Decision:** Set `asyncio_mode = "auto"` in `pyproject.toml` so async test functions are automatically discovered as coroutines.

**Context:** All API functions are `async def`, and tests need to `await` them.

**Rejected:** `asyncio_mode = "strict"` — requires `@pytest.mark.asyncio` on every test, which is repetitive. Manual event loop management — error-prone and deprecated.

**Consequence:** Less boilerplate; async tests "just work."

---

## 13. Capsys for formatter test assertions

**Decision:** Use pytest's built-in `capsys` fixture to capture and assert on formatted terminal output.

**Context:** The formatter uses `rich.console.Console.print()` which writes to stdout.

**Rejected:** Mocking `rich.console.Console` — fragile, over-engineered for checking text presence. Snapshot testing — too heavy for a small formatter.

**Consequence:** Simple string assertions on captured output; easy to verify that all sections render correctly.

---

## 14. No caching strategy (yet)

**Decision:** Do not implement caching for API responses.

**Context:** Each name query is typically one-off. APIs are fast (< 500 ms). Caching adds complexity (TTL, invalidation, storage).

**Rejected:** In-memory dict — trivial but unbounded memory growth. Disk-based (diskcache, sqlite) — added dependency and complexity for marginal gain. Redis — ridiculous overkill for a CLI tool.

**Consequence:** Every query hits live APIs. Acceptable given the tool's low-volume use pattern. Caching can be added later if profiling shows it's needed.

---

## 15. Test completeness: public API + formatting, not LLM

**Decision:** Tests cover the API wrapper module and the formatter module. The LLM module is tested implicitly via the CLI's fallback behavior.

**Context:** LLM calls would require either a real API key or extensive mocking of HTTP response bodies. The LLM profile is a simple pass-through (prompt in → text out).

**Rejected:** Mocking OpenRouter responses — tests would be brittle and tied to specific response shapes. Integration tests with real key — can't run offline.

**Consequence:** Good coverage on the data-fetching and rendering layers. LLM module is trivially simple and covered by the "no key" fallback path in CLI tests.