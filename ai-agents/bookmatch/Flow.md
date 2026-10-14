# Flow.md — Bookmatch

## Execution Trace

### Entry Point: `main()` in `main.py`

```
main()
├── 1. Check OPENROUTER_API_KEY environment variable
│     ├── Missing → print error + sys.exit(1)
│     └── Present → continue
│
├── 2. run_interview() — interactive question loop
│     ├── Display header banner
│     ├── For each question in QUESTIONS list:
│     │     ├── Print question + choices/hint
│     │     ├── input() > parse answer
│     │     └── Set field on ReaderProfile dataclass
│     └── Return populated ReaderProfile
│
├── 3. build_recommendation_prompt(profile)
│     ├── Format profile fields into strings
│     ├── Build system prompt (expert book recommender persona + rules)
│     ├── Build user prompt (serialized profile data)
│     └── Return (system_prompt, user_prompt)
│
├── 4. call_llm(system_prompt, user_prompt)
│     ├── POST to OpenRouter API (httpx)
│     ├── Raise on HTTP error
│     ├── Parse response JSON
│     └── Return message content (raw text)
│
├── 5. parse_recommendations(raw_text)
│     ├── Strip markdown code fences if present
│     ├── Attempt json.loads() on cleaned text
│     │     ├── Success → iterate items → build BookRec list
│     │     └── JSONDecodeError → regex search for JSON array
│     │           ├── Found → json.loads match → build BookRec list
│     │           └── Not found → return empty list
│     └── Return list[BookRec]
│
├── 5b. [Retry if empty] — call_llm with simpler system prompt → parse again
│
├── 6. display_recommendations(recs, name)
│     ├── Print banner with reader name
│     ├── For each BookRec:
│     │     ├── Print number + title
│     │     ├── Print author + genre + similar_to (if present)
│     │     ├── Print "why" description
│     │     └── Print "perfect for" tag
│     └── Print closing banner
│
├── 7. save_recommendations(recs, name, filepath)
│     ├── Open bookmatch-recs.md for writing
│     ├── Write markdown header + metadata
│     ├── For each BookRec:
│     │     ├── Write ## heading with title
│     │     ├── Write author, genre, similar_to
│     │     ├── Write why description
│     │     └── Write perfect_for blockquote
│     └── Return filepath
│
└── 8. Print saved message
```

## Module Dependency Graph

```
main.py
├── stdlib: os, sys, json, re, dataclasses
├── httpx ──────────► OpenRouter API ▷ external
```

No other internal modules. Single-file architecture.

## Function-Level Call Chain

```
main()
├── run_interview()            interactive_cli.py:40-98
│   └── input()               [builtin]
├── build_recommendation_prompt()  engine.py:72-110
├── call_llm()                engine.py:30-65
│   ├── httpx.post()          external
│   └── json.loads()          [builtin]
├── parse_recommendations()   engine.py:112-145
│   ├── json.loads()          [builtin]
│   └── re.search()           [builtin]
├── display_recommendations() ui.py:147-172
│   └── print()               [builtin]
└── save_recommendations()    ui.py:174-190
    └── open().write()        [builtin]
```

## Key Data Flow

```
User Input (CLI)
    │
    ▼
[run_interview()]
    │  8 questions → structured answers
    ▼
ReaderProfile dataclass
    │  { favorite_books, disliked_books, genres_liked,
    │    recently_read, reading_goal, preferred_length,
    │    mood, dealbreakers }
    ▼
[build_recommendation_prompt()]
    │  Merges profile into system + user prompts
    ▼
System + User prompts (strings)
    │
    ▼
[call_llm()]
    │  httpx.post → OpenRouter → response.choices[0].message.content
    ▼
Raw JSON string
    │
    ▼
[parse_recommendations()]
    │  json.loads → list[dict] → [BookRec(title, author, genre, why, perfect_for, similar_to)]
    ▼
list[BookRec]
    │
    ├──► [display_recommendations()]
    │       Pretty-print to terminal
    │
    └──► [save_recommendations()]
            Write bookmatch-recs.md
```

## Error Handling Flow

```
call_llm() failure:
  HTTP error → return f"Error talking to LLM: {detail}"
  Missing API key → return "⚠️  OPENROUTER_API_KEY not set"
  Timeout (60s) → httpx.TimeoutException → caught as generic Exception

parse_recommendations() failure:
  No valid JSON found → return []
    → main() detects empty list
    → Retry with simpler system prompt
    → If still empty → print raw result for debugging

main() startup check:
  OPENROUTER_KEY is empty string → print error + exit(1)
    (Never attempts API call without key)
```