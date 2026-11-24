# Decisions.md

## Architectural decisions for StoryWeaver

### 1. CLI instead of web UI
**Chosen:** CLI with argparse
**Rejected:** Flask/FastAPI web app, TUI with curses/textual  
**Why:** This is a single-purpose AI app for personal use. A CLI keeps dependencies minimal (no web server, no HTML/CSS/JS), is instantly usable from any terminal, and follows the pattern of existing ai-agents/ projects. A web UI adds auth, session management, and deployment complexity that doesn't serve the core use case.

### 2. OpenAI-compatible API instead of a specific provider
**Chosen:** Generic OpenAI-compatible chat completions endpoint
**Rejected:** Anthropic SDK, Google Generative AI SDK, hard-coding to one provider  
**Why:** Many providers (OpenRouter, OpenAI, Groq, Together, local vLLM/Ollama) speak the same chat completions format. Using the generic format with configurable base URL + model lets users bring any provider without code changes. The app ships with sensible defaults (OpenRouter + GPT-4o-mini).

### 3. `response_format: json_object` for structured output
**Chosen:** API-level JSON mode (`response_format: {"type": "json_object"}`)
**Rejected:** Regex parsing of free-text output, instructing in-system without schema enforcement  
**Why:** JSON mode guarantees parseable structured output from the LLM (narrative + choices array). Free-text parsing would require fragile regexes that break when the model changes phrasing. JSON mode is supported by all major providers (OpenAI, OpenRouter, Anthropic via custom tool use).

### 4. Flat JSON file storage instead of SQLite
**Chosen:** JSON files in `~/.storyweaver/saves/`
**Rejected:** SQLite database, in-memory only (no persistence)  
**Why:** Session state is small (<50KB per story) and infrequently accessed (one session at a time). JSON files are human-readable, trivially version-controllable, and require zero schema migrations. SQLite adds a non-trivial dependency and connection management for negligible benefit at this scale.

### 5. Modular `StorySession` dataclass with `to_dict`/`from_dict` instead of ORM
**Chosen:** Plain Python dataclasses with manual serialization
**Rejected:** SQLAlchemy ORM, Pydantic models  
**Why:** The object graph is shallow (session → nodes → choices). Dataclasses with `asdict()` give clean JSON serialization with zero dependencies. Pydantic would add validation that's unnecessary for internally-generated data. An ORM for one-table storage is massive overkill.

### 6. Generous temperature (0.9) for creative writing
**Chosen:** Default temperature 0.9
**Rejected:** Low temperature (0.2-0.5), high temperature (1.5-2.0)  
**Why:** Interactive fiction needs creativity and surprise. A temperature of 0.9 produces varied, imaginative output while staying coherent. Lower temps (0.2-0.5) produce safe, repetitive prose. Higher temps (1.5+) risk incoherence. Users can override via `--temperature`.

### 7. 3 choices per node instead of variable count
**Chosen:** Exactly 3 choices per chapter
**Rejected:** 2 choices, 4 choices, variable (LLM-decided)  
**Why:** 3 choices is the sweet spot in interactive fiction: enough variety to feel meaningful, few enough that each choice can lead to substantially different paths. 2 is too limiting, 4+ dilutes quality. Variable counts complicate the UI and storage model.

### 8. Chapter limit implicit (~5-8) via prompt design instead of hard cap
**Chosen:** Prompt instructs the LLM to aim for "5-8 chapters to a satisfying conclusion"
**Rejected:** Hard limit of N chapters, infinite generation with no guidance  
**Why:** A hard cap truncates stories mid-arc. Infinite generation means stories never end. Prompt-level guidance lets the LLM self-regulate — some genres (mystery) need more chapters, others (horror) fewer. The user can always stop with 's' at any point.

### 9. Epilogue generation as a separate API call instead of inline
**Chosen:** Dedicated `generate_epilogue()` method with a summary prompt
**Rejected:** Never generate an epilogue, force it into the final chapter's response  
**Why:** The standard LLM response format (narrative + 3 choices) doesn't naturally provide an end-of-story signal. A separate epilogue call runs at temperature 0.8 with a short prompt that summarizes the journey — producing a cohesive closing paragraph without forcing more choices. The user triggers it when they reach a node with zero choices.

### 10. Async not used (sync requests)
**Chosen:** `requests` library (synchronous)
**Rejected:** `httpx` async, `aiohttp`  
**Why:** The app generates one chapter per user interaction. There's no parallelism to exploit (users read one chapter, make one choice, wait for the next). Async adds complexity (event loops, async context managers) for zero throughput gain in this sequential use case.

### 11. API key via environment variable (`LLM_API_KEY`) instead of config file
**Chosen:** `LLM_API_KEY` env var with `--api-key` CLI override
**Rejected:** `.env` file, config file in `~/.storyweaver/`, interactive prompt  
**Why:** Env vars are the standard pattern for API keys — they work in CI, containers, and shell sessions without file I/O. A config file would need file permissions management and adds a setup step. Interactive prompt blocks non-interactive usage (scripting, cron).

### 12. Separate `prompts.py` module instead of inline strings
**Chosen:** All prompt templates in a dedicated `prompts.py`
**Rejected:** Inline f-strings in `engine.py`  
**Why:** Prompts are the most-tuned part of any LLM application. Keeping them in one file makes it trivial to iterate, version, and review without touching the execution logic. It also enables future A/B testing of different prompt variants.

### 13. saves_dir at `~/.storyweaver/saves/` instead of project-local
**Chosen:** User home directory (`~/.storyweaver/saves/`)
**Rejected:** Current working directory, `/tmp/`, project root  
**Why:** Stories should persist across working directories and project clones. The home directory is the standard place for per-user application data (XDG Base Directory spec). `/tmp/` is ephemeral. Project root breaks if the project moves or is installed as a package.

### 14. Mock-based testing instead of integration tests hitting a real API
**Chosen:** `unittest.mock.patch` on `requests.post` for all LLM API tests
**Rejected:** Real API calls in test suite, VCR.py for recording cassettes  
**Why:** Tests must be deterministic and fast. Real API calls are slow, cost money, and fail when rate-limited or offline. Mocking the network layer lets the test suite run in <1s and verify the exact prompt/response handling without external dependencies.
