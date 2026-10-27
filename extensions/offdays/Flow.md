# Flow.md — offdays Execution Flow

## Entry Points

```
offdays (CLI)                    python -m offdays.cli
    │
    ├── --list-countries path
    │   └── api.fetch_countries()
    │       └── urllib.request.urlopen() → JSON → list[dict]
    │
    └── main path (default all other flags)
        ├── api.fetch_holidays(country, year)
        │   └── urllib.request.urlopen() → JSON → list[dict]
        │
        ├── Compute plans
        │   └── planner.compute_plans(holidays, year, budget, top_n)
        │       ├── planner.build_off_set(holidays_raw, year)
        │       │   ├── Parse each holiday's date → Holiday dataclass
        │       │   └── Build set[date]: holidays + all weekends in year
        │       │
        │       ├── planner.find_blocks(off_set, year)
        │       │   └── Sort off-dates → group consecutive → list[list[date]]
        │       │
        │       ├── For each block:
        │       │   ├── planner.gap_before(off_set, block_start)
        │       │   │   └── Walk left counting workdays until off_date or Jan 1
        │       │   ├── planner.gap_after(off_set, block_end)
        │       │   │   └── Walk right counting workdays until off_date or Dec 31
        │       │   └── Enumerate kL, kR combinations for k in 1..budget
        │       │       ├── Build booked set (left dates nearest + right dates nearest)
        │       │       ├── Merge off ∪ booked
        │       │       ├── Sort merged and find maximal run containing this block
        │       │       └── Build Plan dataclass
        │       │
        │       └── Deduplicate & rank
        │           ├── Dedupe by (stretch_start, stretch_end, leave_used)
        │           └── Sort by (-days_off, leave_used) → top_n
        │
        ├── Show free long weekends (optional section before plans)
        │   ├── build_off_set(), find_blocks()
        │   └── Filter blocks with len ≥ 3, show top 5
        │
        └── Print output
            ├── Human mode: formatted text with emoji headers
            └── --json mode: structured JSON with serialized dates
```

---

## Module Dependency Graph

```
offdays/
│
├── cli.py (entry point)
│   ├── depends on: api.py, planner.py
│   └── calls: fetch_holidays(), fetch_countries(), compute_plans(), build_off_set(), find_blocks()
│
├── api.py (Nager.Date client)
│   ├── depends on: urllib.request (stdlib)
│   └── exports: fetch_holidays(country, year), fetch_countries()
│
├── planner.py (core algorithm)
│   ├── depends on: datetime, dataclasses, typing (stdlib)
│   ├── no dependency on api.py — algorithm works with any holiday data
│   └── exports: build_off_set(), find_blocks(), gap_before(), gap_after(), compute_plans()
│       └── Plan, Holiday dataclasses
│
└── __init__.py (package marker + version)
```

---

## Key Data Flow

```
User CLI input
    │  --country US --year 2026 --days 3
    ▼
api.fetch_holidays("US", 2026)
    │
    │  HTTP GET https://date.nager.at/api/v3/publicholidays/2026/US
    ▼
list[dict] ── 10 US federal holidays (global=True)
    │
    ▼
planner.compute_plans(holidays, 2026, leave_budget=3)
    │
    ├─▶ build_off_set() → set[date] (365 days, ~1/3 off)
    │       off = {Jan 1, Jan 3, Jan 4, Jan 10, Jan 11, Jan 17...}
    │
    ├─▶ find_blocks() → list[list[date]]
    │       Block A: [Jan 1]
    │       Block B: [Jan 3, Jan 4]
    │       Block C: [Jan 10, Jan 11]
    │       Block D: [Jan 17, Jan 18, Jan 19]   ← MLK + weekend
    │       ...
    │
    ├─▶ For each block → gap_before/gap_after
    │       Block A (Jan 1, B=1):  L=0, R=1 (Jan 2)
    │       Block D (Jan 17-19, B=3): L=5 (Jan 12-16), R=4 (Jan 20-23)
    │
    ├─▶ For each (k, kL, kR) → merge → stretch → Plan
    │       Block A, k=1, kL=0, kR=1:
    │         booked = {Jan 2}
    │         off∪booked run = Jan 1,2,3,4 → stretch = 4 days
    │         Plan(days_off=4, leave_used=1, ...)
    │
    └─▶ Dedup + rank → top 10
```

---

## Data Type Summary

```
┌─────────────────────────────────────┐
│            urllib.request            │  External
│  urlopen() → bytes → json.loads()   │
└──────────┬──────────────────────────┘
           │ list[dict]               │
           ▼                          ▼
   ┌──────────────────┐     ┌──────────────────────┐
   │ build_off_set()  │     │  compute_plans()      │
   │ → set[date]      │     │  → list[Plan]          │
   │ → list[Holiday]  │     └──────────────────────┘
   └──────────────────┘              │
           │                        ▼
           ▼              ┌────────────────────┐
   ┌──────────────┐       │  cli.py             │
   │ find_blocks()│       │  print() / json.dump│
   │ → list[list] │       └────────────────────┘
   └──────────────┘
           │
           ▼
   ┌──────────────────────────┐
   │ gap_before() → list[date]│
   │ gap_after()  → list[date]│
   └──────────────────────────┘
```

---

## Plan Ranking Function

```
sorted(plans, key=lambda p: (-p.days_off, p.leave_used))
```

Primary sort: **more consecutive days off = better**
Secondary sort: **fewer leave days used = better** (tiebreaker)

This means the #1 plan gives you the absolute longest break, and if two plans give 10 days off, the one requiring fewer leave days ranks higher.

---

## Error Handling Flow

```
fetch_holidays()
    │ HTTP error → raises urllib.error.URLError
    ▼
cli.py catches Exception
    │ → Prints "Error fetching holidays: {msg}" to stderr
    │ → Exit code 1
    ▼

compute_plans(empty_holidays)
    │ No holidays → build_off_set returns empty set of off days
    │ → find_blocks returns empty blocks
    │ → No plans generated → returns []
    ▼
cli.py: prints "No optimal leave plans found."
```

---

## Test Coverage Map

```
test_api.py
    ├── test_fetch_holidays_parses_json    api.fetch_holidays
    ├── test_fetch_holidays_url_format      api.fetch_holidays (URL construction)
    └── test_fetch_countries                api.fetch_countries

test_planner.py
    ├── test_off_set_includes_holidays_and_weekends  build_off_set
    ├── test_jan_1_is_solo_block                     find_blocks
    ├── test_mlk_block_merged_with_weekend           find_blocks
    ├── test_gap_before_jan1                         gap_before
    ├── test_gap_after_jan1_holiday                  gap_after
    ├── test_gap_before_mlk_block                    gap_before
    ├── test_gap_after_mlk_block                     gap_after
    ├── test_jan_1_plan_book_fri                     compute_plans (Jan 2 booking)
    ├── test_thanksgiving_plan_book_friday           compute_plans (Nov 27 booking)
    ├── test_christmas_block_free_weekend            compute_plans (free block)
    ├── test_marathon_plan_book_everything           compute_plans (budget=5)
    ├── test_no_holidays_returns_empty_plans          edge case
    ├── test_one_holiday_scenario                    edge case
    ├── test_plan_deduplication                      dedup logic
    ├── test_plans_sorted_descending                  ranking
    └── test_plan_dataclass_order                     Plan.__lt__
```