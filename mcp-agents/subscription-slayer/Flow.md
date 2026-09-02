# Flow — Execution trace from MCP tool call to output

This document traces the path of a typical MCP tool call chain through Subscription Slayer.

## Typical user flow

```
[User] ──→ [MCP Client (Claude Desktop/Cursor)] ──→ [Subscription Slayer MCP Server]
```

## Tool call chain (full pipeline)

```
Tool 1: scan_statements(csv_path="/data/statement.csv")
    │
    ├─ server.py @mcp.tool("scan_statements_tool")
    │     │
    │     └─ scanner.py :: scan_statements(csv_path)
    │           │
    │           ├─ Open CSV file (utf-8-sig for BOM handling)
    │           ├─ Detect header row (HEADER_PATTERNS regex)
    │           │   - Date, Description, Amount
    │           │   - Transaction Date, Description, Debit, Credit
    │           │   - Posting Date, Narrative, Value
    │           │
    │           ├─ For each data row:
    │           │   ├─ _parse_date(cell)  → try 10+ date formats
    │           │   ├─ _parse_amount(cell) → strip $, handle EU/US formats
    │           │   ├─ resolve_merchant(description) → merchant_db.py
    │           │   │     ├─ Direct match in ALIAS_MAP
    │           │   │     └─ Substring match fallback
    │           │   └─ build Charge(...)
    │           │
    │           └─ Return ScanResult(charges=[...], errors=[...])
    │
    └─ → JSON string of charges
          [
            {date: "2025-01-01", description: "SPOTIFY PREMIUM", amount: 10.99, merchant: "spotify"},
            {date: "2025-01-15", description: "NETFLIX", amount: 15.49, merchant: "netflix"},
            ...
          ]


Tool 2: detect_recurring(charges_json)
    │
    ├─ server.py @mcp.tool("detect_recurring_tool")
    │     │
    │     └─ categorizer.py :: detect_recurring(charges)
    │           │
    │           ├─ Group charges by merchant (known merchants)
    │           ├─ Group charges by description (unknown merchants)
    │           ├─ For each group with ≥2 occurrences:
    │           │   ├─ _detect_frequency(dates) → Monthly/Yearly/Weekly/Quarterly
    │           │   │     ├─ Sort dates
    │           │   │     ├─ Calculate average interval
    │           │   │     └─ Classify: 25-35d → monthly, 355-375d → yearly, etc.
    │           │   ├─ Compute average amount
    │           │   └─ Build Subscription(...)
    │           ├─ Deduplicate by merchant name
    │           └─ Sort by amount (descending)
    │
    └─ → JSON string of subscriptions
          [
            {merchant: "Netflix", amount: 15.49, frequency: "monthly", occurrences: 3, ...},
            {merchant: "Spotify", amount: 10.99, frequency: "monthly", occurrences: 3, ...},
            ...
          ]


Tool 3: categorize(subscriptions_json)
    │
    ├─ server.py @mcp.tool("categorize_tool")
    │     │
    │     └─ categorizer.py :: categorize(subscriptions)
    │           │
    │           ├─ For each Subscription:
    │           │   ├─ _assign_category(merchant) → merchant_db lookup
    │           │   ├─ _compute_annual_cost(amount, frequency)
    │           │   │     monthly × 12, yearly × 1, weekly × 52, quarterly × 4
    │           │   └─ Build CategorizedSub(...)
    │           └─ Sort by annual cost (descending)
    │
    └─ → JSON string of categorized subscriptions
          [
            {merchant: "Netflix", category: "streaming", annual_cost: 185.88, ...},
            {merchant: "Spotify", category: "music", annual_cost: 131.88, ...},
            ...
          ]


Tool 4: estimate_annual_cost(categorized_json)
    │
    ├─ server.py @mcp.tool("estimate_annual_cost_tool")
    │     │
    │     └─ categorizer.py :: estimate_annual_cost(categorized_subs)
    │           │
    │           ├─ For each CategorizedSub: accumulate annual_cost by category
    │           ├─ Sum overall total
    │           └─ Return formatted summary (str)
    │
    └─ → Human-readable cost summary
          ── Annual Cost Summary ──
          Streaming           $185.88/yr
          Music               $131.88/yr
          TOTAL               $317.76/yr
          Monthly equivalent  $26.48/mo


Tool 5: identify_unused(categorized_json, user_answers_json)
    │
    ├─ server.py @mcp.tool("identify_unused_tool")
    │     │
    │     └─ categorizer.py :: identify_unused(categorized_subs, user_answers)
    │           │
    │           ├─ For each CategorizedSub:
    │           │   └─ If merchant.lower() in user_answers and user_answers[key]==False:
    │           │         → Add to forgotten list
    │           └─ Return forgotten names (json)
    │
    └─ → ["Netflix", "Spotify"]


Tool 6: get_cancellation_info(service_name="Netflix")
    │
    ├─ server.py @mcp.tool("get_cancellation_info_tool")
    │     │
    │     └─ canceller.py :: get_cancellation_info(service_name)
    │           │
    │           └─ merchant_db.py :: get_cancellation_for(service_name)
    │                 │
    │                 ├─ Lookup in MERCHANT_DB dictionary
    │                 ├─ Fallback: alias lookup in ALIAS_MAP
    │                 └─ Return cancellation info or unknown message
    │
    └─ → Cancellation instructions:
          ── Cancel Netflix ──
            Category:     streaming
            Price:        $15.49/month
            URL:          https://www.netflix.com/YourAccount
            Process:      Account > Cancel Membership > Confirm.


Tool 7: track_trials(categorized_json)
    │
    ├─ server.py @mcp.tool("track_trials_tool")
    │     │
    │     └─ categorizer.py :: track_trials(categorized_subs)
    │           │
    │           ├─ For each CategorizedSub:
    │           │   ├─ If is_trial and trial_end < today:  "CONVERTED"
    │           │   ├─ If is_trial and trial_end in 3 days: "ends soon"
    │           │   └─ If is_trial and trial_end > 3 days:  "still running"
    │           └─ Return warnings list
    │
    └─ → "⚠ Duolingo Plus trial ends in 2 day(s) on 2025-03-25..."

```

## Data flow diagram

```
CSV File ──→ scanner.py ──→ [Charge, Charge, ...]
                                │
                                ▼
                          detect_recurring()
                                │
                                ▼
                     [Subscription, ...]
                                │
                                ▼
                          categorize()
                                │
                                ▼
                ┌─────[CategorizedSub, ...]─────┐
                │           │            │       │
                ▼           ▼            ▼       ▼
           estimate      identify      get_    track_
           _annual       _unused       cancel  _trials
           _cost                       _info
                │           │            │       │
                ▼           ▼            ▼       ▼
           Cost       Forgotten     Cancellation  Trial
           Summary    List          Info          Warnings
```

## Error flow

```
scan_statements("/nonexistent.csv")
    │
    └─ FileNotFoundError:
         Result.errors = ["File not found: /nonexistent.csv"]
         Result.charges = []
         → Graceful: server returns empty result with error message
```

```
scan_statements("bad_format.csv")
    │
    └─ Parse error on row:
         Result.errors = ["Parse error on row: [...]"]
         Result.charges = [valid rows]
         → Partial: good rows are returned, bad rows logged
```

## MCP Protocol (for MCP clients)

Subscription Slayer uses stdio transport by default. The MCP client connects via:

```json
{
  "mcpServers": {
    "subscription-slayer": {
      "command": "python",
      "args": ["/path/to/server.py", "stdio"]
    }
  }
}
```

Each tool call is a JSON-RPC request over stdin. The server responds over stdout. For SSE transport (`server.py sse`), the server listens on `http://localhost:8000` for HTTP POST requests.

## CLI equivalent (for testing)

```bash
# Full pipeline via CLI
python main.py pipeline tests/data/statement.csv

# Step by step
python main.py scan tests/data/statement.csv
python main.py detect-recurring tests/data/statement.csv
python main.py categorize tests/data/statement.csv
python main.py annual-cost tests/data/statement.csv
python main.py cancel netflix
```