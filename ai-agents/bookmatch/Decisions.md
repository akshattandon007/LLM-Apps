# Decisions.md — Bookmatch

Architectural decisions made while building the Bookmatch AI App.

---

## 1. CLI Over Web UI

**Chosen:** CLI (terminal-based interactive interview)
**Rejected:** Web app (Flask/Streamlit), TUI (Textual)
**Why:** The target audience (Akshat / developer-adjacent users) is comfortable in a terminal. CLI keeps the dependency footprint minimal (no web server, no browser rendering) and makes the app trivially scriptable. A web UI would add Flask/Streamlit, HTML templates, and CSS — none of which help the core value proposition of personalized book recommendations.

## 2. Python Over TypeScript/Node.js

**Chosen:** Python 3.14
**Rejected:** Node.js/TypeScript, Go, Rust
**Why:** The app is fundamentally an LLM orchestrator with string processing — Python's ecosystem (httpx, dataclasses, json) handles this with zero friction. The Hermes environment already has Python 3.14 and OpenRouter access configured. Node.js would require node/npm installation and adds unnecessary complexity for a lightweight CLI tool.

## 3. OpenRouter Provider Over Direct Anthropic/OpenAI

**Chosen:** OpenRouter API (`openai/gpt-4o-mini`)
**Rejected:** Direct Anthropic API, direct OpenAI API, Google Gemini API
**Why:** OpenRouter gives us one API key and URL to manage while supporting multiple model backends. It already has a key loaded in the Hermes chief profile. Direct APIs require separate keys per provider and each has different client SDKs. OpenRouter also provides fallback routing if a model is overloaded.

## 4. gpt-4o-mini Model Over Stronger Models

**Chosen:** `openai/gpt-4o-mini` (cheap, fast)
**Rejected:** GPT-4o, Claude Opus 4.6, Gemini Ultra, DeepSeek V4 Flash
**Why:** Book recommendations don't need frontier-reasoning capabilities. gpt-4o-mini is ~20x cheaper, 5x faster, and produces genuinely good book recommendations. The critical path (interview → structured JSON output) is well within a small model's competence. If quality degrades, the MODEL constant can be bumped without code changes.

## 5. JSON Output Parsing Over Raw Text

**Chosen:** Request JSON from the LLM, parse with `json.loads()` with fallback regex extraction
**Rejected:** Free-form text output, markdown tables, structured generation (tools/functions API)
**Why:** JSON output is deterministic to parse and easy to format into pretty-printed recommendations. The LLM is instructed to return only JSON, but fallback regex extraction handles edge cases where it wraps output in code fences. The tools/functions API would be more reliable but requires OpenAI client SDK — httpx.post is simpler and more portable.

## 6. Dataclass Model Over Dict-Passing

**Chosen:** `@dataclass` for ReaderProfile and BookRec
**Rejected:** Plain dicts, Pydantic models, NamedTuple
**Why:** Dataclasses give type hints, field defaults, and readable `__repr__` without a dependency on Pydantic. Dicts lack structure and are error-prone when keys are misspelled. Pydantic adds a dependency that isn't needed — we don't do deep validation. NamedTuples are immutable, which makes profile building awkward.

## 7. Interactive Interview Over Single Prompt

**Chosen:** 8-question interactive interview sequence
**Rejected:** Single-shot "tell me about your reading taste" prompt, multi-turn chat loop
**Why:** An interactive interview gathers richer, more structured data than a single free-text prompt. Each question targets a specific dimension (favorites, dislikes, goals, mood). The user isn't asked to synthesize everything at once, which produces better profiles and ultimately better recommendations. A full chat loop would be overengineered — one interview pass is enough.

## 8. Module Structure: Single-File CLI Over Multi-Module Package

**Chosen:** Single `main.py` with logical sections (Config, Models, LLM, Interview, Display)
**Rejected:** Separate files for interview.py, recommender.py, display.py
**Why:** The entire app is ~350 lines. Splitting across files adds import overhead and mental context-switching without performance benefit. The code is cleanly organized with section headers and each function has a single responsibility. A multi-module architecture would make sense at 2000+ lines.

## 9. Input Validation: Minimal Defense Over Exhaustive Checks

**Chosen:** Basic empty string checks, split-on-comma parsing
**Rejected:** Pydantic validation, argparse, type-annotation enforcement
**Why:** CLI input() always returns a string; the receiver is another human (LLM) that can handle messy input gracefully. Exhaustive validation (email-style "invalid input" loops) would slow down the interview flow. The LLM prompt is robust to commas, partial answers, and empty fields.

## 10. Console Output: Raw Print Over Rich/Library

**Chosen:** `print()` with box-drawing characters
**Rejected:** Rich library, colorama, pyfiglet
**Why:** The two visual elements are: (a) the interview questions and (b) the recommendation cards. Print with Unicode box-drawing (`─`, `=`) is clean, readable, and has zero dependencies. Rich is powerful but adds a dependency for a 5-minute benefit. If we wanted colors, emoji already provides enough visual hierarchy.

## 11. Save Format: Markdown Over TXT/CSV

**Chosen:** Markdown file (`bookmatch-recs.md`)
**Rejected:** Plain text, CSV, JSON
**Why:** Markdown renders beautifully in any viewer (terminal, GitHub, VS Code) and supports headings, bold, lists. It's the most portable "nice" format for saving recommendations. JSON is machine-readable but not human-friendly. Plain text lacks structure. CSV doesn't handle multi-sentence descriptions well.

## 12. Environment Variable Over .env File

**Chosen:** `OPENROUTER_API_KEY` from `os.environ`
**Rejected:** `python-dotenv` loading from `.env`
**Why:** The Hermes runtime already exports API keys as environment variables. Loading from .env would add a dependency and a file that may not exist. The app checks for the key at startup and gives a clear error if missing — this is sufficient.

## 13. httpx Over requests Library

**Chosen:** `httpx` for HTTP calls
**Rejected:** `requests`, `urllib`, `aiohttp`
**Why:** httpx is the modern successor to requests with a near-identical API, better timeout handling, and HTTP/2 support. It's already available in the Hermes Python environment. The requests library works fine but httpx is what's installed. aiohttp would require async/await throughout which is overkill for a synchronous CLI tool.

## 14. No Caching Layer

**Chosen:** Every invocation calls the LLM fresh
**Rejected:** SQLite cache, file-based cache, Redis
**Why:** Book recommendations should be fresh per session — the user's mood and recent reading change. Caching identical profiles would save tokens on repeat invocations but adds code complexity and storage management. The app is cheap to run (~500 tokens per recommendation), so caching isn't justified.

## 15. Name "bookmatch" Over Alternatives

**Chosen:** `bookmatch` (short, clear, available)
**Rejected:** `bookmatchmaker`, `nextread`, `literarymatch`, `pageturner`
**Why:** "Bookmatch" is short, memorable, and clearly communicates "matches you with books." A one-word name fits the ai-agents/ directory convention (echo, roster, stash, myth, etc.). "Bookmatchmaker" is too long. "NextRead" is generic. "Pageturner" doesn't convey the matching concept.