# Flow.md — NameSage Execution Trace

## Overview

NameSage is a single-shot CLI tool: one name in → one profile out. The entire pipeline runs synchronously from the user's perspective, but behind the scenes the four data APIs are called concurrently via `asyncio`.

---

## Function-level call chain

```
CLI invocation:  $ namesage alexandra
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  namesage/cli.py  main()                            │
│  ─────────────────────────────────────────────────── │
│  1. Parse argparse: name = "alexandra"              │
│  2. Print "🔍  Analysing: Alexandra..."             │
│  3. Call asyncio.run(fetch_all("alexandra"))        │
│  4. Call asyncio.run(generate_profile(...))         │
│  5. Call print_profile("alexandra", data)           │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  namesage/api.py  fetch_all(name)                   │
│  ─────────────────────────────────────────────────── │
│  Opens one httpx.AsyncClient for all 4 requests     │
│  Launches 4 tasks concurrently via asyncio.gather:  │
│                                                     │
│   get_age(name) ──► GET api.agify.io/?name=...      │
│   get_gender(name) ──► GET api.genderize.io/...     │
│   get_nationality(name) ──► GET api.nationalize.io/ │
│   get_rhymes(name) ──► GET api.datamuse.com/...     │
│                                                     │
│  Returns: { age, gender, nationality, rhymes }      │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  namesage/llm.py  generate_profile(name, ...)       │
│  ─────────────────────────────────────────────────── │
│  1. Check OPENROUTER_API_KEY env var                │
│  2. Build system + user prompt with all API data    │
│  3. POST to openrouter.ai/api/v1/chat/completions   │
│  4. Extract choice[0].message.content               │
│  Returns: profile_text (or fallback message)        │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  namesage/formatter.py  print_profile(name, data)   │
│  ─────────────────────────────────────────────────── │
│  1. Print title bar "📊  NameSage — Profile: X"    │
│  2. Age Panel (green text, record count)            │
│  3. Gender Panel (capitalized, % probability)       │
│  4. Nationality Table (colored country codes, %)    │
│  5. Rhyming Words Panel (comma-separated)            │
│  6. LLM Profile section (markdown text)              │
└─────────────────────────────────────────────────────┘
         │
         ▼
      stdout
```

---

## Module dependency graph (ASCII)

```
  namesage/cli.py
      │
      ├──► namesage/api.py          (async data fetching)
      │       └── httpx             (HTTP client)
      │
      ├──► namesage/llm.py          (OpenRouter LLM call)
      │       └── httpx             (HTTP client)
      │
      └──► namesage/formatter.py    (terminal rendering)
              └── rich              (Panels, Tables, Text, Console)
```

All modules depend solely on external libraries (no circular dependencies).

---

## Data flow

```
User input ──► argparse ──► name: str
                                │
                                ▼
                    ┌──────────────────────┐
                    │  fetch_all(name)      │
                    │                       │
                    │  ┌─────────────────┐  │
                    │  │ Agify.io        │──├──► { age, count }
                    │  └─────────────────┘  │
                    │  ┌─────────────────┐  │
                    │  │ Genderize.io    │──├──► { gender, probability }
                    │  └─────────────────┘  │
                    │  ┌─────────────────┐  │
                    │  │ Nationalize.io  │──├──► { country: [...] }
                    │  └─────────────────┘  │
                    │  ┌─────────────────┐  │
                    │  │ Datamuse        │──├──► [{ word, score }, ...]
                    │  └─────────────────┘  │
                    └──────────────────────┘
                              │
                              ▼ (merged dict)
                    ┌──────────────────────┐
                    │  generate_profile()   │──► OpenRouter
                    └──────────────────────┘
                              │ (LLM text)
                              ▼
                    ┌──────────────────────┐
                    │  print_profile()     │──► Rich Console (stdout)
                    └──────────────────────┘
```

---

## Error handling paths

```
API failure (network down, 5xx):
  └─► _get() returns {"error": "..."}
  └─► fetch_all() passes error dict through
  └─► print_profile() shows warning panel for that section
  └─► LLM still runs with available data
  └─► Other sections unaffected

No OPENROUTER_API_KEY:
  └─► generate_profile() returns fallback message
  └─► print_profile() skips the LLM profile section
  └─► All data panels still render

LLM HTTP error:
  └─► generate_profile() returns error text
  └─► print_profile() shows error message in LLM section
  └─► Data panels unaffected
```

---

## Startup and teardown

1. Python imports all modules at `import namesage.cli`
2. `main()` parses arguments
3. One `httpx.AsyncClient` session per `fetch_all()` call (managed by `async with`)
4. One `httpx.AsyncClient` session per `generate_profile()` call
5. Both sessions close automatically on completion
6. `print_profile()` writes directly to stdout
7. Process exits with code 0 (success) or 1 (error)