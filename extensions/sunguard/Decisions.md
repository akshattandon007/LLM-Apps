# SunGuard Architecture Decisions

This document records key architectural decisions made during the design of the SunGuard MCP server, along with rejected alternatives and their rationale.

## 1. Module-level `set_client()` injection vs. dependency injection (class-based)

**Chosen**: Module-level `_client` with `set_client()` / `get_client()` functions.

- **Rejected**: Class-based `WeatherAPIClient` injected via constructor — too much ceremony for a small project. The module-level approach is idiomatic in Python (cf. `requests` session pattern), keeps weather.py flat, and is trivially replaced in tests with `pytest-httpx` / `httpx.MockTransport`.
- **Rejected**: Global `httpx.Client` with no injection — impossible to test without hitting real APIs.

## 2. Open-Meteo over OpenWeatherMap / WeatherAPI

**Chosen**: Open-Meteo for weather, air quality, and geocoding.

- **Rejected**: OpenWeatherMap (requires API key, rate limits, paid tiers for air quality).
- **Rejected**: WeatherAPI (requires API key, free tier limited to 1M calls/month but still needs registration).
- **Reason**: Open-Meteo is free, zero-auth, no API key needed, and covers all three data sources (weather, geocoding, air quality) from a single ecosystem.

## 3. NWS alerts (US-only) vs. global heat advisory service

**Chosen**: NWS Weather API for heat advisories (US only).

- **Rejected**: Global weather alert aggregators (requires API keys, paid subscriptions).
- **Trade-off**: NWS is free and authoritative in the US but provides no international coverage. The server gracefully returns empty alerts for non-US locations.

## 4. Fitzpatrick skin type as string enum vs. integer index

**Chosen**: Roman numeral string enum (`I`-`VI`) matching medical convention.

- **Rejected**: Integer enum (1-6) — less discoverable for AI agents that may not know the Fitzpatrick scale details. The Roman numeral system is the clinical standard.
- **Rejected**: Natural language string ("type I", "type 1") — harder to validate and parse.

## 5. One tool per operation vs. one giant `safety_report` tool

**Chosen**: Six separate tools (`sun_safety`, `hourly_uv`, `skin_burn_time`, `heat_safety`, `air_quality_check`, `outdoor_plan`).

- **Rejected**: Single `safety_report` with a `detail_level` parameter — couples unrelated concerns, makes the return type complex, and prevents AI agents from choosing exactly what they need.
- **Reason**: MCP is designed for tool composability. Each tool has a focused return type (Pydantic model), making it easy for AI agents to iterate.

## 6. Pydantic models over plain dicts / TypedDicts

**Chosen**: `pydantic.BaseModel` subclasses for all tool return types.

- **Rejected**: Plain dicts — no schema documentation, no validation, no IDE support.
- **Rejected**: `TypedDict` — runtime validation not possible, no coercion.
- **Reason**: Pydantic provides automatic JSON Schema generation (used by MCP for tool description), field validation, type coercion, and enum handling.

## 7. Simulated fallback over failing on API errors

**Chosen**: Every API call has a `_simulate_*` fallback that returns plausible data when the real API is unreachable.

- **Rejected**: Raising exceptions on API failure — makes the server undemoable without internet access.
- **Rejected**: Caching last-known-good data — adds complexity and staleness issues.
- **Reason**: The server is always demoable. Simulation returns Portland, Oregon summer data (~UV 6.5, 30°C) which is plausible for a default.

## 8. httpx over requests / aiohttp

**Chosen**: `httpx.Client` (synchronous, connection pooling).

- **Rejected**: `requests` — not compatible with `pytest-httpx` mock transport; fewer modern features.
- **Rejected**: `aiohttp` — asynchronous, but MCP `@mcp.tool()` methods are synchronous callbacks. Mixing async would complicate synchronization.
- **Reason**: httpx is the modern standard with built-in mock support via `MockTransport`.

## 9. European AQI over US EPA AQI

**Chosen**: European AQI (`european_aqi`) from Open-Meteo Air Quality.

- **Rejected**: US EPA AQI — Open-Meteo air quality API primarily serves European AQI. EPA AQI requires a different endpoint or transformation.
- **Trade-off**: European AQI runs 0-500 (similar range to EPA AQI) but uses different breakpoints. The risk categorization (low/moderate/high) is similar enough for general advice. If EPA AQI is critical, add a transformation layer.

## 10. Rothfusz heat index regression over simple lookup tables

**Chosen**: Full NOAA Rothfusz regression formula with humidity-based corrections.

- **Rejected**: Lookup table — inflexible, requires pre-computing all temperature/humidity pairs.
- **Rejected**: Simple `temp + 5°C` approximation — inaccurate at extreme temperatures.
- **Reason**: The Rothfusz formula is the NOAA standard, accurate across the full temperature range, and handles humidity adjustments. Default humidity of 50% is a reasonable assumption when actual humidity data isn't fetched.

## 11. Burn time scaling formula over static tables

**Chosen**: Dynamic scaling: `base_time * (3.0 / uv_index)` with clamped UV factor [0.25, 3.0].

- **Rejected**: Static per-skin-type burn time regardless of UV — ignores the huge difference between UV 1 and UV 11.
- **Rejected**: Linear scaling without clamping — UV 0 would give infinite burn time.
- **Reason**: UV 3 is the baseline "moderate" threshold per WHO. The formula gives ~10 minutes for type I at UV 11 and ~90+ minutes for type VI at UV 1, matching medical guidance.

## 12. Synchronous MCP server over async

**Chosen**: Synchronous `FastMCP` with synchronous tool handlers.

- **Rejected**: Async with `asyncio` — adds complexity. All API calls are synchronous httpx. The MCP SDK supports both modes, and synchronous is simpler for a tool server.
- **Trade-off**: If throughput becomes a concern, tools can be converted to async with minimal changes.

## 13. Geocoding auto-fallback to simulated Portland

**Chosen**: On geocode failure, return Portland, OR coordinates (~45.5, -122.7).

- **Rejected**: Raise `ValueError` and let the caller handle it — breaks the "always demoable" principle.
- **Rejected**: Return `None` and have every tool check for None — adds conditional branching in 6 places.
- **Reason**: Portland is a well-known US city with moderate summer UV (~6-7) — a safe default that produces meaningful safety advice even when geocoding fails.

## 14. No caching layer

**Chosen**: Every tool call fetches fresh data.

- **Rejected**: In-memory cache with TTL — adds complexity. Weather data changes hourly, and the server is stateless by design.
- **Reason**: For a safety tool, staleness is dangerous. Fresh data on every call ensures the user gets current conditions.

## 15. `mcp[cli]` pinned `<2` over latest

**Chosen**: `mcp[cli]>=1.0.0,<2.0.0` in requirements.

- **Rejected**: Pinning latest (`>=1.0.0`) — the MCP SDK is evolving rapidly. Version 2 has breaking API changes (different `FastMCP` constructor signature). Pinning `<2` ensures stability.
- **Rejected**: Pinning an exact version — too restrictive, misses security patches.
- **Reason**: The v1 SDK uses `from mcp.server.fastmcp import FastMCP` with a specific constructor. This constraint protects against accidental v2 upgrades.