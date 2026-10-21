# Flow — DocFinder

Execution trace and module dependency graph for the DocFinder MCP agent.

---

## Execution Flow

### Startup
```
entry: docfinder.server.main()
  └─ asyncio.run(_run())
       └─ stdio_server()  ← async context manager
            ├─ read_stream  (stdin)   → MCP JSON-RPC messages
            └─ write_stream (stdout)  ← MCP JSON-RPC responses
       └─ server.run(read_stream, write_stream, InitializationOptions)
            ├─ Handles MCP handshake (initialize/initialized)
            ├─ Exposes capabilities (tools/list)
            └─ Dispatches tools (tools/call)
```

### Request Lifecycle (per tool call)
```
MCP Client
  ↓ JSON-RPC (tools/list)
server._handle_list_tools()
  ↓
ListToolsResult ← TOOL_DEFINITIONS  ─┬─ find_providers
                                      ├─ find_by_name
                                      ├─ find_by_zip
                                      ├─ get_provider_details
                                      └─ find_by_specialty
  ↓
MCP Client receives tool list

MCP Client
  ↓ JSON-RPC (tools/call)
server._handle_call_tool()
  ├─ Match tool name → TOOL_HANDLERS dict
  ├─ Parse arguments
  ├─ Call handler function
  │    ├─ handle_find_providers()
  │    ├─ handle_find_by_name()
  │    ├─ handle_find_by_zip()
  │    ├─ handle_get_provider_details()
  │    └─ handle_find_by_specialty()
  │         └─ Each handler → NppesClient().method()
  │              └─ httpx.Client.get(BASE_URL, params={...})
  │                   └─ JSON response → Provider.from_api()
  │                        └─ Provider dataclass ← typed, structured
  ├─ Format result (provider list or full report)
  └─ Return CallToolResult
```

---

## Module Dependency Graph

```
docfinder/
│
├── server.py          ← MCP server (entry point, tool registration, dispatch)
│   ├── mcp.server.Server          (framework)
│   ├── mcp.server.stdio            (stdio transport)
│   ├── mcp.server.models          (InitializationOptions)
│   ├── mcp.types                   (Tool, ListToolsResult, CallToolResult, etc.)
│   └── docfinder.nppes_client     (↓)
│
├── nppes_client.py    ← API client (HTTP, data parsing)
│   ├── httpx                       (HTTP client)
│   ├── Provider dataclass          (domain model)
│   ├── ProviderAddress dataclass   (address model)
│   ├── ProviderTaxonomy dataclass  (taxonomy model)
│   └── NppesClient                 (API wrapper, 4 search methods)
│
├── tests/
│   ├── test_client.py  ← Unit tests for nppes_client
│   │   ├── pytest
│   │   └── unittest.mock
│   └── test_server.py  ← Unit tests for server
│       ├── pytest
│       └── unittest.mock
│
├── pyproject.toml      ← Project metadata and dependencies
├── requirements.txt    ← Pip dependencies
├── README.md           ← User documentation
├── Decisions.md        ← Architecture decisions (this file)
└── Flow.md             ← Execution flow (this file)
```

---

## Data Flow

### Search by specialty in a city
```
User: "Find cardiologists in Austin TX"
  ↓
find_providers(specialty="cardiology", city="Austin", state="TX")
  ↓
NppesClient.search_providers(
    city="Austin",
    state="TX",
    taxonomy_description="cardiology",
    limit=10
)
  ↓
HTTP GET https://npiregistry.cms.hhs.gov/api/
  ?version=2.1
  &city=Austin
  &state=TX
  &taxonomy_description=cardiology
  &limit=10
  ↓
JSON response:
{
  "result_count": 47,
  "results": [
    {
      "number": "1234567890",
      "enumeration_type": "NPI-1",
      "basic": { "first_name": "Jane", "last_name": "Smith", ... },
      "addresses": [...],
      "taxonomies": [{"code": "207RC0000X", "desc": "Cardiology", "primary": true}]
    },
    ...
  ]
}
  ↓
Provider.from_api()  ← for each result
  ↓
Provider dataclass list
  ↓
Format: bullet-point summary with names, specialties, locations, NPIs
  ↓
CallToolResult → MCP Client → User sees "47 cardiologists in Austin TX"
```

### Full provider detail lookup
```
User: "Get details for NPI 1234567890"
  ↓
get_provider_details(npi="1234567890")
  ↓
NppesClient.get_by_npi("1234567890")
  ↓
HTTP GET https://npiregistry.cms.hhs.gov/api/?version=2.1&number=1234567890
  ↓
Provider.full_report()
  ├─ Display name, credential, NPI, status
  ├─ All taxonomy classifications
  │    └─ Primary specialty (⭐), secondary specialties (•)
  ├─ All addresses (location + mailing)
  │    ├─ Street, suite, city, state, ZIP
  │    └─ Phone, fax
  └─ Identifiers (Medicare, Medicaid, commercial)
  ↓
CallToolResult → MCP Client → Formatted report
```

---

## Key Call Chains

```
                 ┌──────────────────────────┐
                 │    MCP Client (LLM)       │
                 └──────┬───────────────────┘
                        │
                 ┌──────▼───────────────────┐
                 │ server.main()            │
                 │  └─ asyncio.run(_run)    │
                 │       └─ stdio_server()  │
                 └──────┬───────────────────┘
                        │
                 ┌──────▼───────────────────┐
                 │ server._handle_call_tool │
                 └──────┬───────────────────┘
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
    handle_find_providers   handle_get_provider_details
              │                    │
    ┌─────────┴──────────┐  ┌──────┴──────┐
    ▼                    ▼  ▼             ▼
  NppesClient.        NppesClient.    NppesClient.
  search_providers    find_by_zip     get_by_npi
       │                   │              │
       └───────────────────┴──────────────┘
                           │
                    httpx.Client.get()
                           │
                    npiregistry.cms.hhs.gov
                           │
                    JSON → Provider.from_api()
                           │
                    Formatted text → CallToolResult
```

---

## Error Handling Chain

```
_handle_call_tool()
  │
  ├─ Unknown tool name → CallToolResult(is_error=True, "Unknown tool: ...")
  │
  ├─ Missing required argument → KeyError caught → CallToolResult(is_error=True, "Missing required argument: ...")
  │
  ├─ HTTP error from NPPES (timeout, 5xx) → httpx.HTTPError caught → CallToolResult(is_error=True, "Error: ...")
  │
  └─ Provider not found → CallToolResult("No provider found with NPI ...")
```

---

## Tools to Handler Mapping

| Tool Name | Handler Function | NPPES Client Method | Description |
|-----------|-----------------|---------------------|-------------|
| `find_providers` | `handle_find_providers` | `search_providers` | Specialty + city/state |
| `find_by_name` | `handle_find_by_name` | `search_by_name` | Name search |
| `find_by_zip` | `handle_find_by_zip` | `find_by_zip` | ZIP + optional specialty |
| `get_provider_details` | `handle_get_provider_details` | `get_by_npi` | NPI detail lookup |
| `find_by_specialty` | `handle_find_by_specialty` | `search_providers` | Specialty-focused alias |