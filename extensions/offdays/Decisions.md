# Decisions.md — offdays

Architectural decisions made while building the offdays leave optimizer.

---

## 1. Pure Python stdlib vs frameworks

- **Chosen:** Python stdlib-only (`urllib`, `datetime`, `argparse`, `json`)
- **Rejected:** `requests`, `click`, `httpx`, `rich`
- **Why:** Extension category mandate — zero-dependency utilities that run anywhere. stdlib fetches JSON, parses dates, and formats output without a single `pip install`. No risk of dependency rot.

## 2. Nager.Date over other holiday APIs

- **Chosen:** Nager.Date (`date.nager.at` — free, no key)
- **Rejected:** Calendarific (limited free tier), Google Calendar API (OAuth), Abstract API (paid)
- **Why:** Free, zero-auth, 200+ countries, JSON format, includes weekend subnational data. The only free holiday API that Just Works without signup.

## 3. Global-only holiday filter by default

- **Chosen:** Filter to `global=True` holidays (national public holidays)
- **Rejected:** Including subnational holidays (county/state-specific), including observances
- **Why:** Most users want national holidays. Subnational creates noise and misses the "best leave plan" for the general case. Users in specific states can run with `--holidays-only` filters if needed. Keeping the algorithm simple avoids date-set explosion from 50 overlapping state holidays.

## 4. Consecutive block expansion algorithm over combinatorial enumeration

- **Chosen:** Find off-blocks → compute gaps → enumerate leave-days per gap
- **Rejected:** Brute-force all C(365, N) combinations, greedy day-by-day scoring
- **Why:** Enumerating per-gap is O(blocks × K²) — negligible even for 10 blocks and K=5. Brute-force C(365,5) is 50B combinations — infeasible. Greedy misses optimal when bridging merges two blocks.

## 5. Gap expansion via set merging over formula

- **Chosen:** Merge `off ∪ booked`, sort, find runs, measure stretch containing block
- **Rejected:** Recursive expansion with formula `B + kL + kR + merge_left_block + merge_right_block`
- **Why:** Set merging is correct by construction — handles multi-block merges, edge cases at year boundaries, and adjacency without special-case code. Formula-based had bugs with triple-block bridges.

## 6. Deduplication by (stretch_start, stretch_end, leave_used)

- **Chosen:** Dedupe on stretch coordinates + leave count
- **Rejected:** Dedupe on leave_dates tuple, dedupe on days_off
- **Why:** The same stretch can be achieved by different leave-date combinations (e.g. book left 1 vs right 1 around a block). Keeping one plan per (stretch, leave_used) avoids clutter while preserving all useful options.

## 7. Plan dataclass with custom ordering

- **Chosen:** `Plan` as a `@dataclass(order=True)` with `__lt__` that sorts by `(-days_off, leave_used)`
- **Rejected:** External key function in sorted(), separate ranking function
- **Why:** Making the dataclass self-ordering means `sorted(plans)` always does the right thing. Less code, fewer bugs.

## 8. CLI output: human-readable table + optional JSON

- **Chosen:** Dual output: rich text by default (with emoji headers, bullet lists), `--json` for scripts
- **Rejected:** Pure table view, pure Markdown
- **Why:** The primary user is a person at a terminal who wants quick scan-ability. JSON is for integration — `jq` users know how to find it.

## 9. Free 3+ day weekend alerts as bonus section

- **Chosen:** Show a "Free long weekends" section with 0-leave-day blocks ≥3 consecutive off days
- **Rejected:** Only showing plans that require leave, merging free weekends into plan list as "0 leave" plans
- **Why:** Separating the free weekends from the paid-leave plans reduces cognitive load. Users see immediately what they get for free before deciding what to book.

## 10. Holiday coverage tracking in Plan

- **Chosen:** Include `holidays_covered` field listing holiday names in each stretch
- **Rejected:** Only showing numeric stats (days_off, leave_used)
- **Why:** Users care *which* holidays they're covering — "is this the Thanksgiving plan or the Christmas plan?" Names make the output actionable.

## 11. Offline/demo mode excluded from v1

- **Chosen:** No built-in holiday fixture for offline demo
- **Rejected:** Bundling sample JSON for US 2026 + key countries
- **Why:** Nager.Date is fast and free — there's no reason to go offline. Bundling sample data would bloat the package and diverge from reality. Tests use mocked HTTP so they run offline already.

## 12. Country emoji flags from code

- **Chosen:** Compute flag emoji from ISO code via Unicode regional indicators
- **Rejected:** Hardcoded emoji map, skip flags entirely
- **Why:** Computing from code covers all 200+ countries without maintenance. Regional indicators (U+1F1E6..U+1F1FF) are universally supported.

## 13. Test strategy: mocked HTTP + pure logic

- **Chosen:** `@patch('urllib.request.urlopen')` for API tests; fixture data for planner tests
- **Rejected:** Live API tests, golden-file tests
- **Why:** The planner is the complex part — it needs thorough unit testing. The API client is a thin JSON wrapper. Mocking keeps tests fast, deterministic, and offline-capable.

## 14. CLI entry via both `python -m` and console script

- **Chosen:** `pyproject.toml` with `[project.scripts]` (or entry point) for `offdays` command + `python -m offdays.cli`
- **Rejected:** Single `main.py` at project root
- **Why:** Package-installed CLI is the expected UX for a tool. Working directory independence matters — a root script only works from the project dir.

---

**Decision count:** 14