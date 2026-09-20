# Flow — MarketFinder Execution Trace

## CLI Entry → Output

```
User / MCP Host
  │
  ▼
mcp run marketfinder/server.py
  │  ┌────────────────────────────┐
  │  │ server.py                  │
  │  │  main() → mcp.run()        │
  │  │  (FastMCP stdio transport) │
  │  └──────────┬─────────────────┘
  │             │
  ▼             │
MCP Host sends  │
JSON-RPC request│
  │             │
  ▼             ▼
@mcp.tool()
  │
  ├── find_markets(zip, radius_miles)
  │     └── api.search_by_zip(zip, radius_miles)
  │
  ├── filter_by_program(zip, program)
  │     └── api.filter_by_program(zip, program)
  │           └── api.search_by_zip(zip, ...)
  │
  ├── get_market_details(market_id)
  │     └── api.get_market_details(market_id)
  │
  └── find_csa(zip)
        └── api.search_csa(zip, radius_miles)
  │
  ▼
server._format_market_result() / _format_csa_result()
  │
  ▼
Markdown string returned to MCP Host → user
```

## Function-Level Call Chains

### find_markets

```
server.find_markets(zip, radius_miles)
  └─ api.search_by_zip(zip_code, radius_miles)
       ├─ get_client() → httpx.Client
       ├─ client.get(BASE_URL + "/farmersmarket", params={zip, radius})
       │    └─ on success:
       │         resp.json()
       │         [_parse_market(item) for item in data["data"]]
       │         return MarketSearchResult(...)
       │
       └─ on exception (any):
            [_parse_market(m) for m in SIMULATED_MARKETS]
            return MarketSearchResult(...)
  └─ _format_market_result(result)
       └─ iterate result.markets → f-strings with emoji
       └─ return str
```

### filter_by_program

```
server.filter_by_program(zip, program)
  └─ api.filter_by_program(zip_code, program)
       ├─ result = search_by_zip(zip_code)      ← full search
       ├─ if program == "all": return result
       └─ filtered = [m for m in result.markets if _matches_program(m, program)]
            └─ _matches_program(market, program)
                 ├─ mapping: {SNAP→accepts_snap, WIC→accepts_wic, ...}
                 └─ getattr(market, attr, False)
       └─ return MarketSearchResult(..., markets=filtered)
  └─ _format_market_result(result)
```

### get_market_details

```
server.get_market_details(market_id)
  └─ api.get_market_details(market_id)
       ├─ get_client()
       ├─ client.get(BASE_URL + "/farmersmarket", params={id})
       │    └─ on success:
       │         data["data"][0]
       │         _parse_market_details(item)
       │           └─ _parse_market(item) → Market
       │           └─ MarketDetails(**base.model_dump(), schedule, directions, market_link)
       │
       └─ on exception (any):
            find matching simulated market by id
            _parse_market_details(match) or SIMULATED_MARKETS[0]
  └─ format fields inline, return str
```

### find_csa

```
server.find_csa(zip)
  └─ api.search_csa(zip_code, radius_miles=10)
       ├─ get_client()
       ├─ client.get(BASE_URL + "/csa", params={zip, radius})
       │    └─ on success:
       │         [_parse_csa(item) for item in data["data"]]
       │         return CSASearchResult(...)
       │
       └─ on exception:
            [_parse_csa(c) for c in SIMULATED_CSA]
            return CSASearchResult(...)
  └─ _format_csa_result(result)
       └─ iterate result.csa_locations → f-strings
       └─ return str
```

## Module Dependency Graph

```
                  ┌─────────────────────┐
                  │  marketfinder/      │
                  │    server.py        │
                  │  (FastMCP, tools)   │
                  └──────┬──────┬───────┘
                         │      │
           imports       │      │  imports
          ┌──────────────┘      └──────────────┐
          ▼                                     ▼
┌──────────────────┐                ┌──────────────────────┐
│ marketfinder/    │                │ marketfinder/        │
│  api.py          │                │  models.py           │
│ (httpx, fallback)│                │ (Pydantic models)    │
│                  │                │                      │
│ set_client() ◄───┤  tests inject  │ Market               │
│ get_client()     │                │ MarketDetails        │
│ search_by_zip()  │                │ CSALocation          │
│ get_market_...() │                │ MarketSearchResult   │
│ search_csa()     │                │ CSASearchResult      │
│ filter_by_prog() │                │ Program (enum)       │
│ SIMULATED_*      │                └──────────────────────┘
└────────┬─────────┘                         ▲
         │                                   │
         │  imports models                   │
         └───────────────────────────────────┘
                                  ▲
                                  │
                     ┌────────────┴────────────┐
                     │  tests/                  │
                     │  test_marketfinder.py    │
                     │  (pytest + httpx mock)   │
                     │                          │
                     │  set_client(mock_client) │
                     │  → all 4 tools tested    │
                     └─────────────────────────┘

External:
  httpx ──→ USDA Local Food Portal API
            https://www.usdalocalfoodportal.com/api/
            /farmersmarket?zip={zip}&radius={miles}
            /farmersmarket?id={id}
            /csa?zip={zip}&radius={miles}
```

## Data Flow Diagram

```
User ZIP        USDA API          Pydantic Models      Formatted Output
  │                │                   │                    │
  │ zip=97201 ───► │ GET /farmersmarket                    │
  │                │    ?zip=97201                          │
  │                │    &radius=10                          │
  │                │                   │                    │
  │                │ ◄─── JSON array   │                    │
  │                │    {data: [...]}   │                    │
  │                │                   │                    │
  │                │              ┌────┴────┐               │
  │                │              │_parse_  │               │
  │                │              │market() │               │
  │                │              └────┬────┘               │
  │                │                   │                    │
  │                │              Market(id, name,          │
  │                │                address, lat/lng,       │
  │                │                snap, wic, products)    │
  │                │                   │                    │
  │                │         MarketSearchResult             │
  │                │           .count=5                     │
  │                │           .markets=[...]               │
  │                │                   │                    │
  │                │              ┌────┴────┐               │
  │                │              │_format_ │               │
  │                │              │market_  │               │
  │                │              │result() │               │
  │                │              └────┬────┘               │
  │                │                   │                    │
  │◄───────────────┼───────────────────┼─────────────────── │
  │                │        Markdown string                 │
  │                │  "Found 5 markets near 97201..."       │
```

## Error Fallback

```
API call fails (timeout, HTTP error, parse error)
  │
  ▼
catch Exception
  │
  ▼
SIMULATED_MARKETS / SIMULATED_CSA
  │  5 Portland-area markets
  │  3 Portland-area CSAs
  │
  ▼
_parse_market() / _parse_csa()
  │
  ▼
MarketSearchResult / CSASearchResult (same types as real path)
  │
  ▼
_format_market_result / _format_csa_result
  │
  ▼
Markdown output
```

## Test Injection Flow

```
test_marketfinder.py
  │
  ├─ set_client(mock_httpx_client)
  │    │
  │    ▼
  │  api._client = mock
  │
  ├─ search_by_zip("97201", 10)
  │    │
  │    ▼
  │  get_client() → mock
  │  mock.get(...) → returns controlled JSON
  │    │
  │    ▼
  │  assert result.markets[0].market_name == "Test Market 1"
  │
  └─ set_client(error_client)  ← 503 mock
       │
       ▼
     search_by_zip("99999", 10) → exception
       │
       ▼
     assert simulated market returned
```