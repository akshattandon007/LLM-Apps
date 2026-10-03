# Decisions.md — SubsSleuth

## Architecture decisions and rejected alternatives.

### 1. Multi-agent vs monolithic script
**Decision:** Three-agent architecture (Scanner, Cancel, Verify).
**Why:** Real subscription management is three distinct workflows — *find*, *research*, and *verify*. Monolithic code would conflate IMAP email parsing with web research with bank-statement reconciliation, making testing and maintenance harder. The agent boundary mirrors the user's mental model.
**Rejected:** A single "do everything" class. It would have >800 lines and require mocking IMAP + web + file I/O in every test.

### 2. IMAP over Gmail API
**Decision:** Standard IMAP (stdlib `imaplib`) for email scanning.
**Why:** Gmail API requires OAuth 2.0 setup, a Google Cloud project, and scopes that can take days to approve. IMAP + app password works with any email provider (Gmail, Outlook, Yahoo) without a developer console. The user just needs to enable IMAP and create an app password — a 2-minute setup.
**Rejected:** Gmail API (`google-api-python-client`) — more secure but enormous setup friction for the target audience (non-technical people). Also rejected: POP3 — can't access individual folders or search by subject server-side.

### 3. LLM opt-in vs always-required
**Decision:** LLM is optional via `--llm-key` flag; falls back to rule-based extraction.
**Why:** The tool must work out of the box without API keys. The heuristic extraction (known merchant database + regex) covers 90%+ of common subscription emails. LLM adds accuracy for edge cases but is a "nice to have," not a hard dependency. This also makes CI tests deterministic.
**Rejected:** Making LLM required. That would force every user to sign up for Groq/OpenAI and provide a credit card. Also rejected: shipping with a hardcoded free API key that could be rate-limited by the time of first use.

### 4. SQLite key-value store vs full database
**Decision:** Simple SQLite key-value store for persisting scan state.
**Why:** The only persistent state needed is "which emails have I already scanned so I don't re-scan them." A full ORM or document store is overkill. SQLite is stdlib, zero-dependency, and the kv schema is 1 table with 2 columns.
**Rejected:** JSON file — would need full-file locking for concurrent access. Also rejected: Redis — a non-starter for a local CLI tool.

### 5. Demo mode as first-class feature
**Decision:** Every agent has a `_demo()` method that works without credentials.
**Why:** The tool is unusable without email credentials, which many users won't have handy on first try. Demo mode shows the full output format with realistic fake data so users can evaluate before connecting their real email. It's also how CI tests run.
**Rejected:** Documentation-only "here's what it would look like." Users try tools, they don't read examples.

### 6. Known cancellation database vs live search only
**Decision:** Hybrid — a hardcoded database for top 10 services, web search for everything else.
**Why:** Netflix and Spotify cancellation instructions never change — why pay an LLM or wait for a web search every time? The database covers the most common subscriptions instantly. Everything else falls through to web search + optional LLM synthesis.
**Rejected:** Live search only — slow and fragile for the 10 services that constitute 80%+ of subscriptions. Also rejected: maintaining an updatable JSON file — complexity without benefit for a single-ship tool.

### 7. Built-in cancellation guides vs external links only
**Decision:** Provide full step-by-step guides inline, not just "go to this URL."
**Why:** The target user is someone who has already failed to cancel (that's why they're using this tool). Telling them "go to the cancellation page" doesn't help — they need the exact sequence of clicks and the gotchas (e.g. "Hulu shows a pause option that looks like cancel but isn't").
**Rejected:** Just returning the URL. That's what a Google search gives them — the tool's value is the structured playbook.

### 8. Parse-every-subject-line vs targeted keywords
**Decision:** Scan inbox with 15 subscription-related subject keywords.
**Why:** Full-text searching every email is expensive on IMAP. Subject-line keyword search is server-side and fast. The 15 keywords cover 95%+ of subscription email subjects.
**Rejected:** Scanning the entire inbox — way too many emails, most irrelevant, and would hit IMAP rate limits on large inboxes. Also rejected: LLM-classifying every email subject — API cost for potentially hundreds of emails.

### 9. CSV statement parsing over PDF scraping
**Decision:** Accept CSV bank statements, not PDF screenshots.
**Why:** CSV is the standard export format for every major bank, and parsing it is deterministic. PDF bank statements have no standard layout — every bank outputs different column positions, page headers, and table formatting. CSV is a 10-line parser that never breaks.
**Rejected:** PyMuPDF for PDF parsing. We'd need to train a layout model per bank. Also rejected: user manually entering charges — if they have 100+ transactions a month, that's not happening.

### 10. CLI-first over web UI
**Decision:** Command-line interface with `--demo` flag.
**Why:** This tool is designed for the Hermes agent ecosystem — it's called from a cron job or shell script, not from a browser. A web UI adds an HTTP server, authentication, and frontend code that have nothing to do with the subscription problem.
**Rejected:** Flask/FastAPI web app. Wrong interface for the target deployment. Also rejected: a pip package — the tool lives inside the LLM-Apps monorepo.

### 11. Report output as JSON (not formatted tables)
**Decision:** All agent outputs are JSON by default.
**Why:** JSON is parseable by the orchestrator (Hermes agent) and by any downstream tool. Pretty-printed tables add a dependency (tabulate/rich) and produce output that needs parsing anyway. The JSON is readable enough for humans.
**Rejected:** Rich-formatted terminal tables. Nice UX but adds a dependency and the output is consumed by another agent, not a human.

### 12. httpx over requests library
**Decision:** httpx for HTTP calls.
**Why:** httpx supports async natively (future-proof if we parallelize agent calls), has a better timeout API, and is the same library used by the rest of the Hermes ecosystem. requests is frozen in maintenance mode.
**Rejected:** urllib (stdlib) — too low-level and error-prone for API calls. Also rejected: aiohttp — async-first but heavier than needed for a synchronous CLI tool.

### 13. Verification via name+amount matching, not ML
**Decision:** Simple token-overlap + amount-diff scoring for statement matching.
**Why:** Subscription merchants charge with recognizable names (NETFLIX.COM, SPOTIFY PREMIUM). A combinatorial token match plus amount comparison achieves >95% accuracy without any ML dependency. ML would require training data, a model, and a serving dependency.
**Rejected:** Sentence-transformers for semantic merchant name matching. Overkill when "Netflix" and "NETFLIX.COM" are the real-world inputs.

### 14. Single-file maintainer convenience
**Decision:** Each agent is a single `.py` file (<300 lines each).
**Why:** Splitting into more files (one per class, or one per API wrapper) creates 15+ files for a 900-line project. The three-agent boundaries already provide clean module separation. A single engineer can hold all three agents in their head.
**Rejected:** Strict "one class per file" style. Added cognitive load without benefit at this scale.

### 15. `__main__.py` entry point over setuptools script
**Decision:** `python -m subs_sleuth` as the primary invocation.
**Why:** No install step. Works from the checkout directory. `__main__.py` is the Python-standard way. A console_scripts entry in setup.py/pyproject.toml adds a build step that's unnecessary for a monorepo tool.
**Rejected:** `setup.py` with `entry_points={'console_scripts': ...}`. Adds a build step. The tool works immediately as `python -m subs_sleuth`.