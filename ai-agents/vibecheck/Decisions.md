# Decisions Log — VibeCheck

## 1. CLI over Web UI
**Chosen:** Command-line interface (argparse + interactive REPL)  
**Rejected:** Flask/Streamlit web UI, Tkinter GUI  
**Why:** The target audience is developers and power users who want fast analysis without browser overhead. A CLI can be piped (`cat file | vibecheck`), scripted, and integrated into CI workflows. A web UI would add dependency weight (Flask, browser, JS) and limit automation use cases.

## 2. Python over Go/Rust
**Chosen:** Python 3.10+  
**Rejected:** Go, Rust, Node.js  
**Why:** Python has the richest LLM ecosystem (OpenAI SDK, LangChain, local model runners via Ollama) and is the team's strongest language. The performance-critical path is the HTTP round-trip to the LLM provider — Python's speed is irrelevant there. Go/Rust would add compile time and reduce maintainability for no gain.

## 3. Provider Abstraction over Single-Provider Lock-in
**Chosen:** Abstract `LLMProvider` base class with pluggable backends  
**Rejected:** Hard-coding OpenRouter API calls throughout the codebase  
**Why:** Users have different LLM setups (OpenRouter free tier, OpenAI paid, local Ollama, self-hosted vLLM). An abstraction layer means a new provider is a single class, not a refactor. The factory pattern (`_build_provider()`) auto-detects from env vars so setup is zero-config for the default case.

## 4. OpenRouter as Default over OpenAI
**Chosen:** OpenRouter (`gryphe/mythomax-l2-13b:free`)  
**Rejected:** OpenAI API (requires paid account), local-only (requires GPU)  
**Why:** OpenRouter offers a generous free tier that works immediately for new users. OpenAI requires credit card setup which is a friction point. Local LLMs require GPU hardware most users don't have. The free model (MythoMax 13B) is good enough for tone analysis — it's a classification/pattern-matching task, not a reasoning-heavy one.

## 5. Requests over OpenAI SDK
**Chosen:** Raw `requests` library  
**Rejected:** `openai` Python package, `httpx`  
**Why:** The app only needs one API endpoint (`/chat/completions`). The OpenAI SDK adds 500KB+ of dependency and locks the app into OpenAI's API shape. Using `requests` directly makes the provider classes self-contained, testable without mocking a complex SDK, and compatible with any OpenAI-compatible backend (Ollama, vLLM, etc.).

## 6. JSON Response Parsing with Fallback over Strict Schema Validation
**Chosen:** `_try_parse_json()` with code-fence stripping + graceful fallback to empty fields  
**Rejected:** Pydantic models with strict validation, regex-only extraction  
**Why:** LLMs occasionally wrap JSON in markdown fences or add commentary before/after the JSON. The parser strips fences and tries standard `json.loads()`. If parsing fails, the app still returns a `ToneAnalysis` with the raw response — no crashes, no user-facing errors. Pydantic would reject slightly malformed output and force a retry, which adds latency and complexity.

## 7. Dataclasses over Dicts for Results
**Chosen:** Python `@dataclass` with type hints (`ToneAnalysis`, `ComparisonResult`)  
**Rejected:** Plain dicts, NamedTuple, custom class with `__init__`  
**Why:** Dataclasses give IDE autocomplete, type checking, default values, and clean `__repr__` for debugging. Dicts are fragile (typo in a key = silent `None`). NamedTuples are immutable which makes result construction awkward. Dataclasses balance readability and flexibility.

## 8. Module Separation: analyzer.py vs cli.py
**Chosen:** `analyzer.py` (core logic, no I/O) separated from `cli.py` (argparse + display)  
**Rejected:** Monolithic single file  
**Why:** Separating the analysis engine from the CLI allows the core to be imported programmatically (`from vibecheck.analyzer import analyze_text`) by other tools or Jupyter notebooks. The CLI becomes a thin wrapper. This also makes testing cleaner — test the analyzer directly without argparse mocks.

## 9. Interactive REPL over Multi-call Pattern
**Chosen:** Built-in interactive mode (`--interactive`) with `/` commands  
**Rejected:** Separate script for interactive use, using Python's `code` module  
**Why:** A single binary with both one-shot and interactive modes is the simplest UX. The REPL uses a while-loop with `input()`, not `cmd.Cmd` (less magic, no extra dependency). Custom `/` commands (`/file`, `/compare`) keep the interface discoverable without needing a man page for every interaction.

## 10. Config File over .env
**Chosen:** `~/.vibecheck/config.json` for persistent setup  
**Rejected:** `.env` file in project root, environment variables only  
**Why:** Environment variables are ephemeral (lost on shell restart) and `.env` ties config to a specific checkout directory. A `~/.vibecheck/config.json` with `chmod 600` is user-wide, survives reinstalls, and keeps the API key out of shell history. The env var `OPENROUTER_API_KEY` still takes priority for CI/CD and containerized use — config file is the fallback.

## 11. Separate Comparison Mode over Implicit Diff
**Chosen:** Explicit `--compare` flag with `|||` separator for A/B comparison  
**Rejected:** Always running comparison against some baseline, auto-detecting two-text input  
**Why:** Comparison is a distinct operation from single-text analysis. The `|||` delimiter is unambiguous and familiar from `diff` workflows. Auto-detecting "is this one text or two?" from stdin would require heuristics that inevitably fail on edge cases (text containing `|||` legitimately, or pipe input where the user expects single analysis).

## 12. Clarity Score as Integer over Float
**Chosen:** Integer 1-10 scale  
**Rejected:** Float 0.0-1.0, letter grade (A-F), 5-star system  
**Why:** Integers are easier for LLMs to produce consistently (no floating-point formatting issues). The 1-10 scale maps directly to the LLM training data (common in review and scoring tasks). A letter grade would lose granularity, and a 5-star scale compresses too much information.

## 13. No Caching Layer
**Chosen:** Every analysis is a fresh LLM call  
**Rejected:** LRU cache of recent analyses, hash-based dedup  
**Why:** Tone analysis is highly contextual — the same text can have different tones depending on recipient, relationship, and channel. Caching would produce stale or wrong results. The free OpenRouter tier has generous rate limits, and typical analysis texts are short (<500 tokens), so each call costs ~$0.0001 or less.

## 14. Public API Exposes Provider as Optional Parameter
**Chosen:** `analyze_text(text, provider=None)` — provider is optional, auto-detected from env  
**Rejected:** Requiring provider on every call, singleton global provider  
**Why:** The 80% use case is "I just want analysis, figure out the backend." Making provider optional with auto-detection serves that. For advanced users, passing a custom provider enables testing with mocks or using a different backend mid-session. A singleton global would make testing painful (shared state between tests).