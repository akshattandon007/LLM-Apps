# Decisions.md — TeamScribe

## 1. Multi-agent pipeline vs single-agent workflow
**Chosen:** 4 specialized agents in a sequential pipeline.
**Rejected:** Single agent doing all processing, or a fully autonomous agent swarm.
**Why:** Specialized agents produce higher-quality output per task (Transcriber only cleans text, MinuteTaker only extracts structured data, etc.). A single-agent approach would mix concerns and produce less reliable structured output. Full swarm adds latency and coordination complexity without proportional benefit for this use case.

## 2. Sequential agent execution vs parallel
**Chosen:** Sequential — each agent runs after the previous finishes.
**Rejected:** All agents running in parallel on the raw input.
**Why:** The Scribe needs the MinuteTaker's structured output (decisions/action items). The Archivist needs the Scribe's summary. Parallel execution would require re-processing or merging strategies. Sequential is simpler and each agent builds on richer context.

## 3. Shared MeetingRecord vs separate contexts
**Chosen:** A single mutable MeetingRecord dataclass passed through the pipeline.
**Rejected:** Each agent with its own output format, or a shared database.
**Why:** A single object with clear fields is simplest to debug, test, and serialize. Each agent reads and writes to specific fields of the same record. No complex message-passing or event bus needed.

## 4. JSON file storage vs SQLite vs cloud
**Chosen:** Local JSON files.
**Rejected:** SQLite (operational overhead, dependency), cloud storage (requires auth, sync complexity).
**Why:** Meeting records are low-volume, document-oriented data. JSON is human-readable, easy to debug, and requires zero setup. SQLite would be overkill. Cloud adds auth friction.

## 5. CLI interface vs web app vs library
**Chosen:** CLI-first with `argparse`.
**Rejected:** Web app (Flask/Streamlit — adds dependency + UI complexity for minimal benefit), library-only (harder to use ad-hoc).
**Why:** CLI is the fastest path to value for a tool you run after meetings. The `python -m teamscribe` pattern makes it feel like a first-class command. A web UI could be a future addition.

## 6. OpenAI client vs custom LLM connector
**Chosen:** Official `openai` Python library.
**Rejected:** Direct HTTP, LangChain, custom abstraction.
**Why:** The OpenAI library handles retries, streaming, auth, and endpoint configuration. Setting `OPENAI_BASE_URL` makes it compatible with OpenRouter, Together, and any OpenAI-compatible provider. LangChain would add an unnecessary abstraction layer.

## 7. JSON structured output from MinuteTaker vs regex parsing
**Chosen:** LLM returns JSON, parsed with regex fallback.
**Rejected:** Regex extraction from free-text output, or function calling.
**Why:** JSON output gives clean, parseable structured data. Regex from free text is fragile. Function calling (tools) requires specific model support and adds complexity. JSON-in-text works across all models and providers.

## 8. File-based archive vs in-memory only
**Chosen:** Persistent JSON archive on disk.
**Rejected:** No persistence (each run is fresh), or a database.
**Why:** The Archivist's value grows over time — tracking decisions across meetings requires persistence. JSON is lightweight and inspectable. No migration needed.

## 9. Temperature 0.1-0.3 for extraction vs higher for creative
**Chosen:** Low temperature (0.1-0.3) for extraction/minutes, default for creative tasks.
**Rejected:** Uniform temperature across all agents.
**Why:** Extraction (decisions, action items) needs consistency and precision — low temperature. Summary and email writing benefit from slight creativity — default temperature is fine.

## 10. Environment variables for config vs config file
**Chosen:** Environment variables with sensible defaults.
**Rejected:** YAML/TOML config file, command-line flags for everything.
**Why:** API keys are already env vars. Extending to model name and paths keeps the same pattern. A config file adds another file to manage. Critical values (API key) shouldn't be in a config file anyway.

## 11. pytest for testing vs unittest
**Chosen:** pytest.
**Rejected:** unittest (stdlib).
**Why:** pytest has better fixture support (`tmp_path` for temp dirs), shorter assertions, and is the community standard for new Python projects.

## 12. Mock-based testing vs integration tests
**Chosen:** All tests mock the LLM calls.
**Rejected:** Integration tests hitting a real LLM API.
**Why:** Tests must pass without an API key. Mocking isolates agent logic: Does the Transcriber use the LLM return correctly? Does the MinuteTaker parse JSON properly? Integration tests are valuable but should be optional.

## 13. Single package vs flat scripts
**Chosen:** `teamscribe/` Python package with `agents/` sub-package.
**Rejected:** Flat directory with `transcriber.py`, `minute_taker.py` at root.
**Why:** A package structure scales better. The `agents/` sub-package keeps related code together. `__main__.py` enables `python -m teamscribe`. Clearer import paths.

## 14. Each agent as a subclass of BaseAgent vs standalone functions
**Chosen:** Class-based agents inheriting from `BaseAgent`.
**Rejected:** Standalone functions, or a single `Agent` class configured by role string.
**Why:** Classes with a common interface (`process(record)`) make the pipeline uniform. Each agent can override behavior cleanly. A single configured class would need conditionals for each role.

## 15. Optional participant/date fields vs required
**Chosen:** CLI arguments with sensible defaults (date defaults to today, participants empty).
**Rejected:** All fields required, or all optional.
**Why:** Meeting date defaults to today (obvious default). Participants being optional means the tool works even if you just type notes. But meeting title is always required — every meeting has a name.