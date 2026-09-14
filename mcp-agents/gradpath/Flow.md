# Flow — Execution trace from MCP tool call to output

## Overview

```
MCP Host (Claude Desktop, etc.)
    │
    ▼
server.py  (FastMCP — registers 4 tools)
    │
    │  find_colleges(school_name)
    │  college_profile(school_name)
    │  compare_colleges(school1, school2)
    │  earnings_by_program(school, field)
    │
    ▼
src/  (thin formatting + orchestration layer)
    │
    ├── searcher.py    →  scorecard.search_colleges()
    ├── profile.py     →  scorecard.get_college_profile()
    ├── comparer.py    →  scorecard.get_college_profile() x2
    └── earnings.py    →  scorecard.get_college_profile() + get_earnings()
    │
    ▼
src/scorecard.py  (College Scorecard API client)
    │
    ├── LIVE mode:  httpx → api.data.gov/ed/collegescorecard/v1/
    │
    └── SIMULATED:  filter _SAMPLE_COLLEGES list   ← default when no API key
```

## Detailed flows

### 1. find_colleges(budget_max=15000, state="CA", major="Computer Science", size_pref="medium")

```
server.py: find_colleges()
  └─ src/searcher.py: find_colleges(budget_max=15000, state="CA", ...)
       └─ src/scorecard.py: search_colleges(budget_max=15000, state="CA", ...)
            ├─ [SIMULATED] _simulate_search(budget_max=15000, state="CA", major=...)
            │    └─ Filter _SAMPLE_COLLEGES (8 items) by:
            │         net_price ≤ 15000
            │         state == "CA"
            │         program name contains "Computer Science"
            │         size matches "medium" (5000–15000)
            │    └─ Returns: list[College]
            │
            └─ [LIVE] httpx GET /schools?api_key=...&latest.cost.net_price.overall__range=0,15000&school.state=CA&latest.student.size__range=5000,15000
                 └─ Parse JSON → College objects
                 └─ Client-side major filter on programs
       └─ Format results into human-readable string
  └─ Return string to MCP host
```

### 2. college_profile("State University of Technology")

```
server.py: college_profile("State University of Technology")
  └─ src/profile.py: college_profile("State University of Technology")
       └─ src/scorecard.py: get_college_profile("State University of Technology")
            ├─ [SIMULATED] _simulate_school_by_name("State University of Technology")
            │    └─ Case-insensitive partial match against _SAMPLE_COLLEGES[*].school.name
            │    └─ Returns: College or None
            │
            └─ [LIVE] httpx GET /schools?api_key=...&school.name=State University of Technology
                 └─ Parse JSON → first result → College
       └─ Format: costs section, outcomes section, admissions, student body, programs
  └─ Return string to MCP host
```

### 3. compare_colleges("School A", "School B")

```
server.py: compare_colleges("School A", "School B")
  └─ src/comparer.py: compare_colleges("School A", "School B")
       └─ scorecard.get_college_profile("School A")
       └─ scorecard.get_college_profile("School B")
            (two parallel fetch calls — both simulated or both live)
       └─ Build table: Field | School A | School B
            - Net price
            - Tuition (in-state)
            - Tuition (out-of-state)
            - Grad rate
            - Median earnings (10yr)
            - Enrollment
            - SAT average
         └─ Compute ROI estimate (months of earnings to cover net price)
  └─ Return formatted string to MCP host
```

### 4. earnings_by_program("Metro Technical Institute", "Information Technology")

```
server.py: earnings_by_program("Metro Technical Institute", "Information Technology")
  └─ src/earnings.py: earnings_by_program("Metro Technical Institute", "Info Tech")
       └─ scorecard.get_college_profile("Metro Technical Institute")
            └─ Returns College (with programs list)
       └─ (Optional: check if "Information Technology" is in programs)
       └─ scorecard.get_earnings("Metro Technical Institute", "Information Technology")
            ├─ [SIMULATED] Returns {"median_earnings": 50000, "note": "..."}
            │
            └─ [LIVE] httpx GET /schools?api_key=...&school.name=Metro Technical Institute&fields=...,latest.earnings...
                 └─ Returns institution-level median earnings as proxy
       └─ Format: "Information Technology graduates from Metro Technical Institute
                   Median earnings 10 years after entry: $XX,XXX/yr"
  └─ Return string to MCP host
```

## Guard rails

- **No API key?** `_is_simulated()` returns True → all queries use sample data.
  Tests always set `COLLEGE_SCORECARD_API_KEY=""` via conftest fixture.
- **College not found?** Every tool returns a clear "not found" message with
  guidance to try `find_colleges` first.
- **Async throughout** — all tool functions are `async def`, all httpx calls
  use `AsyncClient`. No blocking IO on the event loop.
- **Field validation** — inputs are validated at the MCP layer by pydantic
  type coercion (budget_max as float, state as str, etc.).