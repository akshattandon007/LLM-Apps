# Decisions — MoveMate

## 1. Multi-Agent Pattern vs Monolithic Script
**Chosen:** Modular agent architecture with orchestrator  
**Rejected:** A single monolithic script doing everything  
**Why:** The problem naturally decomposes into 5 distinct concerns (utilities, addresses, costs, neighborhood, timeline). Separate agents are independently testable, swappable, and easier to maintain. The orchestrator gives a single coordination point where logging, error handling, and aggregation live.

## 2. CLI Interface vs Web App
**Chosen:** CLI with both argument and interactive modes  
**Rejected:** Web app (Flask/Streamlit)  
**Why:** The rota pipeline builds CLI tools. A web app would require dependencies, a browser, and deployment overhead. CLI works headlessly (cron-friendly), and the interactive mode handles the non-technical user case with a guided wizard.

## 3. Python vs TypeScript/Node.js
**Chosen:** Python 3.9+  
**Rejected:** TypeScript/Node.js  
**Why:** Zero external dependencies needed. Python's standard library has urllib.request, datetime, argparse, json, and dataclasses — everything required. Node.js would require npm packages for CLI argument parsing and HTTP requests.

## 4. Standard Library HTTP vs `requests` Library
**Chosen:** `urllib.request` (stdlib)  
**Rejected:** `requests` (PyPI)  
**Why:** No pip install needed. The project uses only GET/POST to simple REST endpoints. urllib.request handles everything required. Keeping zero dependencies means instant `git clone && python main.py` with no setup.

## 5. Data Classes vs Dicts vs Pydantic
**Chosen:** `dataclasses` from stdlib  
**Rejected:** Plain dicts (no type safety, no code completion), Pydantic (external dependency)  
**Why:** Dataclasses provide type hints, default factories, and clean `__repr__` without any imports beyond stdlib. They're the sweet spot between formality and simplicity for a 5-agent project.

## 6. Markdown Output vs HTML vs PDF
**Chosen:** Markdown rendered to stdout / saved to .md file  
**Rejected:** HTML (needs template), PDF (needs reportlab/weasyprint), JSON (not human-readable)  
**Why:** Markdown is human-readable in terminal, renders well on GitHub, and can be converted to PDF/HTML later if needed. The `to_markdown()` method on Playbook keeps rendering logic with the model.

## 7. Neighborhood Research Strategy
**Chosen:** OpenStreetMap Overpass API for nearby amenities + Open-Meteo for weather  
**Rejected:** Google Maps API (requires API key + billing), purely static content  
**Why:** Overpass API is free, no key needed, and returns structured amenity data (parks, transit stops, supermarkets). Open-Meteo gives free weather forecasts. Combined, they give a useful neighborhood snapshot without any paid service.

## 8. Zip-Only Input vs Full Address Required
**Chosen:** ZIP codes sufficient, full address optional  
**Rejected:** Requiring full street address always  
**Why:** Many people know the ZIP but not the exact address (e.g., moving to a new city). ZIP codes give enough spatial resolution for cost estimation and enabling neighborhood research if the user provides more detail.

## 9. Cost Estimation Approach
**Chosen:** Deterministic formula based on ZIP distance + household size  
**Rejected:** Real-time price scraping (fragile, rate-limited, legal concerns), LLM-based estimation (unpredictable, needs API key)  
**Why:** A deterministic formula gives consistent, explainable results. The ZIP distance heuristic (first-digit region approximation) is simple but works well enough for rough estimates. Users are told to get 3 real quotes.

## 10. Timeline Format
**Chosen:** Structured entries with week ranges + categorized tasks  
**Rejected:** Flat list of tasks, Gantt chart  
**Why:** Grouped by week with a date range header makes it scannable. Categorization (planning/admin/packing/moving/settling) helps users prioritize. The Playbook `to_markdown()` renders checkboxes for each task.

## 11. Test Framework
**Chosen:** pytest  
**Rejected:** unittest (verbose), no tests (risky)  
**Why:** pytest is standard, requires concise `assert` statements, and is widely available. Tests cover each agent independently plus the Playbook rendering.

## 12. Error Handling Strategy
**Chosen:** Graceful degradation with fallback text  
**Rejected:** Hard fail on API errors, silent ignore  
**Why:** If neighborhood APIs are unreachable, the playbook still delivers utility, costs, address changes, and timeline. An informational note tells the user what was unavailable rather than crashing. The orchestrator never blocks on a single agent.

## 13. No External API Key Requirement
**Chosen:** Zero API keys — all data from free, open APIs  
**Rejected:** Using any service requiring registration or payment  
**Why:** The rota requires buildable-in-one-session with no paid services. Every API used (Nominatim, Overpass, Open-Meteo, Wikipedia) is free and keyless. The project works immediately on any machine with Python.

## 14. Household Size Granularity
**Chosen:** 5 tiers (studio, 1br, 2br, 3br, house)  
**Rejected:** Continuous input (sqft or number of rooms), binary (small/large)  
**Why:** 5 tiers cover the common apartment/house spectrum. Each maps to a cost base table with reasonable variance. More granular inputs would overcomplicate without proportional benefit.