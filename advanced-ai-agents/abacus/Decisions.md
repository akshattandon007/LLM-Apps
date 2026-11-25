# Decisions — abacus

## Why multi-agent?

**Decision:** Use a supervisor-subordinate multi-agent architecture with typed dataclass communication.

**Rejected:**
- *Monolithic script* — simpler but doesn't demonstrate the advanced AI agent pattern this category requires
- *Single-agent with tool calls* — one LLM orchestrating math would be fragile and expensive
- *Microservice architecture* — overkill for a CLI tool; each agent is a Python class, not a separate service

**Why:** The multi-agent pattern showcases independent reasoning (Income/Expense agents use LLM for categorization; Scenario Engine uses pure math) while keeping the code testable. Each agent can be developed, tested, and improved independently.

---

## CLI vs Web interface

**Decision:** CLI-first with argparse.

**Rejected:**
- *Flask/FastAPI web app* — requires a running server, browser interaction, and adds deployment complexity
- *Streamlit/Gradio GUI* — adds dependencies and isn't practical for a CLI-first repo
- *TUI (Textual)* — cool but adds a heavy dependency for marginal benefit

**Why:** CLI is the standard for the advanced-ai-agents category. Zero deployment friction — clone and run. The `--json` flag enables pipe-ability for scripting.

---

## Python over TypeScript/Rust

**Decision:** Python 3.14 with stdlib-only math.

**Rejected:**
- *TypeScript* — better for web apps, not CLI tools; npm dependency chain
- *Rust* — faster for huge number crunching, but this is simple financial math; build time and complexity not justified

**Why:** Python's dataclasses, argparse, and math module handle everything needed. The LLM calls are HTTP requests — no special async needed.

---

## Pure math engine vs LLM-based calculations

**Decision:** Scenario Engine uses pure Python math (stdlib only).

**Rejected:**
- *LLM does the math* — LLMs are unreliable at arithmetic, especially compound interest over 60 periods
- *numpy/pandas* — overkill for scalar financial projections; adds a heavy dependency
- *Wolfram Alpha API* — paid, rate-limited, external dependency

**Why:** Financial math is deterministic — PMT, FV, amortization tables are closed-form formulas. LLM is used only where parsing/categorization needs NLP (income descriptions, expense categorization).

---

## Tax estimation approach

**Decision:** Simplified flat-rate effective tax rate assumption (default 22%).

**Rejected:**
- *Bracket-by-bracket calculation* — requires knowing filing status, deductions, state tax; too complex for a CLI input
- *Tax API integration* — all paid APIs; free ones are unreliable
- *User-provided marginal rate* — added as an override via IncomeStream.tax_rate

**Why:** A flat effective rate (22% = typical US single filer in the $44k–$95k bracket) gives a reasonable estimate. Users can override per-stream via code.

---

## Goal feasibility as "feasible/needs adjustment" vs percentage score

**Decision:** Binary flag + gap amount, with a "monthly_needed" comparison.

**Rejected:**
- *Probability score (70% likely to hit goal)* — misleading precision; too many unknowable variables (market returns, inflation, life changes)
- *Traffic light (green/yellow/red)* — same information, less actionable

**Why:** The gap amount tells the user exactly how much they need to adjust their savings. Binary flag avoids false precision.

---

## Dataclass communication vs raw dicts

**Decision:** Typed dataclasses in models.py with a JSON encoder for serialization.

**Rejected:**
- *Raw dicts everywhere* — fragile, no IDE autocomplete, no validation
- *Pydantic models* — adds dependency; dataclasses with `field()` are sufficient for this scope
- *Protocol classes* — over-engineering for 5 agents

**Why:** Dataclasses are zero-dependency, give type checking, and make the agent contracts explicit. The FinancialEncoder handles JSON output.

---

## What-if scenario parsing

**Decision:** Regex-based keyword matching in `_parse_what_if()`.

**Rejected:**
- *LLM-parsed what-if queries* — accurate but slow, requires a key, adds latency
- *Formal query language* — too much friction for a CLI tool
- *Hardcoded scenario buttons* — limits flexibility

**Why:** Regex covers the common patterns (raise, cut, save more, pay debt) in <1ms. Users who want custom scenarios can pass adjustments directly via the API.

---

## Interactive mode

**Decision:** Built-in `--interactive` mode with guided prompts.

**Rejected:**
- *YAML/JSON config file* — less discoverable; users have to read docs first
- *RC file (~/.abacusrc)* — global state is hard to debug
- *No interactive mode* — CLI-only would be fine but interactive lowers the barrier

**Why:** Interactive mode is a step-by-step guide that works for first-time users. The same data can be passed via CLI args for automation.

---

## Testing strategy

**Decision:** 19 unit tests covering models, agents, engine, goal tracker.

**Rejected:**
- *Integration tests with real API calls* — flaky, slow, requires API key
- *Snapshot tests* — financial projections change with parameter tweaks
- *Property-based tests* — interesting but overkill for this scope

**Why:** The core logic is deterministic (math, parsing). Unit tests with pytest cover all branches. The LLM fallback path is tested implicitly by running without an API key.

---

## LLM integration pattern

**Decision:** Opt-in; fallback mode works without any API key.

**Rejected:**
- *Hard requirement on API key* — breaks in CI, offline, or for users without keys
- *Mock LLM in tests* — adds maintenance burden

**Why:** The financial math is the product; the LLM enriches but doesn't gate. Fallback mode returns deterministic JSON so the CLI works fully offline.

---

## File organization

**Decision:** Flat package structure: models.py, llm.py, agents/ subpackage.

**Rejected:**
- *One file per class* — too many files for a small project
- *All in __main__.py* — unmaintainable
- *src/ layout* — adds import complexity; `python __main__.py` already works

**Why:** `agents/` groups the multi-agent logic. `models.py` centralizes shared types. `__main__.py` is the thin CLI entry point.

---

## Version requirement

**Decision:** Only `pytest>=7.0` in requirements.txt.

**Rejected:**
- *Pinned dependencies* — too strict for a tool that depends only on stdlib
- *All stdlib, no requirements.txt* — pytest is needed for tests; listing it helps discoverability

**Why:** The tool itself needs zero external packages. Only pytest is listed for test runners. Users who just run the tool don't need `pip install` at all.