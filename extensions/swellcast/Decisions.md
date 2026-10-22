# Decisions — SwellCast

### 1. CLI tool vs web app or GUI

**Decision:** CLI (command-line interface).  
**Rejected alternatives:** Web app (Flask/FastAPI) — adds deployment complexity, requires a running server. GUI (Tkinter/Textual) — adds heavy dependencies.  
**Why:** The Extensions category prefers standalone modules. A CLI with `argparse` is self-contained, zero-dependency, and runnable anywhere Python is installed. Matches the pattern of existing extensions (pocketdiet, sunguard, etc.).

### 2. Stdlib only vs. third-party HTTP library (requests, httpx)

**Decision:** `urllib.request` from the Python standard library.  
**Rejected:** `requests` (cleaner API but adds a dependency); `httpx` (async overhead for a sequential CLI).  
**Why:** Zero-install dependencies make the tool immediately runnable. The API calls are simple GET → JSON → parse — urllib handles this fine with no external packages.

### 3. Open-Meteo Marine vs. NOAA NWS / Stormglass / Surfline

**Decision:** Open-Meteo Marine for wave/swell data.  
**Rejected:** NOAA NWS wave data (requires parsing GRB2 — very complex); Stormglass (paid API key); Surfline (no free API).  
**Why:** Open-Meteo Marine is free, no API key, global coverage, returns clean JSON with wave height, period, direction, swell separation, and wind wave data. Buildable in a session.

### 4. Geocoding strategy

**Decision:** Open-Meteo Geocoding API (free, no key).  
**Rejected:** Nominatim (requires User-Agent rate limiting); Google Geocoding (requires API key + billing).  
**Why:** Open-Meteo geocoding is same-ecosystem (same provider as wave data), fast, free, and returns structured results with admin area and timezone.

### 5. Surf scoring algorithm: heuristic vs. machine learning

**Decision:** Heuristic rule-based scoring formula.  
**Rejected:** Machine learning (requires training data on surf quality — not available in one session).  
**Why:** A formula with weighted factors (wave height, swell period, wind) produces reasonable results that are explainable and debuggable. The user sees exactly why a score changed. Good enough for v0.1.

### 6. Module structure: single file vs separated concerns

**Decision:** Four modules: `cli.py`, `core.py`, `geo.py`, `models.py`.  
**Rejected:** Single monolithic file (too long, hard to test — ~200+ lines); over-split (one file per function).  
**Why:** Clear separation: CLI parsing in cli.py, business logic in core.py, geocoding in geo.py, data types in models.py. Each is independently testable. Matches existing extension structure (pocketdiet has similar split).

### 7. Output format: tabular vs narrative

**Decision:** Line-by-line narrative with emoji markers.  
**Rejected:** Table format (tabulate dependency, harder to read on small terminal); pure JSON (requires a viewer).  
**Why:** Surf conditions are consumed as a quick glance — one day per paragraph with emoji score labels is readable and visually scannable.

### 8. Latitude/longitude format support

**Decision:** Accept both `"Place Name"` and `lat lon` (two floats).  
**Rejected:** Only place names (fails for obscure spots); only coordinates (unfriendly for casual users).  
**Why:** Power users know coordinates; casual users know beach names. Supporting both catches every use case.

### 9. Test approach: mock-free vs mocked network

**Decision:** Pure unit tests with computed inputs (no network mocks).  
**Rejected:** Integration tests that call live APIs (flaky, rate-limited); pytest-httpx or responses library (adds dependencies).  
**Why:** The scoring algorithm is the core logic — it takes `SurfDay` dataclass instances and returns scores. Testing it with crafted inputs (flat, perfect, stormy) covers all paths without network I/O. The live API layer is thin; a manual smoke test validated it works.

### 10. Swell vs wave display

**Decision:** Show both wave height and swell height when swell differs from total wave height.  
**Rejected:** Show only wave height (hides important surf info); show only swell (confusing — surfers care about both).  
**Why:** Open-Meteo provides both `wave_height_max` and `swell_wave_height_max`. When swell is present (swell_height > 0), showing both gives surfers the full picture: total wave size vs. underlying groundswell energy.

### 11. Forecast days default

**Decision:** 5 days.  
**Rejected:** 7 days (longer API response, less accurate); 3 days (too short — weekend planning); 16 days (Open-Meteo max, but low accuracy).  
**Why:** 5 days covers the "week + weekend" window surfers check. The `--days` flag allows customization up to 16.

### 12. Weather code description

**Decision:** Include WMO weather codes as human-readable labels.  
**Rejected:** Omit weather entirely (surfers need to know if it's raining/foggy); include full forecast table (bloats output).  
**Why:** A single WMO code description (e.g., "Partly cloudy", "Moderate rain") is concise. Surfers check conditions before heading out — "Moderate rain" changes their day.

### 13. Wind direction display

**Decision:** Compass-direction label (N, SW, etc.) + degrees in parentheses.  
**Rejected:** Degrees only (not human-readable); "offshore/onshore" only (hides exact direction).  
**Why:** Surfers think in compass directions ("NW wind"). The `_wind_dir_label` function converts 0-360° to 16-point compass. The degree value is supplementary for the precision-minded.

### 14. Error handling: fail-fast vs graceful degradation

**Decision:** Fail-fast with clear error messages.  
**Rejected:** Falling back to dummy data (misleading); infinite retry (wastes time for a CLI).  
**Why:** If the Open-Meteo API is down or the location resolves to nowhere, the user gets `Error: Could not find location` or an empty report. Clear and immediate beats silent failure.

### 15. No config file

**Decision:** No configuration file or environment variables.  
**Rejected:** `.env` for API keys (none needed); config.yaml for defaults (over-engineering for a CLI).  
**Why:** Zero config. The tool requires no setup — install and run. This is the hallmark of a well-designed extension.