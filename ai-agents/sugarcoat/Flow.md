# Flow.md — sugarcoat

## Execution Trace

### Primary Path: `sugarcoat.py` → `sugarcoat_engine.py` → OpenRouter API

```
user
  │
  ▼
sugarcoat.py:main()
  │
  ├── argparse.parse_args()
  │     └── Parses: message, tone, style, context, api-key, model, history, flags
  │
  ├── load_api_key()
  │     ├── os.environ["OPENROUTER_API_KEY"]
  │     ├── os.environ["OPENAI_API_KEY"]  (fallback)
  │     ├── /data/profiles/chief/.env     (system env fallback)
  │     └── Path(".env")                  (cwd fallback)
  │
  ├── sys.stdin.read()                    [--interactive or no message arg]
  │
  ├── json.load(history_file)             [--history <path>]
  │
  ▼
sugarcoat_engine.py:rephrase_message()
  │
  ├── _make_system_prompt(tone, style)
  │     ├── TONE_INSTRUCTIONS[tone]       → emotional register text
  │     ├── STYLE_INSTRUCTIONS[style]      → structural verbosity text
  │     ├── SYSTEM_PROMPT_TEMPLATE.format(…)
  │     └── Returns: combined system prompt string
  │
  ├── _make_user_prompt(message, context, history)
  │     ├── "CONTEXT: …\n"                (if context provided)
  │     ├── "CONVERSATION HISTORY:\n…"    (if history provided, last 5 entries)
  │     └── "MESSAGE TO REPHRASE:\n…"     (the actual message)
  │     └── Returns: combined user prompt string
  │
  ├── httpx.post("https://openrouter.ai/api/v1/chat/completions", …)
  │     ├── Headers: Authorization (Bearer), Content-Type, Referer, X-Title
  │     ├── Body: { model, messages: [system, user], temperature, max_tokens }
  │     └── Returns: OpenAI-compatible chat completion response
  │
  ├── response.raise_for_status()        [HTTP errors → propagate]
  │
  ├── data["choices"][0]["message"]["content"]
  │     └── Raw response text (may include ```json fences)
  │
  ├── Strip markdown fences (```json / ```)
  │
  ├── json.loads(content)                [Structured parse]
  │     ├── Success → {"rephrased", "explanation", "alternatives"}
  │     └── Failure → {"rephrased": <raw_text>}  (fallback)
  │
  └── Returns: result dict
  │
  ▼
sugarcoat.py:main()
  │
  ├── print(result["rephrased"])          [Main output - the improved message]
  ├── print(explanation)                  [Why this version works better]
  └── print(alternatives)                 [1-2 shorter alternative phrasings]
```

### Secondary Path: List Flags (no API call)

```
sugarcoat.py:main()
  │
  ├── --list-tones
  │     └── get_supported_tones()
  │           └── Print each tone name
  │
  └── --list-styles
        └── get_supported_styles()
              └── Print each style name
```

## Module Dependency Graph

```
sugarcoat.py
  ├── sugarcoat_engine.py
  │     ├── httpx          (HTTP client, external)
  │     └── json           (stdlib)
  └── argparse            (stdlib, CLI parsing)
```

All external dependencies: `httpx` (only non-stdlib package).

## Key Data Flow

```
User input (message string)
    │
    ▼
+------------------+     +--------------------+     +--------------------+
|  sugarcoat.py    |────▶│ sugarcoat_engine.py│────▶│ OpenRouter API     │
|  (CLI parser,    |     │                    │     │ (DeepSeek Chat)    │
|   user I/O)      |◀────│  - build prompts   │◀────│                    │
+------------------+     │  - call API        │     +--------------------+
         │               │  - parse JSON      │
         ▼               +--------------------+
   Console output
   (rephrased text,
    explanation,
    alternatives)
```

## Entry Points

| Entry point | Purpose | Typical use |
|---|---|---|
| `python3 sugarcoat.py "message"` | One-shot rephrase | CLI direct |
| `python3 sugarcoat.py -i` | Interactive mode | Read from stdin |
| `python3 sugarcoat.py --list-tones` | Discovery | See available tones |
| `python3 sugarcoat.py --list-styles` | Discovery | See available styles |
| `pytest tests/ -v` | Test suite | All mocked, no API key