# Flow.md — SubsSleuth

## Execution flow and module dependency graph.

### Entry point

```
__main__.py  (main() → argparse dispatch)
```

The user invokes `python -m subs_sleuth <command> [options]` or `python -m subs_sleuth all --demo` for the full pipeline.

---

### Command: `scan` (Scanner Agent)

```
__main__.py:_cmd_scan()
  │
  ├─ scanner_agent.scan_demo()           [--demo path]
  │     └─ returns ScanReport (list of Subscription objects)
  │
  └─ scanner_agent.scan_email()          [--email + --password path]
        ├─ utils.connect_imap()
        │     └─ imaplib.IMAP4_SSL()      [stdlib]
        ├─ utils.search_subscription_emails()
        │     └─ imaplib.IMAP4_SSL.search()  [per keyword]
        ├─ scanner_agent._extract_subscription()
        │     ├─ utils.llm_complete()    [if LLM key set]
        │     │     └─ httpx.post() → LLM API → JSON parse
        │     └─ _heuristic_extract()    [fallback]
        │           └─ Known merchant dictionary match
        └─ returns ScanReport
```

**Call chain:**
1. `__main__.main()` → `_parse_args()` → identifies subcommand
2. `_cmd_scan()` reads args, calls appropriate scanner function
3. `scan_email()` opens IMAP connection, searches 15 subscription keywords
4. Each matching email → `_extract_subscription()` runs LLM extraction (or heuristic fallback)
5. Returns aggregated `ScanReport` → serialized as JSON

---

### Command: `cancel` (Cancellation Agent)

```
__main__.py:_cmd_cancel()
  │
  ├─ scanner_agent.scan_demo()           [--demo path]
  │     └─ list[Subscription]
  │
  ├─ load JSON from file                 [--input path]
  │     └─ list[Subscription]
  │
  └─ cancel_agent.research_all(subscriptions)
        └─ For each Subscription:
              cancel_agent.research_cancellation(sub)
                ├─ _known_cancellation(merchant)
                │     └─ Lookup in hardcoded dict → CancellationGuide
                │
                └─ [if not found]:
                      ├─ utils.web_search(query)
                      │     └─ httpx.get() → DuckDuckGo lite → parse results
                      └─ utils.llm_complete()  [if key set]
                            └─ httpx.post() → LLM API
                      └─ Returns CancellationGuide (steps, method, difficulty)
```

**Call chain:**
1. Gets subscription list (demo, file, or single merchant)
2. For each subscription: checks known database first (instant)
3. If unknown: searches web for "how to cancel X subscription"
4. If LLM key set: synthesises search results into structured guide
5. Gathers all CancellationGuide objects → JSON output

---

### Command: `verify` (Verification Agent)

```
__main__.py:_cmd_verify()
  │
  ├─ verify_agent.verify_demo()          [--demo path]
  │     ├─ scanner_agent.scan_demo()
  │     └─ Hardcoded demo StatementLine list
  │
  └─ verify_agent.verify_subscriptions(subs, lines)
        └─ For each Subscription:
              For each StatementLine:
                _match_score(sub, line)
                  ├─ Token overlap: sub.merchant ∩ line.description
                  └─ Amount closeness: |sub.amount - |line.amount||
              └─ Best match → VerificationReport
```

**CSV parsing (when bank statement provided):**
```
parse_statement_csv(csv_text)
  ├─ csv.DictReader()                    [stdlib]
  ├─ _normalize_columns(fieldnames)
  │     └─ Maps "Transaction Date" → "date", "Merchant" → "description", etc.
  └─ Returns list[StatementLine]
```

---

### Command: `all` (Full Pipeline)

```
__main__.py:_cmd_all()
  │
  ├─ Phase 1: scan
  │     └─ scanner_agent.scan_demo() or scan_email()
  │           └─ ScanReport + list[Subscription]
  │
  ├─ Phase 2: cancel
  │     └─ cancel_agent.research_all(subscriptions)
  │           └─ list[CancellationGuide]
  │
  ├─ Phase 3: verify
  │     └─ verify_agent.verify_demo(subscriptions)
  │           └─ list[VerificationReport]
  │
  └─ FullReport(scan, guides, verification)
        └─ .to_json() → JSON output
```

---

### Module dependency graph

```
__main__.py
  ├── subs_sleuth/__init__.py        (version string)
  ├── subs_sleuth/models.py          (dataclasses — no deps beyond stdlib)
  ├── subs_sleuth/utils.py           (LLM client, IMAP client, web search, SimpleDB)
  │     └── httpx (optional external dep)
  ├── subs_sleuth/scanner_agent.py   → utils.py, models.py
  ├── subs_sleuth/cancel_agent.py    → utils.py, models.py
  └── subs_sleuth/verify_agent.py    → models.py  (+ csv/io stdlib)
```

### External APIs (all free, no-auth tiers)
| API | Endpoint | Auth | Rate Limit |
|-----|----------|------|-----------|
| LLM (Groq) | api.groq.com | API key (optional) | Free tier |
| DuckDuckGo (web search) | lite.duckduckgo.com | None | Best-effort |
| IMAP (Gmail/Outlook) | imap.gmail.com | App password | Vendor limits |

### Agent coordination pattern

```
┌───────────────────────────────────────────────────────────┐
│                      __main__.py                          │
│                   (orchestrator)                          │
└──┬────────────────┬──────────────────┬────────────────────┘
   │                │                  │
   ▼                ▼                  ▼
┌────────┐    ┌───────────┐     ┌────────────┐
│Scanner │───▶│  Cancel   │     │  Verify    │
│ Agent  │    │  Agent    │     │  Agent     │
└────────┘    └───────────┘     └────────────┘
    │              │                  │
    ▼              ▼                  ▼
 Subscription  Cancellation       Verification
 objects       Guide objects      Report objects
    │              │                  │
    └──────────────┴──────────────────┘
         FullReport (JSON)
```

Each agent is independently runnable (`scan`, `cancel`, `verify` subcommands) or orchestrated via `all`. Agent outputs are JSON-serializable dataclasses — the pipe is text, not shared memory. This makes each agent testable in isolation and replaceable without affecting the others.