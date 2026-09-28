# Flow.md — MediMate Execution Flow

## Module Dependency Graph

```
server.py  (MCP server — entry point, tool routing, output formatting)
    │
    ├── medimate/__init__.py  (package info)
    │
    └── medimate/client.py  (OpenFDA HTTP client)
            │
            └── httpx (HTTP library)
                    │
                    └── api.fda.gov  (OpenFDA REST API)

tests/test_medimate.py
    ├── tests client.py (mocked & live)
    └── tests server.py (tool routing & formatting)
```

## Entry Point → Output Flow

### 1. Startup (`server.py`)

```
__main__ (python server.py)
  └── anyio.run(main())
        └── async with server.run(InitializationOptions, stdio_server())
              ├── list_tools() → returns 5 tool definitions
              └── await incoming requests via stdio
```

### 2. Tool Dispatch (every request)

```
MCP client sends JSON-RPC over stdin
  └── server.py receives → routes by tool name
        │
        ├── search_drug(name, limit)
        │     └── client.search_drug("Tylenol", 10)
        │           └── httpx.get("/drug/label.json", params={"search": "openfda.brand_name:Tylenol+OR+openfda.generic_name:Tylenol", "limit": 10})
        │                 └── OpenFDA returns JSON: {meta, results}
        │                       └── _enrich_result() adds _brand_name, _warnings, etc.
        │                             └── _format_result() renders Markdown string
        │                                   └── TextContent(type="text", text=markdown)
        │
        ├── check_adverse_events(name, limit)
        │     └── client.get_adverse_events("Aspirin", 5)
        │           └── httpx.get("/drug/event.json", params={...})
        │                 └── _format_result() → TextContent
        │
        ├── find_generic_alternatives(ingredient, limit)
        │     └── client.find_generic_brands("acetaminophen", 20)
        │           └── httpx.get("/drug/label.json", params={"search": "openfda.substance_name:acetaminophen", "limit": 20})
        │                 └── _format_result() → TextContent
        │
        ├── ndc_lookup(ndc)
        │     └── client.get_by_ndc("12345-6789-0")
        │     │     └── httpx.get("/drug/ndc.json", params={"search": "product_ndc:12345-6789-0"})
        │     │           └── if 0 results → fallback to get_label_by_ndc()
        │     └── _format_result() → TextContent
        │
        └── browse_drugs(page, limit)
              └── client.browse_ingredients(50, 1)
                    └── httpx.get("/drug/label.json", params={"limit": 50, "skip": 0})
                          └── _format_result() → TextContent
```

### 3. Error Path

```
Any tool
  └── httpx raises (timeout, connection error, HTTP error)
        └── caught by call_tool() try/except
              └── TextContent(f"❌ Error: {str(exc)}")
                    └── returned to MCP client as a normal result
```

## Data Flow Diagram

```
User (chat message)
  │
  ▼
LLM decides to call e.g. search_drug(name="Tylenol")
  │
  ▼
JSON-RPC: {"method": "tools/call", "params": {"name": "search_drug", "arguments": {"name": "Tylenol", "limit": 5}}}
  │
  ▼
stdio → server.py → call_tool("search_drug", {"name": "Tylenol", "limit": 5})
  │
  ▼
client.search_drug("Tylenol", 5)
  │  builds: http GET https://api.fda.gov/drug/label.json?search=...&limit=5
  ▼
httpx → internet → OpenFDA API
  │
  ▼
Raw JSON response (262k+ total, nested openfda structure)
  │
  ▼
_enrich_result() → flat _prefixed fields
  │
  ▼
_format_result() → Markdown with emoji headings, bold labels, structured data
  │
  ▼
TextContent → JSON-RPC response → stdio → MCP client → LLM → user sees formatted drug info
```

## Key Design Properties

- **Stateless:** Each tool call is independent. No session state maintained between calls.
- **Fail-closed:** Any network error returns a human-readable message, never a raw exception or empty response.
- **Zero-auth:** No tokens, keys, or environment variables needed. Works out of the box.
- **Self-contained:** Single `pip install` to get all dependencies. No external services to configure.