# Decisions.md — Pack Light

## 1. CLI tool vs web app
**Chosen:** CLI tool (Python argparse)
**Rejected:** Flask/Streamlit web app
**Why:** A packing list is a before-trip utility — user runs it once per trip from their laptop. CLI is faster to build, zero deployment overhead, and works offline once data is cached. A web app would require hosting, auth, and a mobile-friendly UI for marginal benefit.

## 2. Python vs Node.js vs Go
**Chosen:** Python 3.13
**Rejected:** Node.js (npm dependency noise), Go (no stdlib HTTP geocoding, no YAML lib)
**Why:** Python has best-in-class HTTP (`requests`), YAML parsing (`pyyaml`), and date handling (`datetime`). The user's VPS already has Python 3.13. The app is I/O-bound (single HTTP call), so Python's speed is not a bottleneck.

## 3. Internal module structure: flat vs package
**Chosen:** Package with `packlight/` directory (3 modules: `weather.py`, `packer.py`, `cli.py`)
**Rejected:** Single monolithic script
**Why:** Separating concerns: `weather.py` owns all API interaction, `packer.py` owns the rules engine, `cli.py` owns argument parsing and output. Makes testing each component in isolation possible. A single-file script would be ~450 lines of mixed concerns.

## 4. Rules engine: YAML config vs hard-coded thresholds
**Chosen:** YAML rules file (`rules.yaml`) with threshold-based conditions
**Rejected:** Hard-coded if/elif tree in Python
**Why:** A config file lets users customise packing rules without touching code. The YAML format supports complex conditions (min/max, any/all) while remaining human-readable. Hard-coding would require code changes for every rule adjustment and wouldn't be user-extensible.

## 5. Condition evaluation: simple threshold vs expression language
**Chosen:** Simple threshold operators (>=, >, <=, <, ==, !=, any)
**Rejected:** Full expression parser (e.g. `min_temp < 5 and not snow_any`)
**Why:** The current set covers 99% of packing rules. A full expression parser adds complexity (ast parsing, safe eval) with no real user benefit. If advanced logic is needed, users can chain multiple rules with different thresholds.

## 6. Weather data source: Open-Meteo vs OpenWeatherMap vs WeatherAPI
**Chosen:** Open-Meteo
**Rejected:** OpenWeatherMap (requires API key signup), WeatherAPI (free tier limits)
**Why:** Open-Meteo is completely free, requires zero API key, serves 10K requests/day non-commercial, and has both geocoding and forecast in one ecosystem. No signup friction means the tool works immediately after install.

## 7. Geocoding: Open-Meteo built-in vs Nominatim vs Google Geocoding
**Chosen:** Open-Meteo Geocoding API
**Rejected:** Nominatim (usage policy requires attribution, rate-limited), Google (requires API key + billing)
**Why:** Open-Meteo's geocoding is bundled with their forecast API ecosystem — same domain, no extra deps, no key. Resolves "Tokyo" and "Paris,FR" correctly.

## 8. Output format: interactive list vs plain text vs table vs JSON
**Chosen:** Three modes: `list` (default, grouped by category with checkboxes), `table` (aligned columns), `minimal` (one-liners)
**Rejected:** Single fixed format
**Why:** Users have different needs. `list` is the most useful for printing as a checklist. `table` is good for screen reading. `minimal` is best for shell piping. No JSON because the primary user is a human, not another program.

## 9. Date handling: manual argparse dates vs python-dateutil parser
**Chosen:** Manual `datetime.strptime` with YYYY-MM-DD format
**Rejected:** `python-dateutil` (extra dependency, parses "next Tuesday" ambiguously)
**Why:** YYYY-MM-DD is unambiguous, ISO 8601 compliant, and the stdlib handles it perfectly. Adding a dependency for date parsing is overkill when the format is pinned.

## 10. Testing approach: pytest vs unittest
**Chosen:** pytest
**Rejected:** unittest (more boilerplate, less readable assertions)
**Why:** pytest's fixture system (especially `tmp_path`) makes testing YAML file loading clean. Fixtures like `sample_days` and `cold_days` keep test data reusable across tests. Conftest.py isn't needed at this scale.

## 11. WMO weather codes: bundled dict vs API introspection
**Chosen:** Hand-maintained dict mapping codes to labels
**Rejected:** Parsing WMO spec XML or calling a metadata API
**Why:** The WMO code set is static (defined by World Meteorological Organization, ~30 codes used in practice). A dict inline is simpler, faster, and more readable than any dynamic solution.

## 12. Remote vs bundled rules location
**Chosen:** Bundled `rules.yaml` in the project root (searched via `Path(__file__).parent.parent`)
**Rejected:** Hard-coded absolute path, or XDG config directory
**Why:** Bundling means the tool works immediately after install with sensible defaults. Users can override with `--rules /path/to/custom.yaml`. An XDG approach would require more discovery logic.

## 13. Error handling: friendly messages vs traceback propagation
**Chosen:** User-facing error messages (❌ prefix, no tracebacks)
**Rejected:** Raw exception propagation to stderr
**Why:** A packing tool is for everyday users, not developers. Network errors, geocoding failures, and bad date formats all produce clear messages. `SystemExit(1)` prevents further execution. Developers can still see tracebacks with `PYTHONVERBOSE=1`.

## 14. Aggregation strategy: per-day vs trip-level
**Chosen:** Trip-level aggregation (max/min/avg across all days)
**Rejected:** Per-day rule evaluation (recommend items per day)
**Why:** A packing list is a single set of items for the whole trip, not a per-day wardrobe. Trip-level aggregation tells you "bring a raincoat" if any day has rain, not "bring a raincoat on day 2."

## 15. Default trip length: 3 days
**Chosen:** 3 days if neither `--to` nor `--days` is specified
**Rejected:** 1 day (too short — misses extended-trip rules), 7 days (too long for weekend trips)
**Why:** 3 days is the most common short-trip duration. Weekend trips (2 nights, 3 days) are the dominant use case for a packing-list generator.