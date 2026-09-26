# Decisions.md — Mood Mixtape

## 1. CLI-first (not web app)
**Chosen:** CLI with Rich terminal output
**Rejected:** Streamlit/Gradio web app, Flask/FastAPI server
**Why:** Mood Mixtape is a shareable, single-purpose app — adding a web server adds deployment overhead (ports, uptime, domain) that doesn't serve the core value. A CLI with beautiful Rich-formatted output is instantly usable, testable, and shareable via terminal transcripts. The Rich library gives us colored tables and panels that rival web UI for this use case.

## 2. Python (not Go, Rust, TypeScript)
**Chosen:** Python 3.13
**Rejected:** Go binary compilation, Rust CLI, Node.js/TypeScript
**Why:** Python has the richest ecosystem for LLM integration (OpenAI SDK, httpx) and the fastest development cycle. The app is I/O-bound (HTTP + LLM calls), so Python's performance is adequate. No compilation step means zero friction between writing code and running it.

## 3. OpenAI-compatible SDK (not direct HTTP to LLM)
**Chosen:** `openai` Python SDK
**Rejected:** Raw `httpx` calls to the LLM API, LangChain
**Why:** The OpenAI SDK provides built-in retry logic, response format enforcement (`response_format={"type": "json_object"}`), and a familiar API surface. LangChain was rejected because we only need two simple LLM calls — the framework overhead doesn't justify itself.

## 4. MusicBrainz API (not Spotify, Last.fm, Genius)
**Chosen:** MusicBrainz (zero-auth, rate-limited, open data)
**Rejected:** Spotify Web API (requires OAuth + client registration), Last.fm API (requires API key), Genius API (requires client access token)
**Why:** MusicBrainz requires **zero authentication** — no API key, no OAuth flow, no app registration. This means the app works immediately after `pip install` with zero configuration. The trade-off is rate limiting (1 req/s) and less polished metadata, but for a mood-based discovery tool the breadth of data matters more than depth per track.

## 5. JSON response format for LLM calls
**Chosen:** `response_format={"type": "json_object"}` on all LLM calls
**Rejected:** Free-text parsing with regex, markdown extraction
**Why:** Enforcing JSON output from the LLM eliminates brittle parsing. The JSON schema acts as a contract — if the model deviates, the JSON parse fails loudly instead of silently producing garbage text. This is especially important for the song selection step where structured data feeds directly into the card formatter.

## 6. `set_client()` injection pattern for testability
**Chosen:** Module-level `set_client()` that accepts `httpx.Client | None`
**Rejected:** Global constants, environment-based URL switching, mocking at the `httpx` level
**Why:** The `set_client()` pattern lets tests inject `httpx.MockTransport` without patching imports or monkey-patching. Test code is explicit about what mock responses the server should return. When not set, the module creates a real `httpx.Client()` — so production code doesn't change behavior. This is the same pattern used in production-grade MCP servers.

## 7. Dataclasses (not Pydantic models for internal types)
**Chosen:** `@dataclass` for Track, MixtapeSong, Mixtape
**Rejected:** Pydantic BaseModel for everything, plain dicts
**Why:** Dataclasses provide type hints + immutability + readable `__repr__` with zero extra dependencies. Pydantic is in `requirements.txt` only because the OpenAI SDK depends on it — using Pydantic for our own models would couple us to its validation semantics (which we don't need for simple data carriers). Dicts were rejected because they lack IDE autocompletion and are error-prone with nested access patterns.

## 8. One-level package structure (not flat scripts)
**Chosen:** `mood_mixtape/` package with 5 modules
**Rejected:** Single `app.py` file, deeply nested package hierarchy
**Why:** Five focused modules (cli, models, musicbrainz, curator, card) make the code navigable: replace the API client without touching the curator, swap the output format without touching the CLI. A single file would be ~700 lines with mixed concerns. Deep nesting would be overkill for a project with ~35 functions.

## 9. `argparse` (not Click, Typer, Fire)
**Chosen:** `argparse` from stdlib
**Rejected:** Click (third-party), Typer (rich but complex), Fire (implicit API)
**Why:** The CLI surface is tiny: one optional positional argument + one flag. Stdlib `argparse` needs no extra install and is universally understood. A framework like Click would add a dependency for what amounts to 10 lines of argument parsing.

## 10. No async (synchronous httpx)
**Chosen:** Synchronous httpx calls throughout
**Rejected:** `httpx.AsyncClient`, `asyncio`, trio
**Why:** The pipeline is linear (mood → search → curate → print), with no concurrent operations. Async adds complexity (`async`/`await` chains, event loop management) for zero throughput benefit. The MusicBrainz rate limit (1 req/s) makes parallelism pointless.

## 11. Cover art as text description (not image generation)
**Chosen:** Cover art described as a DALL-E prompt string
**Rejected:** Actual image generation via DALL-E API
**Why:** Generating actual cover art would require an OpenAI API key with DALL-E access and would add latency and cost. A text description serves the same imaginative purpose — the user can visualize or generate it themselves. The description is stored as `cover_art_description` in the Mixtape model for future extension.

## 12. Deduplication at the MusicBrainz layer (not after LLM)
**Chosen:** Dedup by (`title`, `artist`) before passing tracks to the LLM
**Rejected:** Letting the LLM deduplicate, dedup after LLM selection
**Why:** MusicBrainz searches across multiple keywords often return the same recording. Deduplicating early reduces the prompt size (fewer tokens) and prevents the LLM from selecting the same song twice. The LLM sees a clean, distinct list and can focus on curation.

## 13. No caching layer (re-fetches every run)
**Chosen:** Fresh MusicBrainz search on every invocation
**Rejected:** Local SQLite cache, Redis, disk-based JSON cache
**Why:** Mood Mixtape is meant to be surprising and serendipitous — caching would return the same results for the same mood, reducing the "discovery" aspect. MusicBrainz data is stable enough that re-fetching is trivially fast (1-2 seconds). Caching would add complexity (cache invalidation, staleness) with no user-facing benefit.