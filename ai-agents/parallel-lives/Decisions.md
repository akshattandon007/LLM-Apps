# Decisions.md — Why Parallel Lives is built this way

Every architectural choice has a reason. Here is the rationale for every
non-trivial decision in this project.

---

## 1. CLI over voice app for MVP

**Decision:** Ship as a terminal CLI tool, not a voice-enabled app.

**Why:** Voice adds three hard problems before we know if the concept works:
TTS latency, STT (speech-to-text) accuracy, and audio device handling across
platforms. A CLI tool proves the core value — character-driven conversation —
in one evening. If people use it, voice can be layered on top (via TTS calls
in the responder). MVP should validate the concept, not the transport.

## 2. In-memory conversation state with no database

**Decision:** `ConversationState` is a Pydantic model held in memory per session.

**Why:** The MVP has no need for persistent cross-session state. Each `--call`
or `--simulate` run creates a fresh conversation. Adding persistence later
means swapping `ConversationState` for a SQLite-backed store — the model
interface stays the same. Not building a DB layer we don't need yet.

## 3. Templated simulated responses (no LLM required for demo)

**Decision:** `_simulate_response` uses hand-written templates per character.
Live LLM mode is a fallback behind `simulate=False`.

**Why:** The tool must work offline and on the first run. No API key, no
dependency on OpenAI/Anthropic. The templates are expressive enough to show
personality; the LLM path exists for depth. This is the "boring, proven"
choice — templates always work.

## 4. Characters as data, not code

**Decision:** Each character is a Pydantic model instance in a dict. Adding a
character means adding one dict entry.

**Why:** A character IS data — name, personality, greeting, knowledge tags.
If characters were classes with methods, every new character would need a new
class. The data-driven approach means the roster can be loaded from JSON or
YAML in v2 without any architecture change. Open/closed principle without
the ceremony.

## 5. Module separation: models, characters, conversation, responder

**Decision:** Four source modules with clear responsibilities.

**Why:**
- `models.py` — types only. No logic. Can be swapped for SQLAlchemy/ORM later.
- `characters.py` — the roster. Pure configuration. Adding a character is a
  single dict entry, not a change to flow logic.
- `conversation.py` — state machine. Owns the message list, builds the prompt.
  Testable without any network.
- `responder.py` — generates text. Only module that touches httpx. Swapping
  OpenAI for Anthropic or local LLM means changing one file.

This makes each file independently testable and readable in isolation.

## 6. Global httpx client injected via set_client()

**Decision:** `responder._client` is module-level; tests inject a mock via
`set_client()`.

**Why:** httpx clients are cheap but carry connection pools. A module-level
singleton avoids creating a new client per-request. The `set_client()` pattern
lets tests inject `MagicMock` without monkey-patching or env var tricks. This
is the same pattern as anyio's `current_default_thread_limits` or httpx's own
`Client.__init__` — explicit injection for testability.

## 7. Context window (last 8 turns) instead of full history

**Decision:** The system prompt includes the last 8 turns of conversation, not
the entire message list.

**Why:** LLM context windows are finite and token-costly. Characters don't need
to remember every word from 50 turns ago — they need the vibe of the recent
exchange. Key facts (user's name, important disclosures) are extracted
separately into `state.key_facts` and appended to the prompt. This gives the
illusion of memory without bankrupting the token limit.

## 8. Named entity tracking via heuristics, not NER

**Decision:** The caller's name is extracted by simple substring matching
("I am X", "my name is X").

**Why:** True named-entity recognition means downloading spaCy or calling an
API. For v1, a half-dozen `str.lower().find()` patterns catch 80% of name
introductions. The v2 path (LLM-extracted key facts) is sketched in the
`extract_memory()` stub but not implemented. Ship the 80% solution.

## 9. `dotenv` for optional LLM config

**Decision:** `python-dotenv` loads `.env` if present; not required.

**Why:** The tool works without it (simulate mode). Adding a `.env` with
`LLM_API_KEY` unlocks live LLM responses. This avoids baking API keys into
the repo or requiring env var export on every run. Standard pattern.

## 10. `pytest` over `unittest`

**Decision:** Tests use pytest fixtures, not unittest.TestCase.

**Why:** The `conftest.py` fixture pattern lets us inject mock characters and
mock httpx clients without class boilerplate. Every test is a plain function.
This is the industry standard and keeps tests readable.

## 11. No `.gitignore` for `.git` itself

**Decision:** The build instruction says not to create `.git` inside the
project. `.gitignore` covers venv, `__pycache__`, `.env`, `.pytest_cache`.

**Why:** Git init is the user's choice once they're ready to push. The project
layout should be git-ready without forcing a repo on the first scaffold.