# Decisions — SafeRide

## Why each architectural choice was made, and what was rejected.

### 1. CLI-first (not web app)
**Chosen:** Terminal CLI with Rich formatting.  
**Rejected:** Flask/FastAPI web server; Streamlit dashboard.  
**Why:** CLI is fastest to build, zero infrastructure, works headless. The user runs one command before a road trip — no server, no browser, no setup.

### 2. Sub-agents as Python modules (not microservices)
**Chosen:** Three agents as separate Python files in an `agents/` package, called directly by the coordinator.  
**Rejected:** REST microservices; MCP server pattern; message queue.  
**Why:** For a single-session build with no persistence, function calls between in-process modules are faster, simpler to test, and have zero deployment overhead.

### 3. Dataclasses for models (not Pydantic)
**Chosen:** stdlib `dataclasses` for all data models.  
**Rejected:** Pydantic BaseModel; TypedDict; plain dicts.  
**Why:** Dataclasses give typed fields, default values, and readable `__repr__` without adding a dependency. Pydantic adds validation we don't need for internal data that is always well-formed after parsing.

### 4. Rich for CLI rendering (not plain print)
**Chosen:** `rich` library for tables, panels, and colored output.  
**Rejected:** Plain `print()`; `tabulate`; `textual`.  
**Why:** Rich renders nested data (recall tables, weather grids) in a readable format with zero template code. It's already installed in most Python environments and is a single import.

### 5. NHTSA API for vehicle recalls (not NHTSA scraping)
**Chosen:** `api.nhtsa.gov/recalls/recallsByVehicle` with VIN and make/model/year endpoints.  
**Rejected:** Scraping safercar.gov; using a third-party recall API.  
**Why:** NHTSA's official API is free, unlimited, zero-auth, returns structured JSON, and covers all US-market vehicles. Scraping would break on HTML changes; third-party APIs risk rate limits or paywalls.

### 6. Open-Meteo for weather (not OpenWeatherMap or WeatherAPI)
**Chosen:** Open-Meteo's free forecast API (`api.open-meteo.com/v1/forecast`).  
**Rejected:** OpenWeatherMap (requires API key), WeatherAPI (free tier 1M calls/month but key required).  
**Why:** Open-Meteo needs zero signup, no API key, unlimited calls. It provides all weather fields we need (temp, precipitation, wind, visibility) with global coverage.

### 7. Open-Meteo Geocoding (not Nominatim)
**Chosen:** Open-Meteo's own `/v1/search` geocoding endpoint.  
**Rejected:** Nominatim (1 req/s rate limit); Google Maps Geocoding (paid).  
**Why:** Open-Meteo's geocoder reuses the same HTTP client, has no rate limit, and returns coordinates we pass directly to the forecast endpoint. Fewer dependencies, faster cold start.

### 8. MockTransport pattern for tests (not monkeypatching)
**Chosen:** `httpx.Client(transport=httpx.MockTransport(handler))` injected via `set_client()`.  
**Rejected:** `unittest.mock.patch('httpx.Client')`; VCR.py.  
**Why:** MockTransport is the recommended httpx approach for deterministic tests. It avoids monkeypatching globals and keeps test setup explicit. VCR.py would record real HTTP calls that expire or change.

### 9. Simulated fallback data (not hard crash)
**Chosen:** Each agent has a `_simulate_*` function that returns demo data when the live API fails.  
**Rejected:** Letting exceptions propagate to the CLI; returning empty results silently.  
**Why:** Users running `saferide` for the first time (without internet or behind a proxy) should see realistic output, not a stack trace. Simulated data is clearly labelled with `source="simulated"`.

### 10. Flat project structure (not Django-style apps)
**Chosen:** Single `agents/` package with three agent files + `coordinator.py`, `models.py`, `__main__.py`.  
**Rejected:** Separate top-level package per agent; Django app structure.  
**Why:** Three agents sharing a few models don't warrant deep nesting. Flat structure keeps imports short and the whole project readable in one IDE window.

### 11. No persistence layer (not SQLite)
**Chosen:** Pure stateless CLI — no database, no cache.  
**Rejected:** SQLite for trip history; JSON file for saved VINs.  
**Why:** Persistence adds complexity (schema management, cleanup) and the use case is "check before a trip", not "track my fleet". Users can script their own history with shell `>>` if needed.

### 12. No LLM dependency (not GPT/Claude)
**Chosen:** Pure algorithmic logic — keyword severity classification, weather threshold checks, string matching.  
**Rejected:** OpenAI/Claude to summarize recall text; LLM to generate trip reports.  
**Why:** NHTSA recall summaries are already readable. Adding an LLM would require an API key, add latency, and make the tool non-functional offline. The `_rate_recall_severity` heuristic is sufficient.

### 13. `set_client()` for testability (not a real HTTP layer)
**Chosen:** Module-level `_client` variable set via `set_client()`, falling back to a real `httpx.Client()`.  
**Rejected:** Passing a client through every function signature; using global `httpx` directly.  
**Why:** `set_client()` lets tests inject a MockTransport without changing function signatures. The default None → real client pattern means production code needs zero configuration.

### 14. One-shot trip check (not interactive multi-vehicle)
**Chosen:** Single trip check per invocation (CLI args or interactive mode).  
**Rejected:** REPL loop that lets users check multiple vehicles in one session.  
**Why:** The one-shot model is simpler (no state machine, no loop termination logic) and matches how people actually use it: "I'm about to drive from NYC to LA, check my car." The interactive prompt at startup handles first-time users.