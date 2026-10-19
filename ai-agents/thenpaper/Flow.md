# Flow.md — ThenPaper

Execution tracing from entry point to final front page, module dependency
graph, and data flow.

## Module dependency graph

```
thenpaper/
├── __init__.py        version marker
├── __main__.py        python -m thenpaper entry  → cli.main()
├── cli.py             argparse → _parse_date → api.fetch_day / api.simulate_day
│                      → voice.enhance → paper.build_front_page → paper.render
├── api.py             fetches & parses Wikipedia On This Day
│   ├── _get_json/_default_fetch_json   (urllib layer, injectable via set_fetcher)
│   ├── _validate_date, _parse_items, _parse_pages
│   ├── fetch_day → simulate_day (fallback)
│   └── dataclasses: ArticlePage, DayItem, DayFacts
├── paper.py           assembly + rendering
│   ├── rank_events, rank_births, rank_deaths (_recency_bonus, _focus_bonus, _richness)
│   ├── build_front_page → FrontPage
│   ├── _fallback_headline/_fallback_dek/_fallback_twin_intro
│   └── render → _wrap, _bullet, _center, _plain_holiday_text
└── voice.py           LLM editor (injectable via set_poster)
    ├── _has_key, _ask_llm (_post/_default_post_json), _parse_llm_json
    ├── enhance → _ask_llm | _templates
    └── dataclass: Enhancement
```

Dependencies between modules: `cli → api, paper, voice`; `paper → api`;
`voice → api`. No cycles.

## Execution path 1 — live API (default)

```
$ python -m thenpaper 1990/10/19
│
├─ thenpaper/__main__.py: sys.exit(cli.main())
│
├─ cli.main()
│   ├─ build_parser() → args {date:"1990/10/19", theme:"morning", json:False, ...}
│   ├─ _parse_date("1990/10/19")
│   │    └─ parts [1990,10,19] → api._validate_date(10,19) → (10, 19, 1990)
│   ├─ api.fetch_day(10, 19)
│   │    ├─ _validate_date(10, 19)                # guards 10/19
│   │    ├─ for kind in (events,births,deaths,holidays,selected):
│   │    │    ├─ _get_json(BASE_URL/kind/10/19)
│   │    │    │    └─ _default_fetch_json(url) → (200, {"events":[...]})
│   │    │    ├─ live_hits += 1
│   │    │    └─ _parse_items(raw, singular_kind)
│   │    │         └─ _parse_pages(raw_pages) → [ArticlePage(title, url)]
│   │    └─ live_hits>0 → DayFacts(source="live")   # all 5 facets populated
│   │
│   ├─ voice.enhance(facts, 10, 19, allow_llm=True)
│   │    ├─ _has_key() → ("ANTHROPIC_API_KEY","anthropic") [if set]
│   │    ├─ _ask_llm(facts, 10, 19, key, provider)
│   │    │    ├─ _digest(facts) → compact text of top events/births/deaths/holidays
│   │    │    ├─ _post(ANTHROPIC_URL, headers, payload) → JSON string
│   │    │    └─ _parse_llm_json → Enhancement(headline,dek,twin_intro,used_llm=True)
│   │    └─ on ANY exception: Enhancement(..., used_llm=False) from _templates
│   │
│   ├─ paper.build_front_page(facts, 10, 19, theme="morning",
│   │                        enhancement=enh, events_limit=6, focus_year=1990)
│   │    ├─ paper.rank_events(facts.events, limit=6, focus_year=1990)
│   │    │    └─ key = (-|year-1990|, recency_bonus, year, richness) → sorted desc
│   │    ├─ lead = facts.selected[0] if selected else ranked[0]
│   │    ├─ twins = rank_births(facts.births, limit=3)
│   │    ├─ deaths = rank_deaths(facts.deaths, limit=2)
│   │    ├─ holidays = [_plain_holiday_text(h) for h in facts.holidays[:4]]
│   │    └─ → FrontPage(date_label, headline=enh.headline, ...)
│   │
│   └─ paper.render(page, width=74)
│        ├─ masthead: ╔═╗ rows via _center(title/tagline/dateline)
│        ├─ headline/_wrap + dek centered
│        ├─ lead story → BORN THIS DAY → MORE FROM THE FRONT PAGE
│        ├─ IN MEMORIAM → ON THE CALENDAR
│        └─ footer: SOURCE: Wikipedia On This Day (live)
│
└─ stdout: ASCII front page   (or --json → json.dumps(page.to_dict(), indent=2))
```

## Execution path 2 — offline / simulated

```
python -m thenpaper 12/25 --offline
│
├─ cli.main() → args.offline=True → api.simulate_day(12, 25)
│    ├─ api._validate_date(12, 25)
│    └─ DayFacts(events=[1969 moon, 1945 computer, 1519 voyage],
│                births=[1984 reader, 1922 novelist],
│                holidays=[World Make-Believe Day], source="simulated")
└─ same voice/paper/render pipeline → paper always prints
```

Same path triggers automatically inside `fetch_day` when every endpoint call
raises or returns non-200 (`live_hits == 0`).

## Execution path 3 — JSON contract

```
python -m thenpaper 8/15 --json
└─ cli.main() → paper.build_front_page(...) → FrontPage
     └─ json.dumps(page.to_dict(), indent=2, ensure_ascii=False)
        {
          "month": 8, "day": 15, "date_label": "Saturday, August 15",
          "headline": "...", "dek": "...", "lead": {...DayItem...},
          "events": [...], "twins": [...], "deaths": [...],
          "holidays": [...], "source": "live", "focus_year": null, ...
        }
```

## Data flow (user input → output)

```
 "1990/10/19" ──parse──▶ (month=10, day=19, focus_year=1990)
      │
      ▼
 Wikipedia REST ──fetch──▶ DayFacts(events[], births[], deaths[],
 /onthisday/{kind}/10/19        holidays[], selected[], source)
      │
      ▼
 rank_events / rank_births ──▶ lead, events, twins, deaths, holidays
      │
      ▼
 voice.enhance ──▶ Enhancement(headline, dek, twin_intro)  [LLM or templates]
      │
      ▼
 build_front_page ──▶ FrontPage ──render──▶ ASCII newspaper on stdout
```

## Test → code map

| Test | Exercises |
|------|-----------|
| `test_api.py` | `fetch_day`, `_parse_items`, `_validate_date`, URL padding, simulated fallback |
| `test_paper.py` | `rank_events`, `rank_births`, `build_front_page`, `render`, `_wrap` |
| `test_voice.py` | `enhance`, `_ask_llm`, `_parse_llm_json`, `_digest`, template fallback |
| `test_cli.py` | `_parse_date`, `main` (offline JSON/ASCII/theme), exit codes |