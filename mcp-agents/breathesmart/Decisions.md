# Decisions — BreatheSmart

## 1. Architecture: MCP Server (not a standalone web app)

**Chosen:** MCP (Model Context Protocol) server with stdio transport
**Rejected:** Standalone Flask/FastAPI web service, CLI-only tool

**Why:** BreatheSmart is designed to be an AI-native tool — an LLM calls it directly via the MCP protocol. A web API would add latency and require a running server. Stdio transport means zero config: the MCP client spawns the server as a subprocess.

## 2. Language: Python (not Node.js/TypeScript)

**Chosen:** Python 3 with `mcp` SDK
**Rejected:** Node.js with the MCP TypeScript SDK

**Why:** Python's `mcp` library has a simpler API surface for a tool this size. The project lives in a Python-first monorepo (`LLM-Apps`) where all other MCP agents are Python. Async via `anyio` keeps the server responsive during API calls.

## 3. API Provider: Open-Meteo Air Quality (not AirNow / IQAir / Breezometer)

**Chosen:** Open-Meteo Air Quality API
**Rejected:** AirNow (US-only, requires registration), IQAir (rate-limited free tier), Breezometer (paid), PurpleAir (API key required)

**Why:** Open-Meteo is free, zero-auth, globally available, and returns a rich dataset (AQI, individual pollutants, pollen, UV). No API key means zero friction for users. European AQI and US AQI are both included.

## 4. Tool Surface: 4 focused tools (not 1 mega-tool)

**Chosen:** Four separate tools — get_current_air_quality, get_pollen_forecast, get_uv_index, get_health_summary
**Rejected:** Single tool with a `data_type` parameter, or many granular tools (one per pollutant)

**Why:** Each tool corresponds to a natural user question. The all-in-one `get_health_summary` exists for convenience (one call for outdoor planning). Pollen and UV are separate because they're only relevant seasonally. Granular per-pollutant tools would clutter the tool list.

## 5. Pollen Data Representation: grains/m³ with classified levels

**Chosen:** Return numeric values (grains/m³) with a color-coded level (Low/Moderate/High/Very High)
**Rejected:** Raw numeric values only, or text-only descriptions

**Why:** Raw numbers are meaningless without context. Classifying into Low/Moderate/High/Very High makes the data actionable. Keeping the numeric value lets power users make their own judgment.

## 6. Error Handling: Graceful degradation with user-friendly messages

**Chosen:** Catch `requests.RequestException` and return a friendly error message
**Rejected:** Let exceptions propagate to the MCP client, or silently return empty data

**Why:** API calls fail for many reasons (network, rate limits, temporary outages). The LLM can't recover from a raw exception, but a friendly error message lets it tell the user "the service is temporarily unavailable" instead of crashing.

## 7. AQI Classification: US EPA standard (0-500 scale)

**Chosen:** US EPA AQI breakpoints (0-50 Good, 51-100 Moderate, 101-150 Unhealthy for Sensitive Groups, etc.)
**Rejected:** European AQI scale, WHO guidelines only, custom thresholds

**Why:** The US AQI is the most widely recognized air quality index globally (used by weather apps, news, Google). European AQI is returned alongside for users who prefer it. The 6-level system maps to clear health recommendations.

## 8. Async Design: anyio-based async (not threading)

**Chosen:** `anyio.run()` for the MCP server event loop
**Rejected:** `asyncio.run()`, threaded server, synchronous blocking

**Why:** The `mcp` Python SDK recommends `anyio` for the stdio transport. It provides a clean async interface without the complexity of threading. All API calls use `requests` (sync) wrapped in async handlers — acceptable for a tool that makes one external call per invocation.

## 9. Location Input: Latitude/longitude (not city names or ZIP codes)

**Chosen:** Raw latitude/longitude coordinates
**Rejected:** Geocoding city names via Nominatim, accepting ZIP/postal codes

**Why:** Geocoding adds complexity (rate limits, dependency on a third API, privacy concerns with free-form text). Latitude/longitude is unambiguous and the LLM can easily derive coordinates from a city name ("Paris" → 48.8566, 2.3522). The `location_name` parameter in `get_health_summary` adds a human label without requiring geocoding.

## 10. Test Strategy: Unit tests with mocked API

**Chosen:** `pytest` with `unittest.mock` to mock `requests.get`
**Rejected:** Integration tests hitting the live API, or no tests

**Why:** The live Open-Meteo API is reliable but shouldn't be a test dependency. Mocking the HTTP layer tests all classification logic, error handling, and tool definitions without network calls. Integration tests are covered by the CLI client for manual verification.

## 11. Package Dependencies: Minimal footprint

**Chosen:** Only `requests` and `mcp` as runtime dependencies; `pytest` for testing
**Rejected:** Adding `httpx`, `pydantic`, `click`, `typer`, `geopy`

**Why:** The server only makes HTTP requests to one API. `requests` is sufficient. `mcp` is required by the protocol. Adding CLI frameworks or data validation libraries would increase the dependency surface with no benefit for a 4-tool server.

## 12. UV Data: Include clear-sky estimate

**Chosen:** Return both `uv_index` (actual) and `uv_index_clear_sky` (what UV would be without clouds)
**Rejected:** Return only the actual UV index

**Why:** Cloud cover reduces UV. The clear-sky estimate tells users what protection they'd need on a sunny day — useful for planning outdoor activities where cloud cover might change.

## 13. Pollen Forecast: Hourly trends (not just daily averages)

**Chosen:** Include hourly pollen values for the next 3+ time slots to show trends
**Rejected:** Daily averages only

**Why:** Pollen counts fluctuate throughout the day (peak mid-morning and early evening). Hourly data lets users time their outdoor activities. The summary shows average levels for readability while including the raw hourly data for power users.

## 14. Project Structure: Flat with tests subdirectory

**Chosen:** `server.py` (entry point), `client.py` (CLI), `tests/test_server.py`
**Rejected:** Package with `__init__.py`, separate `src/` and `tests/` directories

**Why:** For a single-module MCP server, a flat structure is simpler. Tests in a `tests/` subdirectory follow pytest conventions. The client is a standalone script for manual testing, not a library to be imported.
