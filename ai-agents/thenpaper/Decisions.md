# Decisions.md — ThenPaper

Every significant design choice for ThenPaper, with the rejected alternatives
and the reasoning. 14 decisions.

## 1. Category: AI App, not MCP server or RAG
**Chosen:** A single-purpose, fun, consumer-grade AI app in `ai-agents/`.
**Rejected:** MCP server, browser extension, RAG pipeline.
**Why:** The rota landed on position 0 (AI Apps). ThenPaper fits the brief —
an everyday person types a date and gets something delightful and shareable,
no setup, no accounts.

## 2. Data source: Wikipedia On This Day REST API
**Chosen:** `https://en.wikipedia.org/api/rest_v1/feed/onthisday/{kind}/{MM}/{DD}`
**Rejected:** NumbersAPI date trivia (shallow, one fact only), HistoryAPI
(paid), scraping "On this day" websites (fragile), hard-coded datasets (stale
and tiny).
**Why:** Free, zero auth, no rate limits for light personal use, and returns
structured JSON (`year`, `text`, `pages`) for five facets — events, births,
deaths, holidays, selected anniversaries. Verified live before the build
(200 on all five endpoints, including Feb 29).

## 3. Runtime: Python 3 stdlib only (urllib), zero pip dependencies
**Chosen:** `urllib.request` for both the Wikipedia fetch and the LLM call.
**Rejected:** `requests` (not installed in the sandbox; adds install friction),
httpx + async (overkill for a CLI).
**Why:** The app runs anywhere with `python3` and no `pip install`. Biggest
failure mode in this repo is dependency rot; eliminating runtime deps
eliminates it entirely. Tests are the only thing that need `pytest`.

## 4. CLI, not a web app
**Chosen:** Terminal CLI with a rich ASCII newspaper render.
**Rejected:** Flask/FastAPI web UI, Streamlit, single-page HTML.
**Why:** Consistent with the existing `ai-agents/` portfolio (regex-please,
echo, stash are CLI/terminal-first), zero server to host, trivially testable,
and the ASCII front page is charm users actually share. JSON output (`--json`)
keeps a machine-readable path open for a future web wrapper.

## 5. LLM is optional and best-effort, template fallback always works
**Chosen:** Read `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` from env; on any LLM
failure (bad key, no credit — verified live), fall back to deterministic witty
templates.
**Rejected:** Requiring an API key (excludes casual users, breaks the demo),
bundling a local model (huge, slow), never calling an LLM (loses the wow
factor).
**Why:** The tool must *always* print a paper. Live verification during this
build found the Anthropic key out of credit and the OpenAI key rejected — the
fallback kept the whole app functional. When a valid key exists, the LLM
writes the headline, dek, and twins intro; otherwise templates do.

## 6. LLM via raw HTTP, not the vendor SDKs
**Chosen:** Direct `POST` to `https://api.anthropic.com/v1/messages` and
`https://api.openai.com/v1/chat/completions` with `urllib`.
**Rejected:** `anthropic` / `openai` Python packages.
**Why:** Keeps runtime dependencies at zero. The endpoints are stable, the
payload is small, and a mutually understood JSON contract is all the code
needs. Model name is overridable with `THENPAPER_MODEL` /
`THENPAPER_OPENAI_MODEL` so the app doesn't die when vendor model names drift.

## 7. Injection points (`set_fetcher`, `set_poster`) instead of mocking the network
**Chosen:** Module-level injection functions let tests swap the HTTP layer
with fake functions.
**Rejected:** `responses` library, real network calls in tests, patching
`urllib` globally.
**Why:** Hermetic tests that pass offline with zero keys, and the seams also
make the code reviewable — the data layer and voice layer are deliberately
ignorant of HTTP mechanics.

## 8. Simulated fallback data, not hard failure
**Chosen:** `simulate_day()` returns deterministic, date-validated fake facts
when every endpoint fails.
**Rejected:** Raising an exception, printing a bare error.
**Why:** A "newspaper" that prints nothing is a broken toy. Deterministic
simulation (same month/day → same output) keeps tests stable and gives
`--offline` a demo mode for screenshots and CI.

## 9. Ranking: recency + era affinity, not Wikipedia page rank
**Chosen:** Score events by era bonus (post-2000 > 1900s > 1800s > 1500s >
older), then year, then text richness; when a focus year is given (`1990/10/19`),
events closest to that year win.
**Rejected:** Wikipedia pageview `rank` field (probed live: `rank` is `None`
for every On This Day entry), raw chronological = oldest first (feels like an
archive, not a newspaper), random shuffle (untestable).
**Why:** A front page should lead with what a modern reader finds
relatable; the focus-year mode delivers the "front page of the year you were
born" promise.

## 10. Birthday twins concept
**Chosen:** The "Born This Day" section is framed as *your birthday twins*,
preferring births 1900–2026.
**Rejected:** Listing births oldest-first, omitting births entirely.
**Why:** Personalization is the emotional hook — "my birthday twins" is
shareable and delightful; modern births are relatable.

## 11. ASCII render with theme variants, not emoji/ANSI rainbows
**Chosen:** Double-line box masthead, `★ ☾ ✦` accents, three editions.
**Rejected:** Rich ANSI colors (depends on terminal), image output (needs
assets), HTML render (scope creep).
**Why:** Pure text renders anywhere, is diffable/testable, and looks like a
printed broadsheet. Themes give personality without dependencies.

## 12. Date input grammar
**Chosen:** Accept `MM/DD`, `M/D`, `YYYY/MM/DD`, and `today`; strict
validation via `datetime.date` construction (rejects 2/30, 13/40).
**Rejected:** Free-text parsing ("october nineteenth") — needs a date parser
dependency and ambiguity handling; only full dates — inconvenient.
**Why:** Three unambiguous input forms cover every real use (quick lookup,
birthday-year focus, today), and validation happens at the edge so the core
never sees garbage.

## 13. Single source of validation
**Chosen:** `api._validate_date` is the one place month/day legality is
decided; CLI and `simulate_day` both call it.
**Rejected:** Duplicated validation in cli.py (drift risk), no validation
(breaks the API contract).
**Why:** One function = one truth. The CLI catches bad dates and exits 2 with
a friendly message; the API layer still protects itself.

## 14. Hanging-indent bullets and hard-wrap for all text
**Chosen:** `_wrap()` hard-chunks words longer than the width; `_bullet()`
indents wrapped continuation lines under the bullet text.
**Rejected:** CSS-style soft wrapping (textwrap default breaks the newspaper
look), truncating long facts (loses real history).
**Why:** Front-page facts are frequently >70 chars (the Wikipedia feed has
multi-sentence entries); ragged continuation lines looked broken. The test
suite pins both behaviors (`test_wrap_handles_long_words`, render tests).

---

## What was rejected entirely (never built)
- **ISS flyover tracker (Open Notify):** the `iss-pass` endpoint 404'd during
  validation — same-day flake or retirement, but the data layer wasn't
  trustworthy enough to build on.
- **Neighborhood history (Wikipedia geosearch):** fun, but geo-disambiguation
  ("Springfield" has hundreds of meanings) made it a rabbit hole for a
  one-session build.
- **Thought-reframing and tattoo-idea apps:** solid, but pure-LLM with no free
  data backbone — weaker demo and harder to test than ThenPaper.