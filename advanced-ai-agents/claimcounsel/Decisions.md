# Decisions.md — ClaimCounsel

## 1. Multi-Agent Architecture Over Monolith
**Decision:** Split the system into 4 specialized agents (PolicyParser, DocumentCollector, TimelineTracker, LetterDrafter) orchestrated by a central coordinator.
**Rejected:** Single monolithic class handling everything — would be harder to test, maintain, and extend. Each agent has a single responsibility and can be tested independently.

## 2. OpenAI-Client Wrapper Over Direct API Calls
**Decision:** Created a lightweight LLMClient wrapper around the OpenAI Python client, with singleton pattern.
**Rejected:** Using raw `requests` to call the API — the OpenAI SDK handles retries, streaming, typing, and auth more reliably. Also rejected a heavier framework like LangChain — overkill for this scope.

## 3. JSON Mode for Structured Extraction
**Decision:** Use `response_format={"type": "json_object"}` for the PolicyParser and DocumentCollector agents' analysis output.
**Rejected:** Free-form text parsing with regex — brittle and misses context. JSON mode guarantees parseable output from the LLM.

## 4. File-Based Data Flow Between Agents
**Decision:** Each agent reads from disk and writes to disk (or returns dicts to the orchestrator which persists them).
**Rejected:** In-memory object passing only — would lose state if the process crashes mid-pipeline. File persistence gives recoverability.

## 5. Config-Driven State Deadlines Over LLM Lookup
**Decision:** Hard-coded a `CLAIM_DEADLINES` dict with statute-of-limitations data for all 50 states.
**Rejected:** Asking the LLM to lookup/remember state laws — models hallucinate legal specifics. Hard-coded validated data is more reliable and faster.

## 6. Document Type Requirements as Config
**Decision:** Stored required documents per claim type in `config.py` as a dict.
**Rejected:** LLM-generated checklist per type — inconsistent and may change between runs. Hard-coded values are deterministic and auditable.

## 7. PyPDF2 Over pdfplumber/pdfminer
**Decision:** Use PyPDF2 for PDF text extraction (lightweight, no system deps).
**Rejected:** pdfplumber is heavier and may need system-level dependencies. PyPDF2 is pure Python and handles most standard insurance policy PDFs.

## 8. CLI Argument Parser Over Interactive Mode
**Decision:** Used `argparse` for CLI invocation (batch-friendly, cron-friendly).
**Rejected:** Interactive questionnaire mode — harder to automate, and cron jobs can't interact. CLI flags let the system be used in scripts.

## 9. Plain Text + JSON Dual Output
**Decision:** Save both a human-readable `.txt` report and a structured `.json` report.
**Rejected:** Only JSON — less accessible to non-technical users. Only text — harder to parse programmatically. Both formats serve different audiences.

## 10. Output Per-Run Directory Pattern
**Decision:** Each pipeline run saves to a timestamped/named subdirectory under `OUTPUT_DIR`.
**Rejected:** Single output file overwritten each run — you lose history and can't track multiple claims.

## 11. Graceful Degradation Without LLM
**Decision:** All agents work (with reduced capability) even when no LLM API key is configured.
**Rejected:** Requiring an API key as a hard dependency — makes the tool unusable for "offline first" use. Timeline tracker calculates deadlines mathematically. Document collector does keyword matching.

## 12. Configurable Paths via Env Vars
**Decision:** All data directories configurable through environment variables (CLAIMCOUNSEL_CLAIMS_DIR etc.) with sensible defaults.
**Rejected:** Hard-coded paths — breaks on different machines. Config file in home dir — more complex to set up. Env vars are simple and container-friendly.

## 13. US State Focus Over Global
**Decision:** Focused on US insurance law deadlines and document requirements.
**Rejected:** Global coverage — insurance regulations vary wildly by country. US focus keeps the scope buildable in a day. The architecture is easy to extend for other countries by adding a locale module.

## 14. Test Directory Overrides via Monkeypatching
**Decision:** Integration tests override config module's `DIR` variables directly.
**Rejected:** Dependency injection framework — overengineered for this scope. Direct attribute override is simple and readable for tests.

## 15. Skip LLM Calls When No Key Configured
**Decision:** Agents check `llm.api_key` before making API calls and return structured fallback values.
**Rejected:** Always attempt the call and fail noisily — frustrating for users without API keys. Silent fallback with clear status messages is better UX.