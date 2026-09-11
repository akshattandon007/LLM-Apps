# Decisions — Complaint Copilot

Every architectural choice documented with the rationale behind it.

---

## 1. MCP over standalone web app

**Decision:** Expose complaint functionality as an MCP server (stdio transport) rather than a standalone FastAPI web app.

**Why:** The target audience is everyday people who will interact via an AI assistant (Claude Desktop, Cursor, custom agent). An MCP server plugs directly into those assistants — the user says "draft a complaint about my delayed flight" and the agent calls `draft_complaint`. A web app would require the user to visit a URL, fill in forms, and copy-paste results. The MCP pattern removes all friction.

**Trade-off:** Less accessible to users who don't run an MCP-compatible client. Mitigation: the CLI entry point (`main.py`) works standalone for testing and manual use.

---

## 2. Simulated / local data over live APIs

**Decision:** Rights database, ombudsman mappings, and complaint tracking are all local/in-memory in v0.1.

**Why:** Zero external dependencies, zero API keys, zero latency, works offline. The rights database covers 7 issue types × 3 countries (21 entries) — enough to be genuinely useful. The ombudsman database has 20+ company-specific overrides plus issue-type fallbacks.

**Trade-off:** Rights may drift from current legislation. Ombudsman URLs may change. Mitigation: update `rights.py` and `ombudsman.py` as needed; the database is plain Python dicts, trivially editable.

**Future option:** Add a live mode that queries an LLM or a regulatory API for current information, with simulated as fallback.

---

## 3. Template-based drafting over LLM generation

**Decision:** Complaint letters are generated from templates with legal references, not by calling an LLM.

**Why:** Deterministic, predictable output. No API cost. No latency. No prompt injection risk. The template includes the correct legal references, deadline, and structure every time.

**Trade-off:** Less personalised tone. Mitigation: the user can customise the letter before sending. An LLM-enhanced mode could be added later as an optional upgrade.

---

## 4. Country-specific rights approach

**Decision:** Rights are stored as a flat dict keyed by `(issue_type, country)` tuple.

**Why:** Simple, fast, exhaustive. Every combination either has an entry or returns None. No inheritance, no fallback chains, no complex resolution logic. Adding a new country means adding 7 entries to the dict.

**Countries in v0.1:** US, UK, EU. These cover the three major consumer protection regimes. EU is treated as a single jurisdiction because the core consumer directives (EU261, Consumer Sales Directive, PSD2) apply across all member states.

---

## 5. In-memory complaint tracking

**Decision:** Complaint status is stored in a plain Python dict, not a database.

**Why:** No database setup, no migrations, no SQL. The tracker is a convenience feature — it provides a status template and tracks escalation stages. In v0.1, ephemeral storage is acceptable because the MCP client typically manages conversation state.

**Trade-off:** Data is lost on server restart. Mitigation: upgrade to SQLite when persistence is needed.

---

## 6. FastMCP over raw MCP SDK

**Decision:** Use `mcp.server.fastmcp.FastMCP` (the high-level FastMCP API from the `mcp` library).

**Why:** Clean decorator-based tool registration, automatic schema generation from type hints, no boilerplate. `@mcp.tool()` is all we need.

**Pin:** `mcp<2.0.0` per project requirements.

---

## 7. No FastAPI/uvicorn in the MCP server itself

**Decision:** The MCP server runs on stdio transport only. FastAPI/uvicorn is listed in requirements for potential future HTTP/SSE transport, but not used in v0.1.

**Why:** stdio is the simplest and most reliable transport for MCP. No ports, no firewall rules, no process management. The CLI (`main.py`) demonstrates all tools without a server.

---

## 8. Single-file server, modular source

**Decision:** The MCP server is a single `server.py` file that imports from `src/` modules.

**Why:** Clear separation of concerns. `server.py` is the API layer (input parsing, tool registration). `src/` modules are the domain logic (drafting, rights, ombudsman, tracking, escalation). New contributors know exactly where to add code.

---

## 9. 7 issue types, not a taxonomy engine

**Decision:** Define exactly 7 issue types as an enum. No dynamic taxonomy, no sub-types, no AI classification.

**Why:** 7 types cover 90%+ of consumer complaints. An enum is self-documenting, IDE-friendly, and makes validation trivial. Dynamic classification would add complexity with no clear benefit for v0.1.

---

## 10. No external LLM dependency

**Decision:** v0.1 has zero LLM calls. The `.env.example` shows an optional `LLM_API_KEY` for future use.

**Why:** Every external dependency is a point of failure. v0.1 is fully functional without one. An LLM could enhance the drafting (more personalised tone, better issue summaries) or the ombudsman finder (interpret free-text company names), but neither is required for a working v1.
