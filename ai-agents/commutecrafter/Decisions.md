# Decisions Log — CommuteCrafter

Every non-obvious choice, what it beat, and what it costs.

---

### 1. Solve the inverse problem: fit content to the window, not the window to content

**Context:** Every content app starts with content ("here are 40 podcasts") and hopes the user finds a slot. Commutes are fixed, immovable, and arbitrary — 22 minutes, not 20 or 25.

**Decision:** The commute length is the primary input. Content is selected and cut to fit it.

**Rejected:**
- **Catalog-first browsing with duration filters** — this is what podcast apps already do badly; a filter for "under 25 min" still gives you a 9 minute episode and 16 minutes of silence.
- **Recommend a single item** — one item can never fit an arbitrary window; you need a set.

**Trade-off:** Requires word-level duration data per candidate (see decision 3). Content that cannot be measured cannot be planned.

---

### 2. Three-act pacing (18% / 62% / 20%) instead of flat filling

**Context:** A plan could simply be "items that sum to 22 minutes", in any order.

**Decision:** Split the window into warm-up, core and wind-down with fixed shares, then fill each act separately.

**Rejected:**
- **Flat greedy fill** — produces plans like "47 minute essay, then done", which is unusable in a 22 minute commute and ends mid-thought.
- **Let the user set the shares** — adds configuration for a problem almost nobody has. The defaults are the product.
- **LLM-decided pacing** — non-deterministic and untestable; pacing is arithmetic, not judgement.

**Trade-off:** A short window (under ~6 minutes) gets thin acts. Mitigated by the balance pass and by dropping empty segments.

---

### 3. Real word counts from real text, not byte sizes or feed descriptions

**Context:** Reading time is the core promise. It would be far cheaper to estimate from page bytes or RSS descriptions.

**Decision:** Fetch the actual plaintext and count words: Wikipedia full extracts, arXiv abstracts, HN `story_text`, Gutenberg text prefixes.

**Rejected:**
- **`prop=info` page length in bytes ÷ 6** — one request instead of N, but Wikipedia markup overhead varies wildly by article (tables, references, infoboxes). A 10% error on a 40 minute read is 4 minutes of lies.
- **RSS/OpenGraph descriptions** — truncated to ~50 words, useless for duration.
- **Headline-only estimates via LLM** — plausible-looking numbers with no grounding. Unacceptable in a tool whose entire value is accuracy.

**Trade-off:** Wikipedia costs one extra request per candidate (~6 per topic), parallelised 4-wide. Measured cost: a live 28 minute plan completes in a few seconds.

---

### 4. Keyless sources only — no Spotify, no NewsAPI

**Context:** The first research pass proposed Spotify (podcasts by duration) and NewsAPI (headlines).

**Decision:** Only sources that need zero credentials: Wikipedia, arXiv, Hacker News (Algolia), Project Gutenberg, Open-Meteo.

**Rejected:**
- **Spotify Web API** — OAuth with refresh-token dance, app registration, and a 25-item search cap. It would turn a `pip install` into a 15 minute setup ritual for the single most-requested feature (podcasts).
- **NewsAPI** — 100 requests/day free tier and no duration data at all.
- **Podcast Index** — needs an API key and most feeds expose durations inconsistently.

**Trade-off:** No real podcast episodes. Compensated by `--mode listen`, which converts text plans to narration time at 150 wpm, and by Gutenberg long reads that work well as audio.

---

### 5. Wikipedia in two stages: search for candidates, then one call per title for full text

**Context:** A single `generator=search&prop=extracts` call returns intros only (~8 sentences, ~200 words). Those are far too short to fill a core act.

**Decision:** Search with `exintro` for a display summary, then fetch each candidate's full plaintext individually (`exlimit=1`), in a 4-worker thread pool.

**Rejected:**
- **`exintro` only** — every item becomes a 1-2 minute read; plans degenerate to lists of stubs (observed: a 24 minute plan filled only 5.2 minutes).
- **`action=parse&prop=text`** — returns full HTML with references and navboxes; requires an HTML parser (bs4 isn't installed) and inflates payloads several-fold.
- **`exlimit=20` with full text** — MediaWiki only honours multi-page full extracts when `exintro` is set; otherwise you get one page per request anyway.

**Trade-off:** N extra requests per topic instead of 1. Slightly slower; dramatically better plans. Falls back to intro length if an individual call fails.

---

### 6. Greedy best-fit per act, then a global pad/trim pass — not knapsack DP

**Context:** Choosing items that sum to a target is a subset-sum problem. Optimal solutions exist.

**Decision:** Greedy best-fit-decreasing inside each act, then a balancing pass that pads (trimmed item) or trims (partial/last item) the total into tolerance.

**Rejected:**
- **Dynamic programming / ILP** — optimal, but the objective isn't purely "exact sum": we also prefer preferred categories, source diversity, and substance. A DP would need a weighted objective and would still be overruled by the pacing split.
- **Random sampling until it fits** — non-deterministic, and tests cannot assert anything stable.
- **Pure greedy with no balancing** — left a 60 minute plan 364 seconds short in testing, because no single act could absorb the remainder.

**Trade-off:** Not provably optimal. In practice the pad/trim pass lands plans within ±90s across 8–60 minute windows (asserted in `test_planner.py`).

---

### 7. Partial items with an explicit fraction, rather than dropping what doesn't fit

**Context:** An 89% fit is a real outcome. Discarding the item leaves silence; including it whole overshoots by 3 minutes.

**Decision:** Keep the item, mark `fraction`, recompute seconds from `words × fraction`, and render it as `[89%]` with the instruction "trimmed to fit".

**Rejected:**
- **Drop and accept the gap** — a 22 minute plan delivering 19 minutes is a broken promise, and the user notices on day one.
- **Round up and overshoot** — worse: you arrive mid-sentence, which is precisely the failure the app exists to fix.
- **Speed up playback to fit** — 1.4x narration is a real option, but it changes comprehension and belongs as a separate feature, not a silent default.

**Trade-off:** Sub-35% fractions are refused (`MIN_PARTIAL_FRACTION`) — a 4 minute nibble of a 40 minute article isn't worth starting.

---

### 8. SQLite memory of served URLs, in a local file

**Context:** Without memory, a recommender serves the same top-ranked Wikipedia article every morning.

**Decision:** Record every served URL with a timestamp in `~/.local/share/commutecrafter/commutecrafter.db`, exclude anything served in the last 14 days, override with `COMMUTECRAFTER_DB`.

**Rejected:**
- **No memory** — trivially reproducible bug: identical plan on consecutive runs (now asserted against in `test_cli.py`).
- **Random shuffle of candidates** — avoids exact repeats but still surfaces the same "top" items constantly, just in a different order.
- **Cloud sync** — this is a local CLI; no account, no server, no sync surface.

**Trade-off:** A 14 day window can exhaust a narrow topic. Mitigated: if the pool dries up, the plan says so in `warnings` rather than silently repeating.

---

### 9. `argparse` rather than `click` or `typer`

**Context:** `click` is installed in the environment; `typer` is not.

**Decision:** Standard library `argparse` with subcommands.

**Rejected:**
- **typer** — not installed, and its type-hint magic makes the CLI harder to unit test through `main(argv)`.
- **click** — requires decorating every command and complicates the "parse → dispatch to `cmd_*` function" shape that makes `test_cli.py` a three-line test.

**Trade-off:** More verbose parser construction; zero extra dependency and a trivially testable entry point.

---

### 10. Mode is decided by a rule table (transport + weather), not by an LLM

**Context:** "Should I read or listen?" is the kind of question an LLM could answer.

**Decision:** A four-rule precedence table: hands busy → wet → cold → read-friendly transport → either.

**Rejected:**
- **LLM decides** — adds a network failure mode to a decision with an obvious physical answer, and makes the behaviour untestable (see `test_weather.py`'s 9-case matrix).
- **Ask the user every time** — one more prompt for something they've already implied by typing `--transport drive`.

**Trade-off:** Can't model personal preference (motion sickness on trains, for example). Explicit `--mode` overrides the table entirely.

---

### 11. LLM enrichment is optional and always has a deterministic fallback

**Decision:** `--explain` asks OpenRouter for a one-sentence rationale; with no key, or on any error, it falls back to `template_reason()` built from measured numbers.

**Rejected:**
- **LLM required** — violates the keyless promise and makes offline use impossible.
- **No explanations at all** — the reason line is what makes a plan feel curated rather than computed.
- **LLM-generated durations** — never. Durations are arithmetic or they are fiction.

**Trade-off:** Explanations differ in tone with and without a key. Both are truthful.

---

### 12. Gutenberg via a curated catalogue + streamed prefix, not Gutendex

**Context:** Gutendex is the friendly JSON API for Project Gutenberg, and it was the obvious first choice.

**Decision:** Ship a 20-book `classics.json` (id, title, author, tags) and stream the first ~250 KB of each book's plain text from `gutenberg.org`.

**Rejected:**
- **Gutendex** — returned HTTP 301 then an empty body from this network, repeatedly. A hard dependency on it would make the wind-down act silently empty.
- **Gutenberg's "top 100" HTML page** — scraping with no bs4 installed means regex against a layout that changes.
- **Full book download** — a 1.2 MB file to count words for a 10 minute slot. Streaming and stopping is the same information for 1/5 the bytes.

**Trade-off:** The catalogue is fixed at 20 classics; topic matching is tag-based, not semantic. A `--book-id` escape hatch exists on the source API for future use.

---

### 13. `xml.etree` for arXiv instead of `feedparser`

**Decision:** Parse arXiv's Atom feed with the standard library.

**Rejected:**
- **feedparser** — not installed, and it's a large dependency for one feed shape that changes rarely.
- **Regex extraction from XML** — fragile against arXiv's multi-line titles (which it does produce; see `test_parse_arxiv_normalises_title_and_url`).

**Trade-off:** Handles only the Atom subset arXiv actually emits. Acceptable: this is a single-purpose client.

---

### 14. Reading 230 wpm, narration 150 wpm, plus 8 seconds of friction per item

**Context:** Duration constants determine whether the plan's promise is credible.

**Decision:** 230 wpm for web prose, 150 wpm for narration, 8s overhead per item, both overridable only in code.

**Rejected:**
- **A single 200 wpm constant** — overstates reading speed and understates narration; the same article would be mis-timed in both modes.
- **250 wpm (speed-reading figures)** — flattering and wrong for comprehension of unfamiliar material.
- **Exposing wpm as a CLI flag** — invites users to tune the number until the plan "fits", which defeats the purpose.

**Trade-off:** Averages, not your personal speed. The overhead constant is the honest admission that switching items is not free.

---

### 15. Two dependencies: `requests` and `rich`

**Decision:** Nothing else. `sqlite3`, `json`, `argparse`, `xml.etree`, `concurrent.futures` are stdlib.

**Rejected:**
- **pandas** — used for nothing here; a table of eight rows does not need a dataframe.
- **aiohttp** — the parallel win is captured with a 4-worker thread pool for a handful of requests.
- **textual / prompt_toolkit TUI** — a commute plan is output, not an application. `rich` renders it and exits.

**Trade-off:** No async; a slow source blocks its worker thread for up to the timeout. Fine at this request volume.

---

### 16. Bundled offline corpus as the final fallback

**Decision:** `data/sample_corpus.json` (44 items, real titles, varied lengths) is used for `--offline`, for tests, and automatically if every live source returns nothing.

**Rejected:**
- **Hard failure when offline** — a commute planner that needs the internet to plan your offline commute is a joke.
- **Synthetic generated items** — tests would pass against fake data with no relationship to real content lengths.

**Trade-off:** The corpus grows stale. It is a floor, not a feed, and the live path is the default.
