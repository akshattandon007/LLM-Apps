# Decisions.md — SafeHome architecture rationale

## 1. Why an MCP server, not a web app?
The user needs to check property safety from any chat interface or AI agent workflow. A web app locks the tool into a browser with its own UI. An MCP server decouples safety logic from presentation: any MCP host (Claude Desktop, Hermes, custom scripts) can call it via stdio or HTTP. A non-technical person can ask an AI "is this house in a flood zone?" and get an answer without installing anything.

Rejected: Standalone web app (too much UI overhead, single access path).

## 2. Why three separate data sources instead of one?
No single free API provides comprehensive property risk data. FEMA covers federally-declared disasters by county. NWS covers active weather alerts and forecasts. The Census Geocoder resolves addresses to coordinates. Combining them gives a complete picture: "What disasters have happened here, what's happening now, and what's the weather doing?"

Rejected: Using only one data source (incomplete picture). Paying for a consolidated risk API (unnecessary cost when free sources cover the need).

## 3. Why the Census Geocoder for address resolution?
Free, zero-auth (no API key), returns accurate lat/lon for any US street address including verification of the address existence. Alternatives like Google Geocoding or Mapbox require API keys and billing. OpenStreetMap/Nominatim has rate limits and slower response. Census is the most practical free option for US-only data.

Rejected: Google Geocoding API (requires API key + billing). Nominatim (rate-limited, slower). Manual zip code centroid approximation (too imprecise).

## 4. Why FEMA's DisasterDeclarationsSummaries API?
FEMA's open data API provides the most comprehensive free source of declared natural disasters at the county level. Data goes back decades, is updated regularly, and is structured JSON. Includes incident type, date, and whether individual assistance or public assistance was declared.

Rejected: USGS earthquake API (only earthquakes, not comprehensive). NOAA storm events (CSV-based, harder to query). NFHL flood zone API (requires complex map service, not REST).

## 5. Why the NWS API (weather.gov) instead of OpenWeatherMap or WeatherAPI?
The NWS API is free, zero-auth, authoritative for US weather data, and provides rich alert data (headline, severity, urgency, instruction). OpenWeatherMap and WeatherAPI require API keys and have free tier limits. NWS alerts include the critical "instruction" field telling people what to do (evacuate, shelter, etc.).

Rejected: OpenWeatherMap (API key required, free tier limited). WeatherAPI (same). AccuWeather (paid).

## 6. Why in-process caching?
The NWS forecast API and FEMA API return data that stays relevant for hours. In-process caching (dict) avoids redundant network calls when a user queries the same address or state within a session. Cache is per-server-instance, not shared — no Redis complexity for a tool meant to be simple.

Rejected: Redis/memcached (overkill for a single-server MCP tool). No caching (unnecessary API calls for repeated lookups). File-based cache (complexity without benefit for session-scoped data).

## 7. Why httpx instead of requests?
httpx supports async natively (useful if we parallelize API calls in the future) and has HTTP/2 support, connection pooling, and modern defaults. For a tool making 3-4 API calls per lookup, httpx's client session management is cleaner than requests' session API.

Rejected: requests (no native async, older design). aiohttp (async-only, overkill for current sync pattern).

## 8. Why the MCP SDK (mcp package) instead of raw FastAPI?
The `mcp` library handles protocol negotiation (stdio vs SSE), tool registration, input validation, and response formatting. Implementing this manually means reimplementing the MCP spec. The library is community-standard, well-maintained, and used by all existing project MCP agents.

Rejected: Raw FastAPI (must reimplement MCP protocol). Custom SSE protocol (not compatible with MCP hosts).

## 9. Why module-per-capability, not monolithic?
- `src/geocoder.py` — Census API abstraction (single responsibility)
- `src/disasters.py` — FEMA disaster data
- `src/weather.py` — NWS alerts and forecasts
- `src/report.py` — report assembly and formatting
- `server.py` — MCP glue

Each module is testable in isolation. Swapping a data source (e.g., Census → Google) touches exactly one file. Adding a new data source (e.g., FEMA flood maps) is one new module + one new handler.

Rejected: Monolithic server.py (harder to test, maintain, or swap providers). Flat module layout without source package (import ambiguity).

## 10. Why 6 MCP tools, not more?
These 6 cover the complete user story from "what's the risk at this address?" to detailed drill-downs on specific dimensions. The `safety_report` tool is the primary entry point; the others are power-user tools for specific questions. Adding more before shipping v1 would violate thin-slice delivery.

Rejected: 10+ tools (scope creep, confusing UX). Single "do everything" tool (takes too long to get an answer for specific questions).

## 11. Why Pydantic v2?
Type-safe model validation, serialization, and clear error messages. Already a dependency of the MCP SDK. Pydantic v2 is the modern standard for Python API work.

Rejected: Raw dict validation (no type safety, runtime bugs). Pydantic v1 (older, less performant).

## 12. Why FastAPI + uvicorn for HTTP transport?
MCP supports stdio (desktop/local clients) and SSE (remote clients on a VPS). FastAPI/uvicorn provides the SSE path with minimal overhead. The MCP package handles the protocol; FastAPI just serves it. This is the standard stack for MCP-over-HTTP in the LLM-Apps repo.

Rejected: Raw asyncio server (reinventing the wheel). Flask (no native async, requires hacks for SSE).

## 13. Why not include flood zone data (FEMA NFHL)?
FEMA's National Flood Hazard Layer is available via map services (WMS/WFS) but not through a simple REST API. Integrating it would require complex spatial queries. Adding flood zone lookup requires either Esri ArcGIS REST or manual coordinate-vs-polygon comparisons. Worth adding in v2 but would stretch the v1 build window.

Rejected: FEMA NFHL integration (complex, not REST, v2 feature). Third-party flood API (paid).

## Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | MCP server | Client-agnostic, works with any MCP host |
| Primary API sources | Census + FEMA + NWS | Free, zero-auth, comprehensive coverage |
| Address resolution | Census Geocoder | Free, zero-auth, accurate US data |
| Disaster data | FEMA Open API | Free, county-level, decades of history |
| Weather data | NWS/weather.gov | Free, authoritative, zero-auth |
| HTTP client | httpx | Async-capable, modern defaults |
| Transport | FastAPI/uvicorn (SSE) + stdio | Supports remote and local clients |
| Models | Pydantic v2 | Type-safe, ecosystem standard |
| Module layout | Per-capability modules | Testable isolation, one-change swaps |
| Caching | In-process dict | Session-scoped, no overhead |
| Tool count | 6 | Complete story without over-scoping |
| Flood zones | Deferred to v2 | Complex spatial data, not REST-friendly |