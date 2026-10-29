# Flow.md — Ingenius

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ingenius.py                       │
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌───────────────┐   │
│  │  main()   │──▶│build_    │──▶│  call_llm()   │   │
│  │          │   │prompt()  │   │               │   │
│  │  - parse  │   │          │   │  - HTTP POST  │   │
│  │    args   │   │  - build │   │    OpenRouter  │   │
│  │  - call   │   │    sys/  │   │  - strip code │   │
│  │    prompt │   │    user  │   │    fences     │   │
│  │  - call   │   │    msg   │   │  - JSON parse │   │
│  │    llm    │   └────┬─────┘   └───────┬───────┘   │
│  │  - format │        │                 │           │
│  │    output │        └─────────────────┘           │
│  └────┬─────┘            (system, user)             │
│       │                                             │
│       ▼                                             │
│  ┌──────────┐                                       │
│  │format_   │                                       │
│  │output()  │                                       │
│  │          │                                       │
│  │ - pretty │                                       │
│  │   print  │                                       │
│  └──────────┘                                       │
└─────────────────────────────────────────────────────┘
```

## Execution Flow

### Entry Point: `main()`

Called when user runs `python ingenius.py <ingredient> [options]`

```
main()
├── argparse.parse_args()
│   ├── positional: ingredient (str, required)
│   ├── --recipe / -r (str, optional)
│   └── --mood / -m (str, optional, choices=[quick, pantry, gourmet])
│
├── build_prompt(ingredient, recipe, mood)
│   ├── Construct system prompt (chef persona, JSON schema, instructions)
│   ├── Construct user prompt (missing ingredient, recipe context, mood)
│   └── Returns (system, user) as tuple of strings
│
├── call_llm(system, user)
│   ├── Read OPENROUTER_API_KEY from os.environ
│   │   └── Missing → sys.exit(1) with error message
│   ├── POST https://openrouter.ai/api/v1/chat/completions
│   │   ├── Headers: Authorization, Content-Type, Referer, Title
│   │   ├── Body: model, messages=[system, user], temperature=0.3, max_tokens=1024
│   │   └── Timeout: 30s
│   ├── resp.raise_for_status() — network/HTTP errors
│   ├── Extract content from response["choices"][0]["message"]["content"]
│   ├── Strip ```json ... ``` markdown fences if present
│   ├── json.loads(content) — parse JSON
│   │   └── Malformed → sys.exit(1) with raw response
│   └── Return parsed dict
│
├── format_output(result, ingredient)
│   ├── Iterate result["substitutes"]
│   │   └── For each: name, ratio, chemistry, tip
│   ├── Build pretty-printed ASCII block
│   └── Return formatted string
│
└── print(formatted_output) → stdout
```

### Data Flow

```
User Input ──▶ argparse ──▶ build_prompt()
                                    │
                                    ▼
                          (system_prompt, user_prompt)
                                    │
                                    ▼
                            call_llm() ──▶ OpenRouter API
                                    │
                                    ▼
                            {"substitutes": [...]}
                                    │
                                    ▼
                          format_output() ──▶ stdout
```

### Module Dependency Graph

```
ingenius.py
├── standard library
│   ├── argparse (CLI argument parsing)
│   ├── json (LLM response parsing)
│   ├── os (environment variable access)
│   └── sys (exit codes, stderr)
│
└── third-party
    └── requests (HTTP client for OpenRouter API)
```

### Error Paths

| Condition | Where caught | Behaviour |
|-----------|-------------|-----------|
| OPENROUTER_API_KEY not set | `call_llm()` | `sys.exit(1)`, stderr: error message + link |
| HTTP error (network/400/500) | `call_llm()` | `resp.raise_for_status()` raises `requests.HTTPError` → unhandled → Python traceback |
| LLM returns non-JSON | `call_llm()` | `sys.exit(1)`, stderr: raw LLM output for debugging |
| Empty substitutes list | `format_output()` | Grace: prints "No substitutes suggested" |
| Timeout (>30s) | `call_llm()` | `requests.Timeout` → unhandled → Python traceback |
| Missing ingredient argument | `main()` | Argparse prints usage and exits 2 |

### Test Coverage Flow

```
test_ingenius.py
├── TestBuildPrompt
│   ├── test_basic_prompt          — ingredient only
│   ├── test_with_recipe           — ingredient + recipe
│   ├── test_quick_mood            — --mood quick
│   ├── test_pantry_mood           — --mood pantry
│   └── test_gourmet_mood          — --mood gourmet
│
├── TestFormatOutput
│   ├── test_basic_format          — 3 substitutes rendered
│   └── test_empty                 — empty list handled
│
├── TestCallLlm (mocked requests.post)
│   ├── test_successful_call       — normal JSON response
│   └── test_markdown_wrapped_json — JSON in ``` fences
│
└── TestCliIntegration
    ├── test_help                  — --help flag
    └── test_no_api_key            — missing env var
```