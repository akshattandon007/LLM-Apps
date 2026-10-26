# Flow.md

## Execution Trace: fuel-tracker MCP Server

### Entry Point

```
python -m fuel_tracker.server
               │
               ▼
         fuel_tracker.server.main()
               │
               ├── sys.argv has "--country" flag?
               │     YES → get_country_fuel_prices(sys.argv[2]) → print → exit
               │
               └── NO → server.run(transport="stdio")
                           │
                           ▼
                    MCP stdio transport starts
                    reads JSON-RPC messages from stdin
                    writes JSON-RPC responses to stdout
```

### Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host (Claude, etc.)                  │
│  sends JSON-RPC request → {"method":"tools/call",          │
│     "params":{"name":"get_fuel_prices","arguments":{}}}    │
└─────────────────────┬───────────────────────────────────────┘
                      │ stdin
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCPServer (mcp 2.x)                        │
│  deserialises request → routes to registered tool          │
│  @server.tool() decorator maps name → function             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Tool Function                              │
│                                                             │
│  get_fuel_prices()                                          │
│    → _get_client()  (lazy-init FuelWideClient singleton)    │
│    → client.get_all_prices()                                │
│    → formatter: dict → markdown string                      │
│    → return str                                             │
│                                                             │
│  get_country_fuel_prices(country_code)                      │
│    → _get_client()                                          │
│    → client.get_country_prices(country_code)                │
│    → HTTP 451? → user-friendly error message                │
│    → json.dumps(data, indent=2)                             │
│    → return str                                             │
│                                                             │
│  get_nearby_stations(country, lat, lon, ...)                │
│    → _get_client()                                          │
│    → client.get_stations(country, lat, lon, ...)            │
│    → HTTP 451? → user-friendly error message                │
│    → formatter: list → markdown (capped at 50)              │
│    → return str                                             │
└─────────────────────┬───────────────────────────────────────┘
                      │ return str
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCPServer (mcp 2.x)                        │
│  wraps result in JSON-RPC response                          │
│  {"jsonrpc":"2.0","id":1,"result":{"content":[...]}}       │
└─────────────────────┬───────────────────────────────────────┘
                      │ stdout
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host receives response               │
│  parses content → presents to user                          │
└─────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
fuel_tracker/__init__.py       (package marker, no code)
         │
         ▼
fuel_tracker/server.py         (ALL logic in one file)
         │
         ├── from mcp.server.mcpserver import MCPServer
         ├── import httpx
         ├── import json, sys, dataclasses
         │
         ├── FuelWideClient          (HTTP client)
         │    ├── get_all_prices()    GET /api/fuel-prices
         │    ├── get_country_prices() GET /api/fuel-prices/{country}
         │    └── get_stations()       GET /api/stations/{country}?near=lat,lon
         │
         ├── MCPServer instance
         │    ├── @server.tool(get_fuel_prices)
         │    ├── @server.tool(get_country_fuel_prices)
         │    └── @server.tool(get_nearby_stations)
         │
         └── main()                   entry point
              ├── CLI mode (--country flag)
              └── MCP stdio mode

tests/test_server.py
         │
         ├── from fuel_tracker.server import ...
         ├── import pytest
         ├── import unittest.mock
         │
         ├── TestFuelWideClient
         │    ├── test_get_all_prices_happy_path
         │    └── test_get_country_prices
         │
         └── TestMCPTools
              ├── test_get_fuel_prices_returns_formatted_output
              ├── test_get_fuel_prices_empty
              ├── test_get_country_fuel_prices
              ├── test_get_nearby_stations
              └── test_get_nearby_stations_empty
```

### Data Flow

```
User question ──► AI Assistant ──► MCP Client ──► fuel-tracker (stdio)
  "What are fuel                           │
   prices in Germany?"                     │
                    ◄───────────────────────┘
                    │ response (markdown)
                    ▼
              AI parses markdown
                    │
                    ▼
              "In Germany, petrol 95 is €1.74/L
               and diesel is €1.62/L."
```

### Error Flow

```
Tool call ──► FuelWideClient.get_country_prices("XX")
                  │
                  ├── HTTP 200 → return parsed JSON → format → return str
                  │
                  ├── HTTP 451 → return "Unavailable For Legal Reasons" message
                  │
                  ├── HTTP 4xx/5xx → httpx.HTTPStatusError caught
                  │                 → return f"Error: {exc}" string
                  │
                  └── Network error → httpx.RequestError → propagate as traceback
```

### Key Design Properties

1. **Lazy initialisation**: `FuelWideClient` is created on first tool call, not on import
2. **Connection reuse**: Single `httpx.Client` with connection pooling reused across all tool calls
3. **Stateless**: No per-session state — every tool call is independent
4. **Deterministic formatting**: Same input always produces same output format
5. **Conservative output**: Station lists capped at 50 entries to bound token usage