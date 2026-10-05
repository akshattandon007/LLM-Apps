# Flow.md — RecallGuard Execution & Data Flow

## Module Dependency Graph

```
server.py  ───>  nhtsa_client.py  ───>  httpx (external HTTP)
                     │
                     └──>  RecallRecord (dataclass, no external deps)
```

**Legend**:
- `server.py` = MCP server (tool definitions + request handling)
- `nhtsa_client.py` = NHTSA API client wrapper
- `RecallRecord` = Domain model for a single recall

## Call Chains

### A) Tool Discovery & Listing

```
User A → list_tools()
   └──> Returns 5 tool definitions with JSON Schema
```

### B) get_recall_years

```
User → get_recall_years()
   ├──> server.call_tool("get_recall_years")  
   │      └──> _get_recall_years()
   │             └──> NhtsaClient.get_model_years()
   │                    └──> httpx.GET /api.nhtsa.gov/products/vehicle/modelYears?issueType=r
   │                           └──> JSON response → extract [modelYear] list
   └──> Formatted markdown: "Range: 1949 – 2027 (80 years)"
```

### C) get_recall_makes

```
User → get_recall_makes(model_year="2020")
   ├──> server.call_tool("get_recall_makes", {"model_year": "2020"})
   │      └──> _get_recall_makes("2020")
   │             └──> NhtsaClient.get_makes("2020")
   │                    └──> httpx.GET /api.nhtsa.gov/products/vehicle/makes?modelYear=2020&issueType=r
   │                           └──> JSON response → deduplicate & sort makes
   └──> Formatted list: "Total: 200+ makes\n• FORD\n• TOYOTA\n…"
```

### D) get_recall_models

```
User → get_recall_models(make="TOYOTA", model_year="2020")
   ├──> server.call_tool("get_recall_models", {"make": "TOYOTA", "model_year": "2020"})
   │      └──> _get_recall_models("TOYOTA", "2020")
   │             └──> NhtsaClient.get_models("TOYOTA", "2020")
   │                    └──> httpx.GET /api.nhtsa.gov/products/vehicle/models?make=TOYOTA&modelYear=2020&issueType=r
   │                           └──> JSON response → deduplicate & sort models
   └──> Formatted list: "TOYOTA Models with Recalls — 2020\n• 4RUNNER\n• CAMRY\n…"
```

### E) check_vehicle_recalls (the main action)

```
User → check_vehicle_recalls(make="TOYOTA", model="COROLLA", model_year="2020")
   ├──> server.call_tool("check_vehicle_recalls", {"make": "TOYOTA", "model": "COROLLA", "model_year": "2020"})
   │      └──> _check_recalls("TOYOTA", "COROLLA", "2020")
   │             └──> NhtsaClient.check_vehicle_recalls("TOYOTA", "COROLLA", "2020")
   │                    └──> httpx.GET /api.nhtsa.gov/recalls/recallsByVehicle?make=TOYOTA&model=COROLLA&modelYear=2020
   │                           └──> JSON response → [RecallRecord, …]
   │                                  └──> Each RecallRecord.from_api(dict)
   │                                         └──> .full_report() → formatted text
   │
   │   ┌── [no results] → "✅ No open recalls found"
   │   └── [results]     → f"⚠ N Recall(s) Found" + each .full_report()
   └──> Formatted text response
```

### F) get_recall_by_campaign

```
User → get_recall_by_campaign(campaign_number="20V682000")
   ├──> server.call_tool("get_recall_by_campaign", {"campaign_number": "20V682000"})
   │      └──> _lookup_campaign("20V682000")
   │             └──> NhtsaClient.get_recall_by_campaign("20V682000")
   │                    └──> httpx.GET /api.nhtsa.gov/recalls/campaignNumber?campaignNumber=20V682000
   │                           └──> JSON response → [RecallRecord, …]
   └──> "🔍 Recall Campaign: 20V682000" + full report
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client (AI)                       │
│  (Claude Desktop / Claude Code / any MCP-capable host)   │
└───────────────┬───────────────────────────┬──────────────┘
                │ stdin/stdout (JSON-RPC)    │
                ▼                            ▼
┌──────────────────────────────┐
│     recallguard/server.py     │
│                               │
│  list_tools() ───> tool defs  │
│  call_tool()  ───> dispatch   │
└───────────────┬───────────────┘
                │ method calls
                ▼
┌──────────────────────────────┐
│   recallguard/nhtsa_client   │
│                               │
│  NhtsaClient                  │
│   ├── get_model_years()      │
│   ├── get_makes()            │
│   ├── get_models()           │
│   ├── check_vehicle_recalls()│
│   └── get_recall_by_campaign()│
│                               │
│  RecallRecord (dataclass)    │
│   ├── from_api(dict)         │
│   ├── short_summary()        │
│   └── full_report()          │
└───────────────┬───────────────┘
                │ HTTP GET (HTTPS)
                ▼
┌──────────────────────────────┐
│    api.nhtsa.gov (NHTSA)     │
│  Zero-auth public endpoints  │
└──────────────────────────────┘
```

## Error Handling Flow

```
Tool Call
   │
   ├── HTTP 4xx/5xx ──> httpx.HTTPStatusError ──> caught in call_tool()
   │                                                   └──> "❌ Error: ... Please check your inputs"
   │
   ├── Invalid args ──> KeyError ──> caught in call_tool()
   │                                    └──> "❌ Error: ... Please check your inputs"
   │
   ├── Unknown tool ──> ValueError ──> caught in call_tool()
   │                                    └──> "❌ Error: Unknown tool: ..."
   │
   └── Success ──> formatted markdown text ──> returned to MCP client
```

## Test Flow

```
pytest tests/test_nhtsa.py
   │
   ├── TestRecallRecord
   │   ├── test_from_api_full
   │   ├── test_short_summary
   │   ├── test_full_report
   │   ├── test_park_it_flag
   │   └── test_empty_notes
   │
   ├── TestNhtsaClient (all mocked)
   │   ├── test_get_model_years
   │   ├── test_get_makes_deduplicates
   │   ├── test_get_models_deduplicates
   │   ├── test_check_vehicle_recalls
   │   ├── test_check_vehicle_recalls_empty
   │   ├── test_get_recall_by_campaign
   │   └── test_api_404_raises
   │
   └── TestLiveNhtsaApi (skipped; --live flag)
       ├── test_live_model_years
       └── test_live_recall_check
```