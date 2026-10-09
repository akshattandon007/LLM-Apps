# Decisions.md — LearnerLane

## Architecture decisions for the multi-agent learning curriculum builder.

---

### 1. CLI over Web UI
**Chosen:** CLI (argparse + rich-formatted output)  
**Rejected:** Web UI (Flask/FastAPI), GUI desktop app  
**Why:** CLI is instant to demo, zero setup, no server/port management. A web UI would require running a server and opening a browser — too much friction for a terminal-first repo. Rich-formatted output in the terminal provides a visual experience comparable to a basic web interface.

---

### 2. Module-level Python package over monolith
**Chosen:** Separate package (`learnerlane/`) with an `agents/` subdirectory for each agent  
**Rejected:** Single monolithic Python file, one-file-per-agent in the root  
**Why:** The multi-agent architecture IS the product — separating agents into their own modules makes the design explicit, testable, and extensible. New agents can be added by dropping a file into `agents/` and registering it in the orchestrator.

---

### 3. Simulated (template-based) mode over LLM-only
**Chosen:** Built-in curriculum templates for 5+ topics with a generic fallback, plus live API integration for Wikipedia/Open Library  
**Rejected:** LLM-only generation (requires API key always), hardcoded output-only  
**Why:** The project must be demoable without ANY API keys. Templates provide realistic, complete curricula for the most common skills. The generic fallback handles any topic. Live Wikipedia/Open Library calls enhance results when the user has internet. This hybrid approach means `python -m learnerlane --demo` works immediately.

---

### 4. HTTPX over requests
**Chosen:** `httpx` for HTTP calls  
**Rejected:** `requests`, `aiohttp`, `urllib`  
**Why:** httpx has a clean synchronous API matching `requests` (familiar), plus built-in MockTransport for hermetic tests. No async complexity needed here since API calls are sequential and fast. `requests` lacks MockTransport for clean test injection.

---

### 5. Injectable HTTP client for testability
**Chosen:** Module-level `_client` variable with `set_client()` and `_get_client()`  
**Rejected:** Direct `httpx.get()` calls, dependency injection framework  
**Why:** Module-level client injection is the simplest pattern that allows tests to inject MockTransport without mocking at the network layer. A DI framework would be overkill for 3 API-calling functions. Direct HTTP calls in tests would hit real network or require monkey-patching.

---

### 6. Dataclass-driven data flow over dicts
**Chosen:** Typed dataclasses (`SkillProfile`, `Curriculum`, `Module`, `Resource`, `CompletePlan`)  
**Rejected:** Plain dicts, NamedTuples, Pydantic models  
**Why:** Dataclasses provide type hints, default values, and `@property` methods without external dependencies. NamedTuples are immutable (wrong semantics — we build objects incrementally). Pydantic adds a dependency for validation we don't need. Dicts lack structure and IDE autocomplete.

---

### 7. Sequential pipeline over parallel agent execution
**Chosen:** Agents run in strict sequence (Assess → Build → Hunt → Plan)  
**Rejected:** Parallel agent execution, event-driven agent mesh  
**Why:** Each agent depends on the previous agent's output. The Curriculum Builder needs the SkillProfile. The Resource Hunter needs Modules. The Practice Planner needs both Curriculum and Profile. Parallel execution would require dependency tracking with zero benefit — the pipeline is inherently linear.

---

### 8. Template matching by keyword over user-selected template
**Chosen:** Automatic keyword matching against template keys with partial-match fallback  
**Rejected:** Ask user to pick from a list of templates, always use generic template  
**Why:** Automatic matching means zero friction — type "photography" and get a photography-specific curriculum. The user never needs to select anything. The partial-match ratio (50%+ keyword overlap) prevents false matches while catching variants like "digital photography" or "learning photography".

---

### 9. Free/zero-auth APIs only
**Chosen:** Wikipedia API (no auth), Open Library API (no auth), YouTube search URLs, Google search URLs  
**Rejected:** Coursera API (requires partners), Udemy API (paid), YouTube Data API (requires key)  
**Why:** Zero-auth APIs guarantee the project works for anyone who clones it. Wikipedia and Open Library provide authoritative free content. YouTube and Google search URLs don't need keys — they open in the browser. The project should never say "error: API key not configured."

---

### 10. Fixed 5-module curriculum for templates with duration adjustment
**Chosen:** 5-module templates that adjust to 4-8 modules based on time/level  
**Rejected:** Dynamically generated N modules from scratch, always 8 modules  
**Why:** 5 modules fits a coherent learning arc (basics → core skills → intermediate → application → next steps) for the most common skills. Adjustment for level/time means beginners aren't overwhelmed and advanced learners aren't bored. Dynamic generation from scratch would need an LLM.

---

### 11. Practice tasks mapped to each module by index
**Chosen:** One practice task per curriculum module, matched by index (wrap-around if more modules than practice templates)  
**Rejected:** Random practice task assignment, user-selected tasks, single "master project"  
**Why:** One task per module gives a clear week-by-week cadence. Index matching ensures the right task difficulty order (simple exercise → project). Wrap-around prevents errors when templates have more modules than practice tasks.

---

### 12. `--demo` flag for instant showcase
**Chosen:** A `--demo` flag that runs 3 example curricula (photography, guitar, python)  
**Rejected:** No demo mode, interactive-only, output-to-file only  
**Why:** The first thing anyone does with a new tool is run it with `--help` or `--demo`. The demo shows ALL features (curriculum, resources, practice) across multiple topics, proving the agent architecture works. Interactive-only means reviewers must read code to understand it.

---

### 13. Main README.md table-style project entry
**Chosen:** Single-line entry in the main README's Advanced AI Agents table  
**Rejected:** Separate paragraph with screenshots, no listing at all  
**Why:** A table entry keeps the growing main README scannable. Each project gets: emoji icon, name, link to its directory, and a one-line summary. Separate paragraphs would make the 30+ project list unreadable.

---

### 14. Unification of `skill_assessor.py` assessment and parsing
**Chosen:** Both `assess_skill()` (structured intake) and `parse_goal_freeform()` (free-text parsing) in one module  
**Rejected:** Separate modules, one function that does both  
**Why:** Both functions produce the same `SkillProfile` output — they're different intake FORM strategies, not different domains. Keeping them together makes the Skill Assessor agent a coherent unit. Users can type "photography" (structured) or "I'm a total beginner wanting to learn python" (freeform) and get reasonable results.

---

### 15. Requirements.txt over pyproject.toml
**Chosen:** Plain `requirements.txt` with minimal deps (`httpx`, `rich`)  
**Rejected:** `pyproject.toml` with setuptools/poetry, no dependency file  
**Why:** `requirements.txt` is the lowest-friction install for a CLI tool. `pyproject.toml` adds complexity (build system choice, version pinning, editable install) for a project with only 2 dependencies. The exclusion of `rich` from the core install (only used in the CLI) keeps it optional.