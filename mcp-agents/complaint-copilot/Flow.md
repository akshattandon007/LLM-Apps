# Flow — Complaint Copilot Execution Trace

How data flows from an MCP tool call through the system to the output.

---

## Dependency Graph

```
server.py (FastMCP entry point)
├── src/models.py          ← Pydantic models (no deps)
├── src/rights.py          ← Rights database
│   └── src/models.py
├── src/ombudsman.py       ← Ombudsman finder
│   └── src/models.py
├── src/drafter.py         ← Complaint letter generator
│   ├── src/models.py
│   └── src/rights.py
├── src/tracker.py         ← Status tracking (in-memory)
│   └── src/models.py
└── src/escalation.py      ← Regulatory referral generator
    ├── src/models.py
    └── src/ombudsman.py
```

All arrows point from importer to imported module. No circular dependencies.

---

## Tool Call Chains

### 1. `draft_complaint(company, issue, amount, outcome, issue_type, country)`

```
User/Client
  │  MCP call: draft_complaint(...)
  ▼
server.py: draft_complaint()          ← parses args, resolves enums
  │
  ├─ src/drafter.py: draft_complaint()
  │   │
  │   ├─ src/models.py: IssueType, Country  ← enum resolution
  │   │
  │   └─ src/rights.py: get_rights()        ← lookup rights (optional)
  │       │
  │       └─ src/models.py: StatutoryRight  ← typed return
  │
  └─ Returns formatted complaint letter string
```

**Output:** A complete formal complaint letter with:
- Complaint reference number
- Date
- Company address block
- Issue description
- Legal basis section (if issue_type + country provided)
- Desired resolution
- Response deadline (14 calendar days)
- Signature block

---

### 2. `find_ombudsman(company, issue_type)`

```
User/Client
  │  MCP call: find_ombudsman(...)
  ▼
server.py: find_ombudsman()          ← parses args, resolves issue_type
  │
  └─ src/ombudsman.py: find_ombudsman()
      │
      ├─ 1. Check _COMPANY_OVERRIDES dict (case-insensitive key match)
      │     → If found: return single-entry list
      │
      ├─ 2. Check _ISSUE_FALLBACKS dict (by issue type)
      │     → If found: return multi-entry list
      │
      └─ 3. Return _GENERAL_FALLBACK
```

**Output:** Formatted list of 1–4 ombudsmen/regulators with:
- Name
- URL
- Jurisdiction
- Eligibility criteria
- Optional notes

---

### 3. `statutory_rights(issue_type, country)`

```
User/Client
  │  MCP call: statutory_rights(...)
  ▼
server.py: statutory_rights()        ← parses args, resolves enums
  │
  └─ src/rights.py: get_rights()
      │
      └─ src/models.py: StatutoryRight
```

**Output:** Consumer rights information with:
- Right title
- Summary (plain English)
- Legal deadline to claim
- Legal reference (statute/regulation)
- Detailed guidance

---

### 4. `track_complaint(company, reference)`

```
User/Client
  │  MCP call: track_complaint(...)
  ▼
server.py: track_complaint()         ← parses args
  │
  └─ src/tracker.py: track_complaint()
      │
      ├─ reference provided + exists in _store?
      │   → Return current status with timeline
      │
      ├─ reference provided + not in _store?
      │   → Create new tracker entry, return status
      │
      └─ no reference?
          → Return escalation stage template
```

**Output:** Status report or escalation template with next action.

---

### 5. `escalate_to_regulator(company, ombudsman, case_summary)`

```
User/Client
  │  MCP call: escalate_to_regulator(...)
  ▼
server.py: escalate_to_regulator()   ← parses args
  │
  ├─ src/ombudsman.py: find_ombudsman()   ← try to find URL for ombudsman
  │
  └─ src/escalation.py: escalate_to_regulator()
      │
      └─ Returns formatted referral letter
```

**Output:** Formal regulatory referral letter with:
- Recipient (ombudsman/regulator name)
- Case summary
- Grounds for referral (3 enumerated points)
- Relief sought (3 enumerated requests)
- Signature block

---

## Data Flow Diagram

```
                    ┌─────────────────────────┐
                    │    MCP Client (Claude,   │
                    │   Cursor, custom agent)  │
                    └───────────┬─────────────┘
                                │ stdio transport
                                ▼
                    ┌─────────────────────────┐
                    │      server.py          │
                    │   (FastMCP, 5 tools)    │
                    └───┬───┬───┬───┬───┬────┘
                        │   │   │   │   │
         ┌──────────────┘   │   │   │   └──────────────┐
         ▼                  ▼   ▼   ▼                  ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ drafter  │    │ ombudsman│    │escalation│
   │  .py     │    │   .py    │    │   .py    │
   └────┬─────┘    └────┬─────┘    └────┬─────┘
        │               │               │
        ▼               ▼               ▼
   ┌──────────┐    ┌──────────┐
   │ rights   │    │ models   │
   │   .py    │    │   .py    │
   └──────────┘    └──────────┘
```

---

## State Management

```
tracker.py: _store (module-level dict)
  ├─ Key: complaint reference string (e.g. "CC-20260311-ABC123")
  └─ Value: ComplaintStatus object
       ├─ reference, company
       ├─ status, created_at, updated_at
       ├─ notes[] (timeline entries)
       └─ next_action (string prompt for the user)
```

**Ephemeral:** Data lives only as long as the Python process. No persistence in v0.1.
