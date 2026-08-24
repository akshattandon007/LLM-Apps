# Flow — HomeCourt

Execution trace from entry point to output. Follows the call chain through every module.

---

## Entry: `python main.py`

```
main.py
└── main()
    ├── load_dotenv()                     # Reads .env (optional, for live mode)
    │
    ├── if --simulate:
    │   └── court.run_simulated_demo()
    │
    ├── if --plead:
    │   └── court.run_interactive_session()
    │
    └── else:
        └── print usage text
```

---

## Flow A: Simulated Demo

```
court.run_simulated_demo()
│
├── Selects a random Case from demo_cases[]
│   └── Case(title, pleas=[CasePlea, CasePlea])
│
├── Selects a random PersonaDef from PERSONAS[]
│
├── Prints case info and persona greeting
│   └── persona.greeting (e.g. "You kids and your nonsense...")
│
└── jurors.render_verdict(case, persona.key.value, mode="simulate")
    │
    ├── personas.get_persona(persona_key)
    │   └── PERSONA_MAP[JudgePersona(persona_key)] → PersonaDef
    │
    └── _simulate_verdict(case, persona)
        │
        ├── persona.style.value → "grumpy" | "dramatic" | "clinical" | ...
        │
        ├── _SIMULATED_REASONING[style] → random.choice([...])
        │   └── Returns a persona-appropriate reasoning paragraph
        │
        ├── _SIMULATED_RULINGS → random.choice([...])
        │   └── Returns a ruling string
        │
        ├── _DISSENTING_OPTIONS → random.choice([...])
        │   └── Returns a dissenting opinion (or None)
        │
        └── Verdict(case_name, presiding_judge, reasoning, ruling, ...)
            └── RETURNED to court.run_simulated_demo()
    │
    └── reporter.format_verdict(verdict)
        │
        ├── verdict.formatted_header
        │   └── Box-drawn "HOMECOURT — OFFICIAL VERDICT" banner
        │
        ├── Header block: case name, judge emoji+name, date
        │
        ├── Reasoning section (word-wrapped)
        │   └── _wrap_text(paragraph, prefix="  ", width=76)
        │
        ├── verdict.formatted_ruling
        │   └── Ruling banner with ruling text
        │
        ├── Dissenting opinion (if present)
        │
        └── Footer: "binding in the court of friendship"
            └── PRINTED to stdout
```

---

## Flow B: Interactive Session

```
court.run_interactive_session()
│
├── _prompt("Case name")               → "Sushi vs Pizza"
├── _prompt("Side A name")             → "Alice"
├── _prompt("Alice's argument", multi) → "Sushi is fresh..."
├── _prompt("Side B name")             → "Bob"
├── _prompt("Bob's argument", multi)   → "Pizza is happiness..."
│
├── Case(title, pleas=[CasePlea, CasePlea])
│
├── Print persona list (PERSONAS[0..5])
│
├── _pick_persona()
│   ├── input() → number or name
│   ├── Lookup by index or name match
│   └── RETURN persona.key.value
│
├── Print persona.greeting
│
├── _prompt("Mode") → "simulate" | "live"
│
└── jurors.render_verdict(case, persona_key, mode)
    └── (Same as Flow A from here)
```

---

## Flow C: Live LLM Mode

```
jurors.render_verdict(case, persona_key, mode="live")
│
├── personas.get_persona(persona_key) → PersonaDef
│
└── _live_verdict(case, persona)
    │
    ├── _build_messages(case, persona)
    │   ├── system: _LIVE_SYSTEM_PROMPT
    │   ├── system: persona.personality_prompt
    │   └── user: "Judge the following case:\n\n{case_text}"
    │
    ├── _call_llm(messages)
    │   ├── os.environ["LLM_API_KEY"]
    │   ├── os.environ["LLM_BASE_URL"] (default: https://api.openai.com/v1)
    │   ├── os.environ["LLM_MODEL"] (default: gpt-4o)
    │   │
    │   ├── httpx.Client → POST {base_url}/chat/completions
    │   ├── response.raise_for_status()
    │   └── RETURN response["choices"][0]["message"]["content"]
    │
    └── Verdict(case_name, presiding_judge, reasoning=raw, ...)
```

---

## Module Dependency Graph

```
main.py
  └── src/court.py
        ├── src/jurors.py
        │     ├── src/personas.py
        │     └── src/models.py
        ├── src/reporter.py
        │     └── src/models.py
        └── src/personas.py
              └── src/models.py
```

No circular dependencies. Every module depends only on `models.py` (the data layer) and one or two siblings.

---

## Key Data Flow

```
User input (stdin)
    │
    ▼
court.py: build Case + pick PersonaDef
    │
    ▼
jurors.py: render_verdict(Case, persona_key, mode)
    │
    ├── persona.personality_prompt (shapes LLM/system output)
    │
    ▼
reporter.py: format_verdict(Verdict)
    │
    ▼
stdout (shareable court order)
```

*Last updated: 2026-08-24*