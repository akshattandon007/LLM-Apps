# Flow — triallight

## Module Dependency Graph

```
main.py
  ├── clinicaltrials.py    (via sys.path: src/)
  │     ├── models.py
  │     └── requests
  ├── geo.py
  │     └── requests
  ├── llm.py
  │     ├── models.py
  │     └── openai
  ├── models.py
  └── pubmed.py
        ├── models.py
        └── requests
```

## Call Chain (Runtime)

### 1. CLI Entry — `main.py`

```
main()
  └─ run_triallight(args)
       │
       ├─ geo.geocode_city(city)         # optional — resolves city → lat/lon
       │    └─ requests.get(Open-Meteo Geo URL)
       │    └─ returns dict {lat, lon, name, country, region} | None
       │
       ├─ clinicaltrials.search_studies(condition, page_size, location_query)
       │    └─ requests.get(ClinicalTrials.gov API v2 endpoint)
       │    └─ returns raw dict response
       │
       ├─ clinicaltrials.parse_studies(api_response)   # transforms API JSON → list[StudyProtocol]
       │    └─ for each study in api_response['studies']:
       │         ├─ Location(city, state, country, zip)
       │         ├─ EligibilityCriterion(category, text)
       │         └─ StudyProtocol(nct_id, brief_title, ..., eligibility_criteria, ...)
       │
       ├─ pubmed.search_articles(condition, max_results)  # optional (--pubmed)
       │    └─ requests.get(PubMed ESearch)
       │    └─ requests.get(PubMed EFetch)    # after 0.4s delay
       │    └─ returns list[PubMedArticle]
       │
       ├─ llm.generate_search_summary(search_result)      # if api_key
       │    └─ build_client()
       │    │    └─ OpenAI(api_key, base_url) from env vars
       │    └─ openai.chat.completions.create(model, messages)
       │    └─ returns markdown string
       │
       └─ for each study in studies[0:max_trials]:
            ├─ llm.generate_study_digest(study, articles)  # if api_key
            │    └─ build_trial_prompt(study, articles)
            │    │    └─ formats study data + criteria + articles → prompt string
            │    └─ openai.chat.completions.create(model, messages)
            │    └─ returns markdown string (4-section digest)
            │
            └─ _show_raw_study(study)  # fallback (--raw mode)
                 └─ prints structured fields to console
```

### 2. Data Flow

```
User Input (condition + city)
    │
    ▼
[Search Phase]
    ├─ ClinicalTrials.gov API ──► raw JSON ──► parse_studies() ──► list[StudyProtocol]
    ├─ Open-Meteo Geo API ──► geocode_city() ──► lat/lon for location context
    └─ PubMed E-utilities ──► search_articles() ──► list[PubMedArticle]
    │
    ▼
[Augment Phase]  (if api_key set)
    ├─ build_trial_prompt(study, articles) ──► structured prompt
    └─ OpenAI-compatible API ──► markdown digest
    │
    ▼
[Display Phase]
    Rich console output (Panels, Markdown, Rules)
```

## Key File Functions

| File | Functions | Purpose |
|------|-----------|---------|
| `main.py` | `main()`, `run_triallight()`, `_show_raw_study()` | CLI orchestration, user I/O |
| `src/clinicaltrials.py` | `search_studies()`, `fetch_study_detail()`, `parse_studies()` | CT.gov API v2 search + parse |
| `src/pubmed.py` | `search_articles()`, `_parse_pubmed_xml()` | PubMed search + XML parse |
| `src/geo.py` | `geocode_city()`, `format_location_query()` | City → coordinates, API query building |
| `src/llm.py` | `build_client()`, `build_trial_prompt()`, `generate_study_digest()`, `generate_search_summary()` | LLM prompt engineering + API call |
| `src/models.py` | `StudyProtocol`, `PubMedArticle`, `EligibilityCriterion`, `Location`, `SearchResult`, `StudyStatus` | Data classes (no logic) |

## Error Handling

```
clinicaltrials.search_studies() ──► requests.exceptions.RequestException
                                         │
                                         ▼
run_triallight() catches Exception ──► Console.print("[red]Error: {e}[/]") ──► return 1

pubmed.search_articles() ──► Exception
                                   │
                                   ▼
run_triallight() catches ──► Console.print("⚠️ PubMed fetch failed") ──► continues with empty articles

llm.generate_*() ──► Exception
                          │
                          ▼
run_triallight() catches ──► falls back to _show_raw_study()
```

## Entry Points

- `python main.py <condition>` — CLI search
- `python -m pytest tests/` — run unit tests (mock-based, no network)