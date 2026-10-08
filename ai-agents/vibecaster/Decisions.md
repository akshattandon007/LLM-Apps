# Decisions.md — VibeCaster

## 1. CLI-only vs Web UI
**Chosen:** CLI with Rich-rendered terminal UI  
**Rejected:** Flask/FastAPI web app, Streamlit, or TUI (textual)  
**Why:** The rota brief calls for a "fun creative single-purpose AI app" buildable in one session. A web UI adds routing, templates, state management, and deployment complexity. Rich's `Panel`, `Columns`, and `rule` provide a polished terminal experience with zero server overhead.

## 2. Python vs Node.js vs Bash
**Chosen:** Python 3.13  
**Rejected:** Node.js (JS ecosystem), Bash (no structured output), Go (compile time)  
**Why:** Python has the OpenAI client SDK pre-installed, Rich for terminal rendering, and `json` in stdlib. Speed of development — the app is ~250 lines, no type-checking or compilation step needed.

## 3. OpenRouter vs direct provider API
**Chosen:** OpenRouter (free-tier models)  
**Rejected:** OpenAI direct API (paid), Anthropic (paid), Google AI Studio (separate SDK)  
**Why:** OpenRouter provides free-tier models (`google/gemini-2.5-flash`, `openai/gpt-4o-mini:free`) through a single OpenAI-compatible endpoint. No credit card needed, single API key, and the free models are sufficient for creative text generation.

## 4. JSON structured output vs free-form text parsing
**Chosen:** LLM returns strict JSON, parsed with `json.loads`  
**Rejected:** LLM returns free-form markdown parsed by regex or section headings  
**Why:** A JSON schema in the system prompt guarantees parseable output. Free-form text would require fragile heading/regex parsing and break if the LLM changes phrasing. The user prompt includes "respond with valid JSON (no markdown fences)" — reliable extraction.

## 5. Single model vs fallback chain
**Chosen:** Single-model call with hardcoded model list (first model used)  
**Rejected:** Retry loop with fallback models, or dynamic model selection  
**Why:** The app targets free-tier models; if the first is overloaded, switching rarely helps (all free models share the same rate limits). Keeping it simple: one request, fail fast. The model list exists for future manual swaps only.

## 6. Gemini 2.5 Flash vs GPT-4o-mini-free vs Mythomax
**Chosen:** `google/gemini-2.5-flash` as default  
**Rejected:** `openai/gpt-4o-mini:free` (slower on creative tasks), `gryphe/mythomax-l2-13b:free` (lower instruction following)  
**Why:** Gemini 2.5 Flash consistently returns structured JSON without extra coaxing, is fast, and is free on OpenRouter. It handles the 8-field JSON schema reliably.

## 7. Rich vs Colorama vs crayons vs plain print
**Chosen:** Rich library  
**Rejected:** Colorama (no panels/tables), crayons (minimal), plain print (ugly)  
**Why:** Rich provides `Panel`, `Columns`, `rule`, `Markdown` rendering, and custom colour output in a single library. It's already installed (v15.0.0) and creates a "wow" terminal experience with minimal code.

## 8. Colour palette display method
**Chosen:** Unicode block characters (`●`) with ANSI RGB colour  
**Rejected:** Hex-dump text blocks, 24-bit escape sequences, external image viewers  
**Why:** Terminal colour blocks render inline in any modern terminal emulator without dependencies. The `●` character is universally available and visually distinct.

## 9. Poetry generation — original vs curated quotes
**Chosen:** LLM-generated original poetry in the AI response  
**Rejected:** Curated quotes from a local database, or Wikipedia quote scraping  
**Why:** Original poetry is more personal and matches the user's expressed mood. A curated database would be static and limited; web scraping adds fragility. The LLM easily generates 4-8 line poems on any mood.

## 10. Playlist — real songs vs generated track names
**Chosen:** LLM instructed to reference existing real songs  
**Rejected:** AI-invented song names (unverifiable), or hardcoded mood→song map  
**Why:** Real-song references are verifiable and useful — the user can actually listen to them. The LLM's training data includes extensive music knowledge (artists, titles, genres). A hardcoded map would be limited and require manual curation.

## 11. API key resolution strategy
**Chosen:** Environment variable (`OPENROUTER_API_KEY`) → `OPENAI_API_KEY` → `~/.env` file  
**Rejected:** Hardcoded keys, config file, interactive prompt  
**Why:** Environment variables are the standard 12-factor app pattern. Falling back to `~/.env` handles the common case where the key is stored in a dotfile but not exported. The search order ensures explicit overrides work while still finding the key when sourced from `.bashrc`.

## 12. Test approach — mocking the LLM call
**Chosen:** `unittest.mock` patches on the inner OpenAI client  
**Rejected:** Making real API calls, or testing against a local model  
**Why:** Real API calls cost money, are slow, and depend on network availability. Mocking the chat completion endpoint lets tests run in milliseconds and verify both parsing and error handling deterministically.

## 13. Rich Console vs logging for error output
**Chosen:** `Console.print` for all output (including errors)  
**Rejected:** Python `logging` module, or mixed print/logging  
**Why:** A single-purpose CLI app doesn't need log levels, file handlers, or structured logging. Console as the output channel keeps the code uniform — errors, status, and results all flow through the same rendering system. If the app ever needs debug logging, Rich also has `console.log`.

## 14. Project structure — flat vs package
**Chosen:** Single flat module (`vibecaster.py`) with `tests/test_vibecaster.py`  
**Rejected:** Full package with `__init__.py`, `cli.py`, `render.py`, `client.py` submodules  
**Why:** With <300 lines of total application code, splitting into submodules adds import overhead and navigation friction. A single file is easier to read, test, and maintain. The test file is kept separate because it's not shipped to end users.

## 15. Pytest vs unittest
**Chosen:** pytest  
**Rejected:** unittest (verbose, more boilerplate)  
**Why:** pytest fixtures (`capsys`, `tmp_path`, `monkeypatch`) are built-in and reduce test boilerplate by ~40% compared to unittest. The `pytest.raises` context manager is clearer than `self.assertRaises`. Pytest's fixture system also makes the mock injection for API key and OpenAI responses cleaner.