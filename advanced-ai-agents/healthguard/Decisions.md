# Decisions — HealthGuard

## 1. CLI-first (not web UI)
- **Chosen:** Rich CLI with typer + `rich` + `rich.table` + `rich.panel`
- **Rejected:** Flask web app, Streamlit dashboard
- **Why:** This project lives in an AI-agent repo where every other project is CLI-first. Consistency matters more than eye candy. Typer gives us free `--help` and argument parsing, Rich makes the terminal output readable without a browser.

## 2. Multi-agent architecture (not monolithic)
- **Chosen:** 4 specialized agents, each in its own file under `agents/`, coordinated by `main.py`
- **Rejected:** Single file with all logic, plugin system with dynamic loading
- **Why:** Multi-agent orchestration is literally the category requirement (Advanced AI Agents). Each agent has a clear scope: Drug Checker queries OpenFDA, Symptom Triage is a lookup-only agent, Condition Researcher queries MedlinePlus, Report Compiler aggregates. Files stay under 300 lines each. A plugin system would be overengineered for 4 agents.

## 3. Local curated DB + API fallback (not API-only)
- **Chosen:** Curated drug interaction DB (10 pairs) and condition DB (7 conditions) as primary, with OpenFDA/MedlinePlus as fallback
- **Rejected:** API-only approach, pure offline mode with no live data
- **Why:** The demo must work without internet — no API keys, no network. The curated DB gives deterministic output for common queries. Live API fallback enriches results when network is available. Pure offline would give stale data; API-only fails on first launch or in CI.

## 4. OpenFDA + RxNorm + MedlinePlus (not other health APIs)
- **Chosen:** OpenFDA (drug labels/interactions), RxNorm (drug identity), MedlinePlus (condition info)
- **Rejected:** NIH ClinicalTrials.gov (trial-focused, not consumer), WHO APIs (auth-heavy), commercial APIs (require API keys)
- **Why:** All three are US Government APIs — free, zero-auth, no rate limiting for reasonable use, well-documented. OpenFDA has drug interaction sections in labels. MedlinePlus returns consumer-friendly health topic summaries.

## 5. httpx (not requests or urllib)
- **Chosen:** `httpx` with `set_client()` injection pattern
- **Rejected:** `requests` (blocking-only, no built-in timeout management for multiple calls), `urllib` (too low-level)
- **Why:** httpx supports connection pooling, has a clean async API for future upgrades, and the `set_client()` injection pattern makes tests hermetic (no real network calls in unit tests). Every project in the repo uses the same pattern.

## 6. dataclasses + enums (not pydantic models or plain dicts)
- **Chosen:** Python `@dataclass` with `StrEnum` for `Severity`/`Urgency`
- **Rejected:** Pydantic v2 models (overkill for 6 flat types), plain dicts (no type safety, no IDE autocomplete)
- **Why:** dataclasses give us immutability, clean `__repr__`, and type safety. Enums prevent typos in severity strings. Pydantic's validation would be useful for a user-facing API server, but this is a CLI tool.

## 7. Source field on every model (provenance tracking)
- **Chosen:** Every dataclass has a `source: str = "live"` field
- **Rejected:** Implicit source tracking via log messages, no provenance at all
- **Why:** The report compiler needs to tell the user whether data came from OpenFDA (live), the curated database (known-db), or simulation (simulated). Without this, users can't judge reliability. Every agent must declare where its data came from.

## 8. Command dispatch: subcommands not flags
- **Chosen:** `check`, `symptom`, `condition`, `info`, `interactive` as typer subcommands
- **Rejected:** Single command with positional flags, YAML config files
- **Why:** Subcommands let users run only the agents they need (`python main.py condition hypertension` skips the drug checker). Positional flags would require remembering a flag order. YAML configs add complexity for a tool that takes 2-5 arguments.

## 9. Symptom matching: heuristic keyword detection (not NLP)
- **Chosen:** Keyword-based matching with partial substring lookups and an urgency ladder
- **Rejected:** spaCy NER, sentence-transformers embeddings, regex-only exact match
- **Why:** An LLM call per symptom would be expensive and slow for a CLI tool. spaCy adds 100MB+ dependency. Keyword matching with 10 curated symptoms covers the top 80% of consumer health queries. The urgency ladder (routine → soon → urgent → emergency) maps directly to clinical triage categories.

## 10. Report format: formatted text (not HTML/PDF/JSON)
- **Chosen:** Plain text with Rich formatting, Markdown for condition panels
- **Rejected:** HTML report (needs browser), JSON output (needs a viewer), PDF (heavy deps)
- **Why:** Console-first tool = console-first output. The `format_report()` generates a 70-col-wide report that renders perfectly in any terminal. The `_severity_label()` and `_urgency_label()` functions map enums to human-readable text. JSON export is one `print(report.__dict__)` away for power users.

## 11. Interactive mode: comma-separated input (not a REPL with history)
- **Chosen:** Simple `input()` loop splitting on commas, with heuristic drug vs symptom detection
- **Rejected:** Full REPL with readline/history, OpenAI-like chat interface
- **Why:** A full REPL adds complexity (readline, multi-line input, command history). The comma-separated approach handles the common case ("aspirin, ibuprofen, headache") with zero extra dependencies. The heuristic (detects symptom keywords vs drug names) is good enough for the 90% case.

## 12. Test approach: deterministic offline tests (not integration tests)
- **Chosen:** Offline unit tests using the curated DB paths — no network calls, no API keys
- **Rejected:** Live API integration tests, snapshot tests with recorded responses
- **Why:** Offline tests run in CI, in cron, and on first clone — no setup friction. The curated DB gives deterministic outputs. Live API tests would fail on network flake or API changes. The `set_client()` pattern keeps the option open for integration tests later.

## 13. One test file (not per-agent test files)
- **Chosen:** Single `test_healthguard.py` with test classes grouped by agent
- **Rejected:** Per-agent test files under `tests/agents/`, doctests inline
- **Why:** 4 agents × ~25 tests each = 100 tests in one file. Splitting would add `__init__.py` boilerplate and import chains. Grouping by class (`TestDrugChecker`, `TestSymptomTriage`, etc.) gives the same organization without the file overhead. Doctests would tie test data to code changes.

## 14. Single-command entry point (not pip-installable package)
- **Chosen:** `python main.py` with `if __name__ == "__main__": main()` pattern
- **Rejected:** `pyproject.toml` with `[project.scripts]` entry, setup.py
- **Why:** Every project in this repo uses `python <project>/main.py` as the convention. Adding pyproject.toml would be more correct but inconsistent with the rest of the repo. The `main()` function is importable for programmatic use regardless.

## 15. Rich for formatting (not colorama or pure ANSI)
- **Chosen:** `rich` library with Panel, Table, Markdown, console.status
- **Rejected:** `colorama` (tables and panels require manual ASCII art), `f-strings` (no mixing of formatting modes)
- **Why:** Rich gives tables with auto-column-width, colored severity labels, loading spinners during agent runs, and Markdown rendering for condition descriptions. It's already a dependency in many repo projects.