# Decisions — HomeCourt

Every meaningful architectural choice, explained.

---

## 1. CLI over Web

| Option | Chosen? | Why |
|--------|---------|-----|
| CLI tool | ✅ Yes | Zero infra, instant feedback, perfect for a VPS-based dev workflow. The project's value is the verdict output, not a UI. |
| Web app | ❌ No | Requires a server, port config, frontend code, and ongoing maintenance. Out of scope for a thin-slice v1. |

## 2. Python over Node.js / Go

Python is the user's established stack (AlphaBrief, Photo Time Machine, PR Auto-Pilot all use Python). No learning curve, consistent tooling (venv, pip, pytest), and the libraries we need (httpx, pydantic) are Python-native.

## 3. Pydantic for models

Pydantic v2 is already in the user's stack (visible in AlphaBrief). It provides:
- Runtime type validation (Catches bad data before it propagates)
- Clear serialization (Verdict can be JSON-serialized later if we add an output flag)
- Enum support (JudgePersona enum prevents invalid persona values)

## 4. Separate module per concern (5 modules in src/)

| Module | Responsibility | Why separate? |
|--------|---------------|---------------|
| `models.py` | Data types (Case, Verdict, PersonaDef, etc.) | Single source of truth for shapes. Every other module imports from here. No circular imports. |
| `personas.py` | Judge personality definitions | Personas are data, not logic. Easy to add/remove/edit without touching any other file. |
| `jurors.py` | Verdict generation (simulate + live LLM) | The core reasoning engine. Separated so it can be tested independently and swapped (simulate/live). |
| `reporter.py` | Verdict formatting | Formatting is a distinct concern. Keeps `jurors.py` from being polluted with display logic. |
| `court.py` | Session flow (interactive or demo) | Orchestrates the user journey. High-level, calls the other modules. |

This follows the **single-responsibility principle**: each file has exactly one reason to change.

## 5. Simulated verdicts as the default

Why ship with procedural "fake" verdicts instead of requiring an API key?
- Zero setup friction (pip install + run = done)
- Demoable immediately (no env vars, no API costs)
- Tests are hermetic (no network, no flakiness)
- The LLM integration path is clean (swap `_simulate_verdict()` for `_live_verdict()`)

The simulated verdicts are not random strings — they are persona-aware templates keyed by `VerdictStyle`, so each judge sounds like themselves even in demo mode.

## 6. Persona as prompt template + metadata

Each persona is a `PersonaDef` Pydantic model containing:
- `personality_prompt` — injected as a system message to the LLM
- `greeting` / `sign_off` — used in the session flow
- `style` — maps to a set of simulated verdict templates

This means:
- Personas can be authored without writing code (add a `PersonaDef` and it works)
- The LLM path and the simulated path both consume the same metadata
- No switch statements, no `if persona == "grouchy"` branching

## 7. `format_verdict()` returns a plain string

The verdict format function returns a plain string rather than writing to a file or returning rich text. This keeps it:
- Testable (assert on string content)
- Composable (pipe to file, display to terminal, send via Telegram)
- Screenshot-ready (fixed-width formatting with box-drawing chars)

## 8. Hardcoded demo cases over config file

Demo cases are defined inline in `court.py` rather than in a JSON/YAML file. For v1 with three cases, adding a file format adds complexity with zero benefit. If we reach 20+ cases, we move them to a data file.

## 9. `render_verdict()` as the public API

The `render_verdict()` function in `jurors.py` is the single entry point for verdict generation:

```python
def render_verdict(case, persona_key, mode="simulate") -> Verdict
```

This is the only function that `court.py` and `test_smoke.py` need to import. Everything else is an implementation detail. This makes future refactoring (e.g., switching LLM providers) a single-file change.

## 10. `.env.example` with multiple providers

The `.env.example` includes placeholders for OpenAI and Anthropic — not because we support both in v1, but because the config structure is forward-compatible. The `_call_llm()` function reads `LLM_BASE_URL`, so switching providers just means changing the env var and model name.

---

*Last updated: 2026-08-24*