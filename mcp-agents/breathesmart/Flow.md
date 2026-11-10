# Flow — BreatheSmart

## Execution Flow

### 1. Server Startup

```
main()
  └─ anyio.run(_run())
       └─ stdio_server() → (read_stream, write_stream)
            └─ server.run(read_stream, write_stream, InitializationOptions)
```

The MCP server starts, registers its tools, and listens for JSON-RPC messages on stdin/stdout. The `InitializationOptions` advertises `breathesmart` as the server name with version `1.0.0`.

### 2. Tool Dispatch

```
MCP Client (LLM) → stdin (JSON-RPC)
  └─ server.call_tool(name, arguments)
       ├─ get_current_air_quality(lat, lon)
       │    └─ _handle_current_air_quality(lat, lon)
       │         └─ _fetch_air_quality(lat, lon, current_params)
       │              └─ requests.get(AIR_QUALITY_URL, params)
       │         └─ _classify(us_aqi, AQI_LEVELS)
       │         └─ _build_aqi_summary(us_aqi)
       │
       ├─ get_pollen_forecast(lat, lon, days)
       │    └─ _handle_pollen_forecast(lat, lon, days)
       │         └─ _fetch_air_quality(lat, lon, pollen_params, pollen_params, days)
       │         └─ _classify(value, POLLEN_LEVELS) [per pollen type]
       │
       ├─ get_uv_index(lat, lon)
       │    └─ _handle_uv_index(lat, lon)
       │         └─ _fetch_air_quality(lat, lon, ["us_aqi", "uv_index", "uv_index_clear_sky"])
       │         └─ _classify(uv, UV_LEVELS)
       │
       └─ get_health_summary(lat, lon, location_name)
            └─ _handle_health_summary(lat, lon, location_name)
                 └─ _fetch_air_quality(lat, lon, all_params)
                 └─ _classify(us_aqi, AQI_LEVELS)
                 └─ _classify(uv, UV_LEVELS)
                 └─ _classify(value, POLLEN_LEVELS) [per pollen type]
                 └─ Build outdoor activity verdict
```

### 3. Error Path

```
call_tool → try/except chain:
  ├─ requests.RequestException → "Could not reach air quality data service..."
  └─ Exception → "An unexpected error occurred: {e}"
```

## Module Dependency Graph

```
server.py (MCP Server, entry point)
  ├── mcp (SDK)
  │   ├── mcp.types (Tool, TextContent)
  │   ├── mcp.server (Server, InitializationOptions)
  │   └── mcp.server.stdio (stdio_server)
  ├── requests (HTTP client → Open-Meteo API)
  └── anyio (async runtime)

client.py (CLI test tool, standalone)
  └── requests (HTTP client → Open-Meteo API)

tests/test_server.py
  ├── pytest
  ├── unittest.mock (MagicMock, patch)
  └── server (module under test)
```

## Data Flow

```
User Query (LLM)                    Open-Meteo API
     │                                    │
     ▼                                    │
MCP Client                               │
     │                                    │
     ▼                                    │
server.call_tool()                        │
     │                                    │
     ▼                                    │
_fetch_air_quality(lat, lon, params) ──────► GET /v1/air-quality
     │                                    │
     │                                    ◄── JSON response
     ▼                                    │
_classify(value, levels)                   │
     │                                    │
     ▼                                    │
_format_output()                           │
     │                                    │
     ▼                                    │
types.TextContent ◄────────────────────────┘
     │
     ▼
User (via LLM)
```

## Key Call Chains

### Air Quality Query (most common path)

```
list_tools() → [Tool, Tool, Tool, Tool]
call_tool("get_current_air_quality", {lat, lon})
  → _handle_current_air_quality(lat, lon)
    → _fetch_air_quality(lat, lon, current_params)
      → requests.get(AIR_QUALITY_URL, params={"latitude": lat, "longitude": lon, "current": "us_aqi,pm2_5,..."})
      → resp.json()
    → _classify(us_aqi, AQI_LEVELS)  # Returns {label, emoji, value}
    → _build_aqi_summary(us_aqi)     # Returns markdown string
  → [TextContent(markdown)]
```

### Pollen Forecast Query

```
call_tool("get_pollen_forecast", {lat, lon, days})
  → _handle_pollen_forecast(lat, lon, days)
    → _fetch_air_quality(lat, lon, pollen_params, pollen_params, days)
      → requests.get(..., params={"hourly": "grass_pollen,birch_pollen,...", "forecast_days": days})
    → _classify(grass_pollen, POLLEN_LEVELS)  # Per pollen type
    → Compute average from hourly data
  → [TextContent(markdown)]
```

### Health Summary Query

```
call_tool("get_health_summary", {lat, lon, location_name})
  → _handle_health_summary(lat, lon, location_name)
    → _fetch_air_quality(lat, lon, ALL_PARAMS)  # All current params at once
    → _classify(us_aqi, AQI_LEVELS)
    → _classify(uv, UV_LEVELS)
    → _classify(grass_pollen, POLLEN_LEVELS)  # Per active pollen type
    → Build risks list
    → Determine verdict: "All clear" / "Moderate caution" / "Take precautions"
  → [TextContent(markdown)]
```

## Configuration

No environment variables or config files needed. The server uses the Open-Meteo API directly with hardcoded endpoints. Lat/lon is provided per-request by the calling LLM.
