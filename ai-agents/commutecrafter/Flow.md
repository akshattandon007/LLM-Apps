# Flow — CommuteCrafter

Function-level traces of every path through the system, plus the module graph.

## Module dependency graph

```
                        ┌──────────────┐
                        │  __main__.py │
                        └──────┬───────┘
                               │ main()
                        ┌──────▼───────┐
                        │   cli.py     │
                        └──┬──┬──┬──┬──┘
             ┌─────────────┘  │  │  └──────────────┐
             │                │  │                 │
      ┌──────▼──────┐  ┌──────▼──▼──────┐  ┌───────▼──────┐
      │  sources/   │  │   planner.py   │  │  weather.py  │
      └──┬──┬──┬──┬─┘  └───┬────────┬───┘  └──────────────┘
         │  │  │  │        │        │
         │  │  │  │   ┌────▼───┐ ┌──▼──────┐
         │  │  │  │   │timing.py│ │models.py│◄────────────┐
         │  │  │  │   └────────┘ └──▲──────┘             │
         │  │  │  │                │                     │
         │  │  │  └──► gutenberg.py│                     │
         │  │  └─────► hackernews.py                     │
         │  └────────► arxiv.py                           │
         └───────────► wikipedia.py                       │
                          │                              │
   cli.py ──► store.py ───┘        render.py ────────────┘
   cli.py ──► llm.py ──────────────┘
```

**Rules the graph encodes**

- `models.py` and `timing.py` import nothing from the project — they are pure and safe to test in isolation.
- `planner.py` depends only on `models` + `timing`. It has **no network, no disk, no clock**. That is why plan output is deterministic and testable.
- Sources depend on `models` only. They never know a plan exists.
- `cli.py` is the only module that composes sources + weather + planner + store + render.
- `store.py`, `render.py`, `weather.py`, `llm.py` are leaves: nothing imports them except `cli.py` (and tests).

---

## 1. `commutecrafter plan` — the main path

```
main(argv)
└─ _build_parser().parse_args(argv)
   └─ cmd_plan(args)
      │
      ├─ _parse_topics("history,philosophy")
      │     → ["history", "philosophy"]
      │
      ├─ _gather_multi(topics, offline=False, per_topic=10)
      │   └─ for topic in topics[:5]:
      │        _gather(topic, offline=False)
      │        ├─ build_sources()                      # sources/__init__.py
      │        │    → [WikipediaSource, ArxivSource, HackerNewsSource, GutenbergSource]
      │        ├─ for src in sources:
      │        │    src.fetch(topic)
      │        │    └─ BaseSource._get(url, params)     # 2 retries, 0.6s/1.2s backoff
      │        │       → requests.Session.get(...)
      │        ├─ on SourceError → warning collected, loop continues
      │        ├─ cross-source URL dedupe
      │        └─ if empty → _load_offline(topic)       # graceful fallback
      │   └─ dedupe(all_items)                          # sources/base.dedupe
      │
      ├─ Store()                                        # store.py
      │   ├─ default_db_path()                          # $COMMUTECRAFTER_DB or XDG
      │   ├─ executescript(SCHEMA)                      # plans, served
      │   └─ recently_served(days=14) → set[str]        # lowercase URLs
      │
      ├─ weather_for_city(args.city)   [only if --city and not --no-weather]
      │   ├─ geocode(city)      → open-meteo geocoding API
      │   ├─ current_weather(lat, lon) → open-meteo forecast API
      │   ├─ describe_code(code) → WMO_CODES lookup
      │   └─ on ANY exception → returns None (weather is never fatal)
      │
      ├─ recommend_mode(weather, transport)             # weather.py rule table
      │      hands busy → wet → cold → read-friendly → either
      │
      ├─ build_plan(items, minutes, mode, tolerance, exclude_urls, transport, weather)
      │   │                                              # planner.py — pure
      │   ├─ clamp_minutes(minutes)                     # 2.0 … 240.0
      │   ├─ wpm_for_mode(mode)                          # 230 read / 150 listen
      │   ├─ PacingProfile.budgets(target_seconds)
      │   │      warm = round(t × 0.18)
      │   │      wind = round(t × 0.20)
      │   │      core = t − warm − wind                   # residue lands in core
      │   │
      │   ├─ dedupe + exclude_urls filter
      │   │
      │   ├─ for segment in (warm-up, core, wind-down):
      │   │    _fill_segment(name, budget, items, wpm, used_titles, source_counts, tolerance)
      │   │    ├─ _candidates()  → filter by SEGMENT_MAX_SECONDS, drop <20s
      │   │    │                  sort by (−_score, duration, title)
      │   │    ├─ loop while remaining ≥ 45s and items < MAX_ITEMS_PER_SEGMENT:
      │   │    │    pick min |remaining − duration| among viable
      │   │    │    (respects MAX_PER_SOURCE=2, used_titles)
      │   │    │    → ScheduledItem(seconds=_duration(item, wpm), fraction=1.0)
      │   │    └─ returns chosen list
      │   │    → Segment(name, budget_seconds, items)
      │   │
      │   ├─ BALANCE (too short):
      │   │    while core exists and guard < 3 and gap > tolerance:
      │   │      _best_padding(items, used, counts, wpm, gap, tolerance)
      │   │      ├─ respect_caps=True first; retry with False if pool empty
      │   │      ├─ pick min |duration − gap|
      │   │      └─ trim to gap: fraction = take/duration (≥0.35 else None)
      │   │      → append to CORE segment (never after the wind-down)
      │   │
      │   └─ BALANCE (too long):
      │        over = total − (target + tolerance)
      │        walk segments reversed, items reversed:
      │          keep = seconds − over
      │          if keep ≥ 45s and keep/seconds ≥ 0.35 → _rescale(sched, keep, wpm)
      │          else → drop item, over −= seconds
      │        drop empty segments
      │
      ├─ enrich_plan(plan, limit=3)     [if --explain and a key is present]
      │   └─ explain(sched, plan) → openrouter chat completion
      │        └─ on missing key / HTTP ≥400 / exception → template_reason(sched)
      │   else apply_template_reasons(plan) → template_reason per item
      │
      ├─ Store.record_plan(plan)        [unless --dry-run]
      ├─ Store.mark_served([(url, title, source) …])
      │
      └─ render_plan(plan) or print(plan_json(plan))
```

### Timing invariants asserted by the suite

- `sum(PacingProfile.budgets(t).values()) == t` for every window
- `abs(plan.total_seconds − target) ≤ tolerance` for 8/11/15/22/30/45/60 minute windows
- every `ScheduledItem.fraction ∈ (0, 1]`, and `≥ 0.35` when partial
- `MAX_PER_SOURCE` respected (padding may exceed it by design, and says so)

---

## 2. `commutecrafter search` — inventory without planning

```
main(argv) → cmd_search(args)
├─ _parse_topics(args.query)
├─ _gather_multi(topics, offline, per_topic=8)     # same pipeline as above
├─ filter by --source
├─ slice to --limit
└─ render_items(items)  or  json.dumps([i.to_dict() …])
```

---

## 3. `commutecrafter history` / `stats` / `clear`

```
cmd_history      → Store().history(limit) → render_history(rows)
                     └─ SELECT plans ORDER BY id DESC LIMIT ? → json.loads(payload)
cmd_stats        → Store().stats() → COUNT(*) on plans and served
cmd_clear        → Store().clear() → DELETE FROM served; DELETE FROM plans
```

---

## 4. Source internals

### Wikipedia (`sources/wikipedia.py`)

```
fetch(topic, limit)
├─ _search(topic, limit, sentences=4)
│   └─ BaseSource._get(API, {generator:search, prop:extracts, exintro:1, explaintext:1})
│      └─ parse_wikipedia(payload) → [ContentItem(words=len(intro.split()))]
└─ ThreadPoolExecutor(max_workers=4).map(_full, titles)
    └─ _full(title)
        └─ BaseSource._get(API, {prop:extracts, exlimit:1, titles:title})
           └─ parse_full_extract(payload) → (word_count, excerpt_280)
    → item.words = max(intro_words, full_words)
```

Why two stages: intros are ~200 words (too short for a core act); full text gives honest durations. Failure of a single `_full` call silently keeps the intro length.

### arXiv (`sources/arxiv.py`)

```
fetch(topic, limit)
└─ BaseSource._get("https://export.arxiv.org/api/query", {search_query, max_results})
   └─ parse_arxiv(resp.text)
      └─ ET.fromstring → for entry: title/summary/id/published
         words = len(summary.split())   # <30 words → dropped
```

### Hacker News (`sources/hackernews.py`)

```
fetch(topic, limit)
└─ BaseSource._get(Algolia, {query, tags:"ask_hn", hitsPerPage})
   └─ parse_hackernews(payload)
      ├─ hit.story_text → clean_html() (strip <p>, tags, unescape entities)
      ├─ keep only posts with ≥120 words  (link posts have no reading length)
      └─ url = https://news.ycombinator.com/item?id={objectID}
```

### Gutenberg (`sources/gutenberg.py`)

```
fetch(topic, limit)
├─ load_catalog()            → data/classics.json (20 entries)
├─ rank_catalog(catalog, topic)
│     score = 2×(topic∩tags) + (topic∩title words); stable sort
└─ for entry in ranked[:limit]:
     _stream_prefix(id, max_bytes=250_000)
     └─ session.get(stream=True) → iter_content(16384) until byte cap
     parse_gutenberg_text(raw, words_limit=6000)
     ├─ strip_boilerplate()  → cut at *** START/END OF THE PROJECT GUTENBERG EBOOK ***
     └─ words[:limit] → (count, first 60 words)
     → ContentItem(category="reflective")
```

One failing book never kills the plan: the loop `continue`s.

---

## 5. Weather path (`weather.py`)

```
weather_for_city(city)
├─ geocode(city)          → {city, country, latitude, longitude}  (or None)
├─ current_weather(lat,lon)→ {temp_c, precipitation_mm, wind_kmh, code, description}
└─ returns {**place, **conditions} or None on any exception

recommend_mode(weather, transport)
├─ transport ∈ HANDS_BUSY      → ("listen", "<transport>: eyes and hands are busy")
├─ precipitation_mm ≥ 0.2      → ("listen", "wet weather — hands stay free")
├─ temp_c ≤ 2                  → ("listen", "gloves-on cold")
├─ transport ∈ READ_FRIENDLY   → ("read", "<transport>: hands free")
└─ otherwise                   → ("either", "conditions allow reading or listening")
```

`cli.cmd_plan` coerces `either → read` before planning, because a plan must pick a wpm constant.

---

## 6. Persistence (`store.py`)

```
Store.__init__(path)
├─ default_db_path()  → $COMMUTECRAFTER_DB | $XDG_DATA_HOME/commutecrafter | ~/.local/share/…
├─ mkdir(parents=True)
└─ executescript(SCHEMA)
     plans(id, created_at, minutes, mode, transport, total_seconds, payload JSON)
     served(url PRIMARY KEY, title, source, served_at)  + index on served_at

record_plan(plan)     → INSERT plans(payload=json.dumps(plan.to_dict()))
mark_served(tuples)   → INSERT OR REPLACE served, url lowercased, stamp = now
recently_served(days) → SELECT url WHERE served_at ≥ now − days×86400
history(limit)        → SELECT plans ORDER BY id DESC → payload re-parsed
stats()               → COUNT(*) plans, served
clear()               → DELETE served; DELETE plans
```

URLs are stored lowercased and compared lowercased in `build_plan`, so exclusion is case-insensitive end to end.

---

## 7. Rendering (`render.py`)

```
render_plan(plan, console)
├─ _fit_badge(plan)          → "✔ fits (+0s)" | "✘ off by 3:12"
├─ Panel(header: window, planned, mode, status)
├─ weather_note(weather, mode)        [if weather present]
├─ for segment in plan.segments:
│    Table(title = icon + name + budget)
│    rows: #, format_duration(seconds), title (+ [n%] if partial), source
│    then per item: url line + reason line
├─ warnings block
└─ summary: N items across M sources, tolerance

plan_json(plan) → json.dumps(plan.to_dict(), indent=2)
```

`Plan.to_dict()` is the single serialisation surface — tests assert against it, so CLI JSON and library JSON can never drift.

---

## 8. Failure behaviour (what happens when things break)

| Failure | Handling | User sees |
|---|---|---|
| One source raises | warning collected, other sources continue | plan, plus a stderr line |
| All live sources empty | automatic `_load_offline()` | plan from bundled corpus |
| Wikipedia full-text call fails | intro word count kept | slightly short item, no error |
| Gutenberg book unreachable | `continue` to next book | fewer wind-down candidates |
| Weather API fails | `weather_for_city` returns None | plan without weather note |
| No OpenRouter key | `template_reason()` | numeric reason instead of prose |
| Pool too small for window | `warnings.append("Only Ns of fitting content…")` | plan flagged `fits: false` |
| DB unwritable | sqlite3 exception propagates to CLI | non-zero exit, clear traceback |
