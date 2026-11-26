# Flow — Recall Alert 🚨⚠️

## Execution Architecture

```
                   ┌─────────────────────────────────────────────┐
                   │              MCP Client (AI Agent)           │
                   │  Calls check_food_recall() or                │
                   │  check_vehicle_recall() via MCP protocol     │
                   └──────────────┬──────────────────────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │      server.py (FastMCP)      │
                   │  ┌────────────────────────┐   │
                   │  │ check_food_recall()    │   │
                   │  │   - validates params   │   │
                   │  │   - catches exceptions │   │
                   │  │   - formats output     │   │
                   │  └───────────┬────────────┘   │
                   │  ┌────────────────────────┐   │
                   │  │ check_vehicle_recall() │   │
                   │  │   - validates VIN      │   │
                   │  │   - catches exceptions │   │
                   │  │   - formats output     │   │
                   │  └───────────┬────────────┘   │
                   └──────────────┼────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐
   │ recall_client.py │  │ recall_client.py │  │    Formatting     │
   │ search_          │  │ search_vehicle_  │  │  _format_recall() │
   │ food_recall()    │  │ recall(vin)      │  │  → markdown       │
   │                  │  │                  │  │  string w/ emoji  │
   │  → GET /drug/    │  │  → GET /recalls/ │  │                   │
   │    enforcement   │  │    recallsBy     │  │                   │
   │    .json         │  │    Vehicle?vin=  │  │                   │
   └────────┬─────────┘  └────────┬─────────┘  └────────────────────┘
            │                     │
            ▼                     ▼
   ┌──────────────────┐  ┌──────────────────┐
   │  openFDA API     │  │  NHTSA API       │
   │  (api.fda.gov)   │  │  (api.nhtsa.gov) │
   │  No key needed   │  │  No key needed   │
   └──────────────────┘  └──────────────────┘
```

## Module Dependency Graph

```
server.py
   ├── recall_client.py
   │     ├── RecallResult (dataclass)
   │     ├── set_client()
   │     ├── _get_client()
   │     ├── search_food_recall(product_name, limit)
   │     │     ├── _normalize_fda_recall(entry)
   │     │     └── httpx.Client.get()
   │     └── search_vehicle_recall(vin)
   │           ├── _normalize_nhtsa_recall(entry)
   │           └── httpx.Client.get()
   │
   ├── FastMCP
   ├── check_food_recall()  [MCP tool]
   │     └── _format_recall()
   ├── check_vehicle_recall()  [MCP tool]
   │     └── _format_recall()
   └── CLI entry: if __name__ == "__main__": mcp.run()

test_recall_alert.py
   ├── recall_client.py (real imports)
   └── httpx.MockTransport (injectable)
```

## Function-Level Call Chains

### Path 1: Food/Drug Recall Search

```
check_food_recall("peanut butter", limit=10) ← MCP tool entry
  │
  ├── search_food_recall("peanut butter", limit=10)
  │     │
  │     ├── → HTTP GET https://api.fda.gov/drug/enforcement.json
  │     │     ?search=product_description:peanut+butter
  │     │     &limit=10
  │     │
  │     ├── ← JSON response (list of enforcement entries)
  │     │
  │     └── for each entry:
  │           └── _normalize_fda_recall(entry)
  │                 ├── Extract: product_description, reason_for_recall,
  │                 │          remedial_actions, recalling_firm,
  │                 │          classification, report_date, recall_number
  │                 ├── Parse: report_date "20251101" → "2025-11-01"
  │                 ├── Build: description from firm + reason
  │                 └── Return: RecallResult(...)
  │
  └── for each RecallResult:
        └── _format_recall(r)
              └── Format: "**{product}**\n📅 {date} | ⚠️ {cls}\n{desc}\n🔧 Remedy: {remedy}\n🔗 {url}"
```

### Path 2: Vehicle Recall Search

```
check_vehicle_recall("1HGCM82633A004352") ← MCP tool entry
  │
  ├── Validate: len(vin) == 17? (if no: return error message)
  │
  ├── Clean: strip(), upper()
  │
  ├── search_vehicle_recall("1HGCM82633A004352")
  │     │
  │     ├── → HTTP GET https://api.nhtsa.gov/recalls/recallsByVehicle
  │     │     ?vin=1HGCM82633A004352
  │     │
  │     ├── ← JSON response (list of campaign entries)
  │     │
  │     └── for each entry:
  │           └── _normalize_nhtsa_recall(entry)
  │                 ├── Extract: Component, Summary, Manufacturer,
  │                 │          NHTSACampaignNumber, Remedy
  │                 ├── Build: product from Manufacturer + Component
  │                 ├── Fallback: date = today if no date field
  │                 └── Return: RecallResult(source="NHTSA", ...)
  │
  └── for each RecallResult:
        └── _format_recall(r)
```

### Path 3: No Recalls Found (both tools)

```
check_food_recall("nonexistent product")
  ├── search_food_recall(...) returns []
  └── Return: "✅ No recalls found for 'nonexistent product'..."

check_vehicle_recall("1HGCM82633A004352")
  ├── search_vehicle_recall(...) returns []
  └── Return: "✅ VIN `1HGCM82633A004352` has no open safety recalls..."
```

### Path 4: API Error

```
check_food_recall("peanut")
  ├── search_food_recall(...)
  │     └── httpx raises HTTPStatusError(500)
  └── Caught by try/except
        └── Return: "❌ Error searching FDA recalls: 500 Internal Server Error"
```

## Data Flow Diagram

```
User Query (via AI Agent)
        │
        ▼
┌─────────────────────────────┐
│  "Check if Jif peanut       │
│   butter has been recalled" │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  check_food_recall(product_ │
│  name="Jif peanut butter")  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  HTTP GET → api.fda.gov     │
│  /drug/enforcement.json     │
│  ?search=product_           │
│  description:Jif+peanut     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  JSON Response              │
│  { results: [ {             │
│    product_description,     │
│    reason_for_recall,       │
│    classification, ... } ]} │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  _normalize_fda_recall()    │
│  ──────────────────────     │
│  Raw FDA JSON               │
│      → RecallResult         │
│        (source, product,    │
│         description, date,  │
│         classification,     │
│         remedy, url)        │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  _format_recall()           │
│  ──────────────────────     │
│  RecallResult → Markdown:   │
│  **Jif Creamy Peanut        │
│  Butter 16oz**              │
│  📅 2025-11-01 | ⚠️ Class I │
│  Firm: J.M. Smucker Co.     │
│  Reason: Potential          │
│  salmonella contamination   │
│  🔧 Remedy: Full refund     │
│  🔗 https://...             │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Return to AI Agent         │
│  ──────────────────────     │
│  ⚠️ 1 recall(s) found for   │
│  'Jif peanut butter'        │
│  (source: openFDA)          │
│  ---                        │
│  ### 1. **Jif Creamy...**   │
│  ...                        │
└─────────────────────────────┘
```

## Key Design Decisions (mapped to Flow)

1. **Source segregation**: Two separate client functions (`search_food_recall`, `search_vehicle_recall`) keep data sources independent — no shared API logic.
2. **Normalized schema**: Both data sources map to `RecallResult` with a `source` field, so the server layer treats them uniformly.
3. **Formatting at the server layer**: `_format_recall()` lives in `server.py` (not `recall_client.py`) because formatting is a UI concern — the client returns pure data objects.
4. **Error isolation**: Each MCP tool has its own `try/except` around the client call, preventing one API failure from crashing the other tool.
