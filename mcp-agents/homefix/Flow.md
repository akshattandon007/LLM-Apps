# HomeFix — Execution Flow

## MCP Tool Call → Response Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  AI Agent    │────▶│  MCP Client   │────▶│  HomeFix Server   │
│  (Claude/    │◀────│  (stdio/SSE)  │◀────│  (FastMCP)        │
│   Copilot)   │     └──────────────┘     └────────┬─────────┘
└─────────────┘                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │  Tool Dispatcher  │
                                          │  (server.py)      │
                                          └────────┬─────────┘
                                                    │
                     ┌──────────────────────────────┼─────────────────────────────┐
                     ▼                              ▼                             ▼
              ┌─────────────┐               ┌─────────────┐              ┌─────────────┐
              │  Searcher    │               │  Estimator   │              │  Licenser    │
              │  (find pros) │               │  (pricing)   │              │  (license)   │
              └──────┬──────┘               └──────┬──────┘              └──────┬──────┘
                     │                             │                           │
                     ▼                             ▼                           ▼
              ┌─────────────┐               ┌─────────────┐              ┌─────────────┐
              │ Service DB   │               │ Pricing     │              │ License DB  │
              │ (mock pros)  │               │ Model       │              │ (mock)      │
              └─────────────┘               └─────────────┘              └─────────────┘
```

## Detailed Call Chain per Tool

### 1. `find_pros(service_type, zip_code, emergency=False)`

```
server.py (tool_find_pros)
  └─ src/searcher.py: find_pros(service_type, zip_code, emergency)
      └─ src/service_db.py: get_pros_by_service(ServiceType)
          └─ MOCK_PROS filtered → sorted by rating ↓
```

**Returns**: Formatted string with name, rating, reviews, license status,
availability, phone, company, years in business.

---

### 2. `get_estimate(service, description, zip_code)`

```
server.py (tool_get_estimate)
  └─ src/estimator.py: get_estimate(service, description, zip_code)
      ├─ extract_zip_state(zip_code)       → state code
      ├─ BASELINE_PRICES[service]           → (low, high) range
      ├─ REGIONAL_PRICING[state][service]   → multiplier
      └─ infer_complexity_factor(description)
          ├─ Emergency keywords  → +0.25–0.50
          ├─ Complexity keywords → +0.15–0.60
          └─ Simplicity keywords → -0.15–0.30
```

**Returns**: Formatted string with price range, regional factor, complexity
adjustments.

---

### 3. `check_license(company, state)`

```
server.py (tool_check_license)
  └─ src/licenser.py: check_license(company, state)
      ├─ get_pro_by_name(company)          → known pro or None
      └─ _simulate_check(company, state)
          ├─ STATE_LICENSING_BOARDS[state]  → board name
          ├─ Generates license number + expiration
          └─ Builds human-readable summary
```

**Returns**: Formatted string with license number, status (active/expired/
suspended), insurance status (valid/lapsed), bond status (bonded/not_bonded),
verification source.

---

### 4. `summarize_reviews(professional)`

```
server.py (tool_summarize_reviews)
  └─ src/reviewer.py: summarize_reviews(professional)
      ├─ get_pro_by_name(professional)     → pro or None
      ├─ Selects tier template (excellent/good/mixed/poor) by rating
      ├─ Randomly selects 1-2 praise points from _PROS_TEMPLATES
      ├─ Randomly selects 0-2 cons from _CONS_TEMPLATES (fewer for high ratings)
      └─ Combines into 3-4 sentence summary
```

**Returns**: Formatted string with rating, review count, sentiment tier,
narrative summary.

---

### 5. `compare_quotes(service_type, description, zip_code)`

```
server.py (tool_compare_quotes)
  ├─ src/searcher.py: find_pros(service_type, zip_code)
  ├─ src/estimator.py: get_estimate(service_type, description, zip_code)
  └─ Formats top 4 pros with ratings, license status, contact info
```

**Returns**: Formatted string with market estimate + individual quotes from
top providers.

---

### 6. `emergency_services(zip_code)`

```
server.py (tool_emergency_services)
  ├─ For each in [plumber, electrician, locksmith, hvac]:
  │   └─ src/searcher.py: find_pros(type, zip_code, emergency=True)
  └─ Aggregates all results
```

**Returns**: Formatted string with all available emergency pros grouped by
service type.

---

### 7. `book_appointment(pro_name, time_slot, date_str)`

```
server.py (tool_book_appointment)
  └─ src/scheduler.py: book_appointment(pro_name, time_slot, date_str)
      ├─ get_pro_by_name(pro_name)         → validate existence
      ├─ Parse time_slot (24h or 12h format)
      ├─ Generate confirmation number (HF-XXXXXXXX)
      └─ Store in _booked_appointments list
```

**Returns**: Formatted string with confirmation number, professional details,
date/time, status, cancellation policy note.

---

## Dependency Graph

```
server.py (tool definitions)
    │
    ├── src/searcher.py ──── src/service_db.py
    │                               │
    ├── src/estimator.py ───────────┤ (pricing data)
    │                               │
    ├── src/licenser.py ────────────┤ (mock pros)
    │                               │
    ├── src/reviewer.py ────────────┤ (mock pros)
    │
    └── src/scheduler.py ──────────┤ (mock pros)
                                   │
                            src/models.py (types enums)
```

No circular dependencies. Each module depends only on `service_db.py` for data
and `models.py` for types. The MCP server (`server.py`) imports all modules
and wires them into FastMCP tool decorators.

## Data Flow Summary

```
User says: "My pipe burst, find me a plumber in 10001"

  LLM → find_pros(service_type="plumber", zip_code="10001")
       → Returns: [Rapid Rooter ⭐4.7, Fix-a-Pipe ⭐4.3]
  
  LLM → check_license(company="Rapid Rooter Plumbing", state="NY")
       → Returns: ✅ License active, ✅ Insured, ✅ Bonded
  
  LLM → get_estimate(service="plumber", description="burst pipe", zip="10001")
       → Returns: $150 – $1,080 (regional 1.35x, complexity 25%)
  
  LLM → book_appointment(pro_name="Rapid Rooter Plumbing", time_slot="9:00 am")
       → Returns: ✅ Confirmed (HF-A1B2C3D4)
  
User sees: "Found Rapid Rooter Plumbing (⭐4.7, 203 reviews, licensed).
            Estimated $150–$1,080. Booked for tomorrow at 9:00 AM."
```