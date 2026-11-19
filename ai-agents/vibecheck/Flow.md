# Flow — VibeCheck Execution Trace

## Entry Points

VibeCheck has three entry paths: **single-shot CLI**, **interactive REPL**, and **programmatic API**. All three converge on the same analysis pipeline in `analyzer.py`.

```
CLI Entry (vibecheck/cli.py)
├── main()
│   ├── parse_args() → argparse.Namespace
│   ├── [--setup]     → setup_config() → save key to ~/.vibecheck/config.json
│   ├── [--interactive] → _interactive_mode()
│   └── [default]       → _single_shot_mode()
│
Programmatic Entry (vibecheck/analyzer.py)
├── analyze_text(text, provider=None) → ToneAnalysis
└── compare_texts(orig, rew, provider=None) → ComparisonResult
```

## Execution Path 1: Single-Shot Analysis

```
User runs:  vibecheck --text "Hey, can you review this?"

main()
├── parse_args() → args.text = "Hey, can you review this?"
│   └── args.interactive = False
│
_single_shot_mode(args)
├── text = args.text
├── result = analyze_text(text)
│   ├── _build_provider()
│   │   ├── os.environ["VIBECHECK_PROVIDER"] → "openrouter" (default)
│   │   ├── os.environ["OPENROUTER_API_KEY"] → "sk-..."
│   │   └── return OpenRouterProvider(api_key, model)
│   │
│   ├── ANALYSIS_PROMPT.format(text=text)
│   │   └── Wraps user text in analysis instructions
│   │
│   ├── provider.query(prompt)
│   │   ├── POST https://openrouter.ai/api/v1/chat/completions
│   │   │   Headers: Authorization, Content-Type, HTTP-Referer
│   │   │   Body: {model, messages: [{role: "user", content: prompt}], temperature: 0.3}
│   │   └── response → {choices: [{message: {content: "..."}}]}
│   │
│   ├── _try_parse_json(raw_response)
│   │   ├── Strip ```json / ``` fences
│   │   ├── json.loads() → dict
│   │   └── Return parsed dict or None
│   │
│   └── ToneAnalysis(overall_tone, emotional_subtext, clarity_score, ...)
│       ├── If parsed: populate from dict keys
│       └── If None: return empty ToneAnalysis with raw_llm_response set
│
_print_analysis(result)
└── Pretty-print formatted analysis to stdout
```

## Execution Path 2: Interactive REPL

```
User runs:  vibecheck --interactive

main()
├── parse_args() → args.interactive = True
│
_interactive_mode(args)
├── Print welcome banner
├── while True:
│   ├── input("vibecheck> ") → user_input
│   │
│   ├── user_input == "quit" / "exit" → break
│   │
│   ├── user_input.startswith("/file ")
│   │   ├── Extract path, read file
│   │   ├── analyze_text(content, provider)
│   │   └── _print_analysis(result)
│   │
│   ├── user_input.startswith("/compare ")
│   │   ├── Split on "|||" → original, rewritten
│   │   ├── compare_texts(original, rewritten, provider)
│   │   │   ├── analyze_text(original) → orig_result
│   │   │   ├── analyze_text(rewritten) → rew_result
│   │   │   ├── COMPARE_PROMPT.format(original, rewritten)
│   │   │   ├── provider.query(compare_prompt)
│   │   │   └── ComparisonResult(original=orig_result, rewritten=rew_result, ...)
│   │   └── _print_comparison(result)
│   │
│   └── default:
│       ├── analyze_text(user_input, provider)
│       └── _print_analysis(result)
```

## Execution Path 3: Pipe/File Input

```
User runs:  cat draft.txt | vibecheck

main()
├── sys.stdin.isatty() → False
├── text = sys.stdin.read().strip()
├── result = analyze_text(text)
└── _print_analysis(result)
```

## Execution Path 4: A/B Comparison

```
User runs:  vibecheck --compare --text "Original ||| Rewritten"

_single_shot_mode(args)
├── parts = text.split("|||")
├── original = parts[0].strip()
├── rewritten = parts[1].strip()
├── result = compare_texts(original, rewritten)
│   ├── analyze_text(original) → ToneAnalysis (orig)
│   ├── analyze_text(rewritten) → ToneAnalysis (rew)
│   ├── COMPARE_PROMPT → provider.query() → diff dict
│   └── ComparisonResult(original=orig, rewritten=rew, differences=..., improvement_areas=...)
└── _print_comparison(result)
```

## Module Dependency Graph

```
vibecheck/
│
├── cli.py ─────────────────────────────────────────────────────┐
│   imports: argparse, sys, os                                  │
│   depends on: analyzer.analyze_text, analyzer.compare_texts,  │
│              analyzer.setup_config                            │
│   called by: python -m vibecheck.cli (entry_points)           │
│                                                               │
├── analyzer.py ◄────────────────────────────────────────────────┘
│   imports: json, os, re, requests, dataclasses                 │
│   exports: analyze_text(), compare_texts(), setup_config(),    │
│            ToneAnalysis, ComparisonResult, LLMProvider         │
│   internal: _build_provider(), _try_parse_json()               │
│                                                               │
├── __init__.py                                                  │
│   exports: __version__                                         │
│                                                               │
tests/                                                           │
│                                                               │
└── test_analyzer.py ────────────────────────────────────────────┘
    imports: pytest, analyzer module
    tests: MockProvider, all ToneAnalysis fields, parse failures,
           comparison, edge cases
```

## Data Flow Diagram

```
User Input
    │
    ▼
┌──────────────────────────────────────────────┐
│  cli.py: main()                               │
│  - Parse args                                 │
│  - Select mode (single/interactive/compare)   │
│  - Extract text from: --text, --file, stdin   │
└─────────────────────┬────────────────────────┘
                      │ text (str)
                      ▼
┌──────────────────────────────────────────────┐
│  analyzer.py: analyze_text(text, provider)    │
│                                               │
│  1. Validate input (non-empty check)          │
│  2. _build_provider() → LLMProvider           │
│  3. Format ANALYSIS_PROMPT with text          │
│  4. provider.query(prompt)                    │
│     ┌─────────────────────────────┐           │
│     │ HTTP POST to LLM API        │           │
│     │ → raw JSON response         │           │
│     └─────────────────────────────┘           │
│  5. _try_parse_json(raw) → dict or None       │
│  6. Build ToneAnalysis dataclass              │
│     (parsed fields or defaults)               │
└─────────────────────┬────────────────────────┘
                      │ ToneAnalysis
                      ▼
┌──────────────────────────────────────────────┐
│  cli.py: _print_analysis(result)              │
│  - Format fields to terminal                  │
│  - Color/emoji annotations                    │
│  - Print to stdout                            │
└──────────────────────────────────────────────┘
                      │
                      ▼
              User reads analysis
```

## Key Call Chains

### analyze_text() call chain:
```
analyze_text(text, provider=None)
  ├── _build_provider()
  │   ├── os.environ.get("VIBECHECK_PROVIDER", "openrouter")
  │   ├── os.environ.get("OPENROUTER_API_KEY")
  │   └── return OpenRouterProvider(api_key, model)
  ├── ANALYSIS_PROMPT.format(text=text[:4000])
  ├── OpenRouterProvider.query(prompt)
  │   └── requests.post(url, headers, json=payload, timeout=60)
  │       └── resp.json()["choices"][0]["message"]["content"]
  ├── _try_parse_json(raw)
  │   ├── re.sub(r'^```(?:json)?\s*', '', text)
  │   └── json.loads(cleaned)
  └── ToneAnalysis(**parsed)  or  ToneAnalysis(raw_llm_response=raw)
```

### compare_texts() call chain:
```
compare_texts(original, rewritten, provider=None)
  ├── analyze_text(original, provider)     → orig_result
  ├── analyze_text(rewritten, provider)    → rew_result
  ├── COMPARE_PROMPT.format(original, rewritten)
  ├── provider.query(compare_prompt)
  ├── _try_parse_json(raw) → parsed dict
  └── ComparisonResult(original=orig_result, rewritten=rew_result, **parsed)
```