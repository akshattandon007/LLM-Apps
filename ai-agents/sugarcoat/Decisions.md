# Decisions.md — sugarcoat

## 1. CLI over Web App
- **Chosen:** Pure Python CLI (argparse)
- **Rejected:** Streamlit web app, Gradio interface, FastHTML server
- **Why:** sugarcoat solves a quick, single-session problem — type a message, get a rewrite, done. A web app adds startup time, port management, and browser overhead that contradicts the "fast answer" use case. CLI also means zero infra: install and run.

## 2. OpenRouter as the LLM Provider
- **Chosen:** OpenRouter API (OpenAI-compatible)
- **Rejected:** OpenAI direct, Anthropic Claude, local model via Ollama
- **Why:** OpenRouter gives access to many models through one API key (including free-tier options), matches the existing infra on this VPS, and requires no additional accounts. Local models (Ollama) would add ~4GB download and degrade quality on 7B models.

## 3. DeepSeek Chat as Default Model
- **Chosen:** `deepseek/deepseek-chat`
- **Rejected:** GPT-4o-mini, Claude Haiku, Gemini Flash
- **Why:** DeepSeek Chat is available on OpenRouter, cost-effective (~$0.14/M tokens), and excels at instruction-following in structured JSON output — critical for parsing the rephrased result reliably. The model can be overridden per run via `--model`.

## 4. JSON Response Format from the LLM
- **Chosen:** Structured JSON (`rephrased`, `explanation`, `alternatives`)
- **Rejected:** Plain text response, markdown, conversation-only
- **Why:** JSON allows programmatic extraction of multiple outputs (rewritten text, explanation, alternatives) in one API call. The fallback parser handles cases where the model returns plain text — no silent failures.

## 5. Single-File Engine, Separated CLI
- **Chosen:** `sugarcoat.py` (CLI) + `sugarcoat_engine.py` (logic)
- **Rejected:** Monolithic single file, or fully modularized (5+ files)
- **Why:** Two files is the sweet spot — the CLI handles user interaction, the engine handles API calls. Testable independently (the engine can be tested with mocked HTTP). 5+ files would be over-engineering for a ~300-line project.

## 6. httpx Over requests Library
- **Chosen:** `httpx`
- **Rejected:** `requests`, `urllib`, `aiohttp`
- **Why:** httpx has a synchronous API (no asyncio overhead), supports HTTP/2, timeouts natively, and is one of two deps (alongside pytest). `requests` works but httpx is more modern and the project benefits from staying current.

## 7. 6 Tones + 6 Styles (Combinatorial, Not Presets)
- **Chosen:** Separate tone (emotional register) and style (structural verbosity) selectors
- **Rejected:** 36 hardcoded preset combinations, single tone/style axis
- **Why:** Separating tone and style gives 36 combinations from 12 definitions. Users tune two independent levers instead of memorizing preset names. The prompt template composes them dynamically.

## 8. .env / Env Var API Key Loading
- **Chosen:** Auto-detect from `OPENROUTER_API_KEY` env var, `OPENAI_API_KEY` fallback, then `.env` files
- **Rejected:** Hardcoded key, config file only, interactive prompt
- **Why:** Standard 12-factor app pattern. No config file to manage, works everywhere (local dev, CI, VPS). The `.env` file check makes it work in the Hermes ecosystem where keys are stored in profile `.env` files.

## 9. Conversation History as JSON File
- **Chosen:** `--history <file.json>` — external JSON file loaded at runtime
- **Rejected:** SQLite database, in-memory history, stdin pipe
- **Why:** JSON file is the simplest portable format for passing prior messages. Users can prepare it from any source. SQLite is overkill for a one-shot CLI tool; in-memory history wouldn't survive across invocations.

## 10. Markdown Fence Handling in Response Parser
- **Chosen:** Strip ` ```json ... ``` ` fences from model output before JSON parsing
- **Rejected:** Force model to never use fences (unreliable), fail on non-JSON
- **Why:** Many LLMs wrap JSON output in markdown code fences by default. Stripping them before parsing makes the tool robust to model quirks without requiring special prompt engineering. The fallback (wrap plain text as `rephrased`) handles truly non-JSON responses.

## 11. No Caching Layer
- **Chosen:** Every call goes to the API
- **Rejected:** Local cache of common rephrases, SQLite/Redis
- **Why:** Each message is unique — caching provides zero benefit. The overhead of a cache hit detection and invalidation for a ~1-second API call adds complexity with no payoff.

## 12. pytest with Mocked HTTP
- **Chosen:** `pytest` + `unittest.mock.patch('httpx.post')`
- **Rejected:** Integration tests with real API, vcrpy cassette recording
- **Why:** Unit tests with mocks run instantly, work offline, and don't consume API credits. The HTTP call is a thin wrapper — the project's real complexity is in prompt construction and response parsing, both tested without hitting the network.

## 13. No setup.py / pyproject.toml
- **Chosen:** Plain `requirements.txt`, run with `python3 sugarcoat.py`
- **Rejected:** `pyproject.toml` with entry point, `pip install -e .`
- **Why:** The tool is a single-file CLI + one engine module. A packaging setup adds ceremony for no benefit — users clone and run. If the project grows, a setup can be added later without breaking anything.

## 14. System Prompt as Template String
- **Chosen:** `.format()` on a multi-line string template
- **Rejected:** Jinja2 templates, f-strings at call time
- **Why:** `.format()` is stdlib, zero deps, and the template has only two variable slots (tone and style descriptions). Jinja2 is heavy for this; f-strings would require storing tone/style instructions in the same scope, making the template harder to review independently.