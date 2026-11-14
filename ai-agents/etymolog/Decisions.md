# Decisions — etymolog

## 1. CLI app over web app
- **Chosen:** CLI (Python argparse)
- **Rejected:** Flask/streamlit web UI
- **Why:** CLI keeps the project dependency-free and instantly runnable. No server process, no port management, no frontend framework. Fits the ai-agents/ pattern of the repo (most projects are CLI-first).

## 2. Python over Node.js / Rust
- **Chosen:** Python 3 (stdlib only + json)
- **Rejected:** Node.js (axios/cheerio), Rust (reqwest/scraper)
- **Why:** Python's stdlib has everything needed: `urllib.request` for HTTP, `json` for parsing, `unittest` for tests. Zero npm install or Cargo compile time. The VPS already has Python 3.14.

## 3. Single-file architecture over multi-module
- **Chosen:** One `etymolog.py` with functions (not classes for API wrappers)
- **Rejected:** Package with `etymolog/api/datamuse.py`, `etymolog/api/wiktionary.py`, etc.
- **Why:** The app has exactly three data flows (Wiktionary fetch, Datamuse fetch, LLM narrative) — each fits in 30-50 lines. A package structure adds `__init__.py`, import chains, and setup.py complexity for no benefit at this scale.

## 4. Datamuse over WordNet / ConceptNet
- **Chosen:** Datamuse API (free, zero-auth, no rate limit)
- **Rejected:** WordNet (requires NLTK download ~30MB), ConceptNet (requires API key)
- **Why:** Datamuse is instant — no key, no download, no setup. Returns semantically related words, rhymes, and trigger words in one call each. NLTK's WordNet is richer but requires a local download that bloats the project.

## 5. Wiktionary over Etymonline
- **Chosen:** Wiktionary API (MediaWiki parse + REST definitions)
- **Rejected:** Etymonline (no public API, requires scraping)
- **Why:** Wiktionary has a stable, documented API that returns structured etymology data. Etymonline has richer content but no API — scraping is fragile and unethical at scale.

## 6. LLM narrative over template-based output
- **Chosen:** LLM-generated narrative via OpenRouter (optional, falls back to template)
- **Rejected:** Static Jinja2 templates, hand-written formatting
- **Why:** An LLM turns dry etymology data into engaging, conversational stories — "from Old French to modern slang" reads better than a dictionary dump. The `--no-llm` flag and `_fallback_narrative()` ensure zero-API-key operation.

## 7. OpenRouter over direct Anthropic/OpenAI API
- **Chosen:** OpenRouter (one key, many models)
- **Rejected:** Direct Claude API, Direct GPT API
- **Why:** The repo already uses OpenRouter for other projects. One `OPENROUTER_API_KEY` env var works for all models. DeepSeek V4 Flash is cheap ($0.15/M tokens) and fast.

## 8. JSON output mode for scripting
- **Chosen:** `--json` flag returns structured data
- **Rejected:** Always human-readable, separate API mode
- **Why:** A `--json` flag costs 3 lines of code and makes the tool pipeable: `etymolog serendipity --json | jq '.etymology'`. No separate subcommand needed.

## 9. Pipe/stdin support
- **Chosen:** `sys.stdin.read()` fallback when no word argument
- **Rejected:** Force positional arg always
- **Why:** Piping enables batch processing: `cat words.txt | etymolog` or integration with other CLI tools. Common Unix pattern, zero extra code.

## 10. No caching layer
- **Chosen:** Always live-fetch from APIs
- **Rejected:** SQLite/JSON cache on disk
- **Why:** Etymology data rarely changes. A cache would add complexity (staleness, invalidation, file management) for minimal benefit — Wiktionary and Datamuse are fast enough for interactive use.

## 11. User-Agent header for API politeness
- **Chosen:** Custom `User-Agent: etymolog/1.0` header
- **Rejected:** Default Python urllib User-Agent
- **Why:** Both Wiktionary and Datamuse request meaningful User-Agent strings. Setting one explicitly is good API citizenship and avoids 403 blocks on some endpoints.

## 12. Temperature 0.7 for LLM narrative
- **Chosen:** `temperature=0.7`
- **Rejected:** 0.0 (deterministic), 1.0 (creative)
- **Why:** 0.7 balances factual accuracy with engaging prose. The etymology data grounds the output; the temperature lets the LLM be interesting without hallucinating false origins.

## 13. Max tokens 800 for LLM output
- **Chosen:** `max_tokens=800`
- **Rejected:** 256 (too short), 2048 (too expensive)
- **Why:** A word's journey needs ~3-4 paragraphs. 800 tokens gives room for a full narrative while keeping API cost under $0.001 per query.

## 14. Separate test file over inline doctests
- **Chosen:** `test_etymolog.py` with `unittest.TestCase`
- **Rejected:** Doctests in function docstrings, pytest
- **Why:** Unittest is stdlib (no pytest install needed). A dedicated test file supports mocking of network calls, which doctests cannot. 12 tests cover API calls (both success and failure paths), fallback narrative, formatting, and CLI behavior.

## 15. Lowercase word normalization
- **Chosen:** `word.strip().lower()` before any API call
- **Rejected:** Preserve user casing
- **Why:** Wiktionary page names are lowercase. Datamuse is case-insensitive. Normalizing avoids "Word" vs "word" lookup failures.