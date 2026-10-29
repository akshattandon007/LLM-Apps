# Decisions.md — Ingenius

## 1. Python 3.10+ as the runtime

**Chosen:** Python 3.10+ with standard library + `requests`
**Rejected:** Node.js, Go, Rust
**Why:** Python is the repo's de facto standard, already present on the VPS, and the task is I/O-bound (single HTTP call). No need for async or compiled speeds.

## 2. CLI-only interface (no web UI)

**Chosen:** Simple command-line tool with `argparse`
**Rejected:** Gradio, Streamlit, Flask web app, TUI with curses/textual
**Why:** The tool takes one argument and returns text. A web UI adds 20× the code for zero benefit in a headless/terminal workflow. Users can pipe output or script it. A web GUI would be over-engineering for a single-query tool.

## 3. OpenRouter as the LLM backend

**Chosen:** OpenRouter (Google Gemini 2.0 Flash model)
**Rejected:** OpenAI API (requires credit card), Anthropic API (requires credit card), Google AI Studio direct (free but different auth pattern)
**Why:** OpenRouter offers a free tier with no credit card required and a single unified API. Gemini 2.0 Flash is fast, cheap (often free), and good at structured JSON output. The user likely already has an OpenRouter key from other projects in this repo.

## 4. JSON-only LLM response format

**Chosen:** Instruct the LLM to return only a JSON object with `{"substitutes": [...]}`
**Rejected:** Free-text response, markdown table, XML-structured response
**Why:** JSON is parseable, schematised, and testable. It enables clean formatting on the Python side, graceful error handling if the LLM hallucinates, and easy future extensions (JSON output flag for piping).

## 5. Three substitutes as default

**Chosen:** Always request exactly 3 substitutes
**Rejected:** Variable count (1-5), user-configurable count
**Why:** 3 is the Goldilocks number — enough to give real choice, few enough to avoid overwhelming in a terminal. Variable count complicates the schema and the LLM prompt unnecessarily for a first version.

## 6. Environment variable for API key

**Chosen:** `OPENROUTER_API_KEY` read from environment
**Rejected:** Config file (YAML/TOML), `.env` file with python-dotenv, interactive prompt, hardcoded key
**Why:** Environment variables are the standard for CLI tools: they don't leak, don't need file management, and integrate with shell profiles and CI/CD. A `.env` loader adds a dependency for marginal convenience.

## 7. Mood system as optional modifier

**Chosen:** `--mood` flag with 3 choices: `quick`, `pantry`, `gourmet`
**Rejected:** No mood system, free-text mood ("I'm in a hurry"), slider (1-10 speed)
**Why:** Cooking substitutions have a clear trilemma between speed, ingredients-on-hand, and quality. Three named moods are intuitive and constrain the LLM prompt effectively. Free-text moods would produce inconsistent results.

## 8. Error handling: fail-fast with clear messages

**Chosen:** `sys.exit(1)` with explanatory stderr messages for missing API key, network errors, and malformed JSON
**Rejected:** Silent defaults, fallback logic (use a different model), graceful degradation
**Why:** The tool doesn't work without an API key or network — pretending otherwise is confusing. Clear error messages let the user fix the problem instantly. Silent fallbacks hide broken configurations.

## 9. Mocked unit tests (no live API calls)

**Chosen:** `unittest.mock.patch` to mock `requests.post`
**Rejected:** Integration tests with real API calls, VCR.py cassette recording
**Why:** Tests must run without network, without an API key, and without cost. Mocking the HTTP layer tests all code paths (success, markdown-wrapped JSON, empty results) deterministically. A separate integration test suite could be added later.

## 10. Single-file module structure

**Chosen:** Everything in `ingenius.py` (main), separate `test_ingenius.py`
**Rejected:** Package structure with `ingenius/__init__.py`, `ingenius/cli.py`, `ingenius/prompt.py`, `ingenius/llm.py`
**Why:** The tool is ~150 lines. Splitting into multiple files adds import overhead and navigation cost for zero architectural benefit. A single file keeps the mental model simple. Tests are separate because they're a different concern.

## 11. `python -m ingenius` compatibility

**Chosen:** `if __name__ == "__main__": main()` with `-m` compatibility via `__init__.py` not required (the project ships as a flat script)
**Rejected:** `setuptools` entry_points, click/fire CLI framework
**Why:** An entry_points installer adds packaging complexity for a one-file tool. `python ingenius.py` is the natural invocation. No CLI framework needed — argparse is built-in and sufficient for 3 arguments.

## 12. No caching layer

**Chosen:** Every invocation calls the LLM fresh
**Rejected:** SQLite/JSON cache of ingredient → substitutes pairs
**Why:** Substitutions are context-dependent (recipe + mood change the answer). A cache would need an invalidation strategy and adds complexity for a tool that takes ~2 seconds per call. Not worth it unless the tool sees 100+ daily queries.

## 13. Markdown code-fence stripping in LLM response

**Chosen:** Strip ```json ... ``` fences from the LLM response before JSON parsing
**Rejected:** Expect only raw JSON, ask model explicitly once
**Why:** Some models (especially free-tier) inconsistently wrap JSON in markdown fences. Stripping them is defensive and costs ~3 lines of code. Pure prompt engineering alone can't guarantee compliance across all models.

## 14. Separate `requirements.txt` (not pyproject.toml)

**Chosen:** Plain `requirements.txt` with minimal deps (`requests`)
**Rejected:** `pyproject.toml` with `setuptools`/`flit`/`poetry`
**Why:** The project has one external dependency. A full pyproject.toml with version pinning is overkill. requirements.txt is the lowest-friction, most predictable format for the repo's ecosystem (standard `pip install -r`).

## 15. No async/parallel calls

**Chosen:** Single synchronous `requests.post` call
**Rejected:** `httpx` async, concurrent.futures for parallel substitute generation
**Why:** The tool makes one LLM call that returns all 3 substitutes at once. There's nothing to parallelise. Async adds cognitive complexity with zero latency benefit for a single network request.