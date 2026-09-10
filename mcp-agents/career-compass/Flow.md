# Flow.md — Execution Trace

## Call chain: MCP Tool → Service → Output

```
Agent / CLI
    │
    ▼
MCP Tool (server.py)          ← FastMCP decorator registers the tool
    │
    ▼
Service function               ← src/salary.py, industries.py, skills.py, etc.
    │
    ├── databases.py           ← Occupation lookups + COL data
    │     ├── OCCUPATIONS dict (25 entries, BLS-sourced)
    │     └── COST_OF_LIVING dict (25 ZIP codes)
    │
    ├── Optional: BLS API      ← httpx POST to api.bls.gov (when BLS_API_KEY set)
    │
    ▼
Result model                   ← Pydantic model (SalaryResult, IndustryResult, etc.)
    │
    ▼
Formatted string               ← returned to the AI agent
```

## Dependency Graph

```
src/models.py         ← no deps (pure Pydantic)
src/databases.py      ← depends on src/models.py
src/salary.py         ← depends on src/databases.py, src/models.py
src/industries.py     ← depends on src/databases.py, src/models.py
src/skills.py         ← depends on src/databases.py, src/models.py
src/paths.py          ← depends on src/databases.py, src/models.py
src/offers.py         ← depends on src/databases.py, src/models.py
src/server.py         ← depends on all ↑ + mcp SDK, fastapi, uvicorn
src/main.py           ← depends on all ↑ + dotenv
tests/conftest.py     ← depends on src/models.py
tests/test_smoke.py   ← depends on all service modules + src/server.py
```

## Per-tool trace

### salary_by_role(job_title, zip_code)

```
salary_by_role_tool()
  → salary_by_role(job_title, zip_code)
      → find_occupation_by_title(job_title)         # databases.py: fuzzy match
          → OCCUPATIONS dict lookup
      → find_cost_of_living(zip_code)               # databases.py: ZIP → COL
          → COST_OF_LIVING dict lookup
      → [if BLS_API_KEY] _fetch_bls_wage(series_id) # httpx POST to BLS API
      → SalaryResult(median_wage, p10, p90, col_index, adjusted)
      → formatted string
```

### growing_industries(region)

```
growing_industries_tool()
  → growing_industries(region)
      → INDUSTRY_DATA dict (8 industries)
      → [if region] filter by key_regions match
      → sort by projected_growth_rate desc
      → IndustryResult(industries[])
      → formatted string
```

### skills_gap(current_title, target_title)

```
skills_gap_tool()
  → skills_gap(current_title, target_title)
      → find_occupation_by_title() for both roles    # for education info
      → SKILL_MAPS matching (cur_pat in current, tar_pat in target)
      → [if no match] _generate_generic_gaps()       # education + domain gaps
      → SkillsGapResult(gaps[])
      → formatted string
```

### career_path(entry_job, years)

```
career_path_tool()
  → career_path(entry_job, years)
      → _map_career_family(title_lower)              # keywords → family key
      → PROGRESSION_MAPS[family_key]                 # 6 career ladders
      → filter steps where years_to_reach <= years
      → CareerPathResult(steps[])
      → formatted string
```

### compare_offer(salary, benefits, location, ...)

```
compare_offer_tool()
  → compare_offer(salary, benefits, location, ...)
      → JobOffer model (base + bonus + equity + relocation + benefits)
      → _total_comp(offer)                            # sum all components
      → find_cost_of_living(location)                 # COL adjustment
      → purchasing_power = total * (100 / col_index)
      → OfferComparisonResult(total, purchasing_power, breakdown{})
      → formatted string
```

### job_outlook(occupation, region)

```
job_outlook_tool()
  → job_outlook(occupation, region)
      → find_occupation_by_title(occupation)
      → classify growth_rate into GrowthOutlook enum
      → cross-reference INDUSTRY_DATA for key industries
      → JobOutlookResult(growth_rate, outlook, openings, industries[])
      → formatted string
```

## Startup sequence

```
server.py __main__
  → load_dotenv()                      # read .env file
  → FastMCP(name="Career Compass")     # register 6 tools via @mcp.tool()
  → FastAPI(_lifespan)                 # health endpoint
  → uvicorn.run(app, host, port)       # serve SSE transport
```

## Data flow diagram

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  AI Agent   │◄───►│  MCP Server  │◄───►│  Service Layer │
│  (Claude,   │     │  (FastAPI +  │     │  src/salary.py │
│   Hermes,   │     │   SSE)       │     │  src/skills.py │
│   etc.)     │     │              │     │  src/paths.py  │
└─────────────┘     └──────────────┘     └───────┬────────┘
                                                  │
                    ┌─────────────────────────────┤
                    │                             │
                    ▼                             ▼
        ┌───────────────────┐          ┌──────────────────┐
        │  Occupation DB    │          │  Cost-of-Living  │
        │  (25 jobs, BLS)   │          │  (25 ZIP codes)  │
        └───────────────────┘          └──────────────────┘
```