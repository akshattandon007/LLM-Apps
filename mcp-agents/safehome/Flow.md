# Flow.md — SafeHome execution trace

## Entry Point

```
User query (e.g., "check safety of 742 Evergreen Terrace, Springfield IL")
    │
    ▼
server.py (main / uvicorn / mcp-cli)
    │
    ├── list_tools() → returns 6 tool definitions
    │
    └── call_tool(name="safety_report", arguments={"address": "..."})
          │
          └── _handle_safety_report(address)
                │
                └── generate_safety_report() [src/report.py]
```

## Main Execution Path — safety_report tool

```
generate_safety_report(address)
    │
    ├── 1. geocode(address) [src/geocoder.py]
    │       │
    │       ├── HTTP GET → Census Geocoder API (onelineaddress)
    │       │     └── Returns: lat, lon, formatted_address
    │       │
    │       └── Returns: (lat, lon, formatted_address)
    │
    ├── 2. get_county_for_point(lat, lon) [src/geocoder.py]
    │       │
    │       ├── HTTP GET → Census Geocoder (coordinates→geographies)
    │       │     └── Returns: county name
    │       │
    │       └── Returns: county (str | None)
    │
    ├── 3. _extract_state(formatted_address, county) [src/report.py]
    │       │
    │       └── get_state_code() [src/disasters.py] — lookup table
    │       └── Returns: state 2-letter code (str | None)
    │
    ├── 4. summarize_disasters_for_county(state_code, county) [src/disasters.py]
    │       │
    │       ├── get_disasters_for_state(state_code)
    │       │     │
    │       │     └── HTTP GET → FEMA DisasterDeclarationsSummaries API
    │       │           └── Returns: list of disaster declaration dicts
    │       │
    │       ├── Filter: county name (case-insensitive partial match)
    │       ├── Filter: fyDeclared >= (current_year - max_years)
    │       │
    │       └── Returns: formatted Markdown disaster history string
    │
    ├── 5. get_active_alerts(lat, lon) [src/weather.py]
    │       │
    │       ├── HTTP GET → api.weather.gov/alerts/active?point=lat,lon
    │       │     └── (HEADERS: User-Agent required, no auth)
    │       │
    │       └── Returns: list of alert dicts (headline, event, severity, urgency, instruction)
    │
    ├── 6. format_alerts(alerts) [src/weather.py]
    │       │
    │       ├── Sort by severity (Extreme → Minor)
    │       ├── Format each alert: event, severity, urgency, headline, instruction
    │       │
    │       └── Returns: formatted Markdown alerts string
    │
    ├── 7. get_forecast(lat, lon) [src/weather.py]
    │       │
    │       ├── HTTP GET → api.weather.gov/points/{lat},{lon}
    │       │     └── Returns: forecast URL (properties.forecast)
    │       │
    │       ├── HTTP GET → forecast URL from step 7
    │       │     └── Returns: forecast periods (14 periods = 7 days)
    │       │
    │       └── format_forecast(forecast) — build Markdown
    │
    └── 8. Assemble final report Markdown
          ├── Safety badge (weather severity summary)
          ├── Disaster badge (has recent disasters yes/no)
          ├── FEMA disaster history section
          ├── Active weather alerts section
          └── 7-day forecast section
```

## Other Tool Execution Paths

### geocode tool
```
_handle_geocode(address)
    └── geocode(address) [src/geocoder.py]
          └── Returns formatted coordinates
```

### weather_alerts tool
```
_handle_weather_alerts(address)
    ├── geocode(address) → lat, lon
    └── get_active_alerts(lat, lon) [src/weather.py]
          └── format_alerts() → Markdown
```

### forecast tool
```
_handle_forecast(address)
    ├── geocode(address) → lat, lon
    └── get_forecast(lat, lon) [src/weather.py]
          └── format_forecast() → Markdown
```

### disaster_history tool
```
_handle_disaster_history(state, county)
    ├── get_state_code(state) [src/disasters.py]
    └── summarize_disasters_for_county(state_code, county)
```

### state_alerts tool
```
_handle_state_alerts(state)
    ├── get_state_code(state) [src/disasters.py]
    └── get_alerts_for_state(state_code) [src/weather.py]
          └── format_alerts() → Markdown
```

## Module Dependency Graph

```
server.py (MCP entry point)
    │
    ├── src/geocoder.py
    │     └── httpx
    │
    ├── src/disasters.py
    │     └── httpx
    │
    ├── src/weather.py
    │     └── httpx
    │
    └── src/report.py
          ├── src/geocoder.py
          ├── src/disasters.py
          └── src/weather.py

All src/*.py are independent leaf modules except report.py
which is the aggregator combining all three data sources.
```

## Data Flow

```
User Address (string)
    │
    ▼
┌─────────────────┐
│ Census Geocoder  │──→ lat, lon + normalized address
└─────────────────┘
    │
    ├────────────────────────────────┐
    ▼                                ▼
┌──────────────────────┐  ┌─────────────────────┐
│ Census Reverse-Geo   │  │ NWS Alerts API       │
│ (county lookup)      │  │ (active alerts)       │
└──────────────────────┘  └─────────────────────┘
    │                           │
    ▼                           ▼
┌──────────────────────┐  ┌─────────────────────┐           ┌─────────────────┐
│ FEMA Declarations    │  │ NWS Forecast API     │           │ 7-Day Forecast  │
│ (disaster history)   │  │ (7-day forecast)      │           │ (formatted)     │
└──────────────────────┘  └─────────────────────┘           └─────────────────┘
    │                           │
    ▼                           ▼
┌──────────────────────┐  ┌─────────────────────┐
│ Disaster Badge +     │  │ Severity Badge +    │
│ History Section      │  │ Alert Details       │
└──────────────────────┘  └─────────────────────┘
    │                           │
    └───────────┬───────────────┘
                ▼
     ┌──────────────────┐
     │ Safety Report    │
     │ (Markdown output)│
     └──────────────────┘
```

## Key Dependencies

| Module | External API | Auth | Rate Limit |
|--------|-------------|------|------------|
| geocoder.py | Census Geocoder (REST) | None | ~5000/day |
| disasters.py | FEMA Open API v2 (REST) | None | None documented |
| weather.py | NWS API (REST) | None (User-Agent required) | ~30 req/s |
| report.py | None (aggregator) | — | — |

## Error Handling Flow

```
Any API failure → exception caught in server.py call_tool()
    │
    └── Returns TextContent with "Error: {message}"
    │
    └── report.py wraps geocode failures with user-friendly guidance
    │
    └── FEMA/NWS failures → empty sections with "Could not retrieve" notice
```