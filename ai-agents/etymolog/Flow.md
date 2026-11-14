# Flow — etymolog

## Execution Trace

```
main()  [etymolog.py:152]
  │
  ├─ argparse.ArgumentParser.parse_args()
  │   Reads sys.argv or sys.stdin
  │   Returns args.word, args.json, args.no_llm
  │
  ├─ word = word.strip().lower()
  │
  ├─ fetch_etymology(word)  [etymolog.py:59]
  │   │
  │   ├─ MediaWiki parse API (action=parse, page=word, prop=text)
  │   │   URL: https://en.wiktionary.org/w/api.php
  │   │   Returns: HTML etymology section → regex-stripped plain text
  │   │
  │   ├─ Wiktionary REST API (page/definition/{word})
  │   │   URL: https://en.wiktionary.org/api/rest_v1/page/definition/{word}
  │   │   Returns: structured definitions by language
  │   │
  │   └─ Returns dict with: etymology (str), definitions (list), language (str)
  │
  ├─ fetch_related_words(word, limit=8)  [etymolog.py:26]
  │   │
  │   ├─ Datamuse /words?ml={word}&max={limit}
  │   │   Returns: semantically similar words (score-ranked)
  │   │
  │   ├─ Datamuse /words?rel_rhy={word}&max={limit}
  │   │   Returns: rhyming words (score-ranked)
  │   │
  │   ├─ Datamuse /words?rel_trg={word}&max=5
  │   │   Returns: trigger/associated words
  │   │
  │   └─ Returns dict with: similar, rhymes, triggers (each: [{word, score}])
  │
  ├─ generate_narrative(word, etymology, related)  [etymolog.py:103]
  │   │
  │   ├─ Check OPENROUTER_API_KEY env var
  │   │   │
  │   │   ├─ PRESENT: POST https://openrouter.ai/api/v1/chat/completions
  │   │   │   Model: deepseek/deepseek-v4-flash
  │   │   │   System: "You are an engaging word-etymology guide..."
  │   │   │   User: word data + etymology + related words
  │   │   │   Returns: 3-4 paragraph narrative
  │   │   │
  │   │   └─ ABSENT: _fallback_narrative(word, etymology, related)  [etymolog.py:133]
  │   │       Returns: structured plain-text report with sections
  │   │         • Origin (etymology text)
  │   │         • Definitions (numbered)
  │   │         • Similar Words (comma-separated)
  │   │         • Rhymes (comma-separated)
  │   │         • Associated Words (comma-separated)
  │   │
  │   └─ Returns narrative string
  │
  ├─ format_output(word, etymology, related, narrative)  [etymolog.py:148]
  │   Assembles bordered ASCII art box with title + narrative + data sources
  │   Returns formatted string
  │
  └─ Output
      ├─ args.json=True → json.dumps({word, etymology, related, narrative})
      └─ args.json=False → print(format_output(...))
```

## Module Dependency Graph

```
etymolog.py
  │
  ├─ urllib.request  (stdlib)     — HTTP calls to Wiktionary, Datamuse, OpenRouter
  ├─ urllib.parse    (stdlib)     — URL encoding
  ├─ urllib.error    (stdlib)     — HTTP error handling
  ├─ json            (stdlib)     — API response parsing
  ├─ argparse        (stdlib)     — CLI argument parsing
  ├─ sys             (stdlib)     — stdin, exit codes
  ├─ os              (stdlib)     — env vars
  ├─ re              (stdlib)     — HTML tag stripping
  └─ dataclasses     (stdlib)     — data structures (unused in final, vestigial)

test_etymolog.py
  │
  ├─ unittest        (stdlib)     — test framework
  ├─ unittest.mock   (stdlib)     — HTTP mocking
  └─ etymolog        (local)      — module under test
```

## Data Flow

```
User Input (word)
     │
     ▼
┌─────────────────────┐     ┌──────────────────────────────┐
│  Wiktionary API      │◄────│  fetch_etymology()           │
│  (parse + REST)      │     │  Returns: etymology text +   │
│  CC-BY-SA licensed   │     │  definitions                 │
└─────────────────────┘     └──────────┬───────────────────┘
                                        │
┌─────────────────────┐     ┌──────────▼───────────────────┐
│  Datamuse API        │◄────│  fetch_related_words()       │
│  (ml, rel_rhy,       │     │  Returns: similar, rhymes,  │
│   rel_trg)           │     │  trigger words              │
└─────────────────────┘     └──────────┬───────────────────┘
                                        │
┌─────────────────────┐     ┌──────────▼───────────────────┐
│  OpenRouter API      │◄────│  generate_narrative()        │
│  (LLM)               │     │  Optional: needs API key     │
│  deepseek-v4-flash   │     │  Fallback: _fallback_narr.   │
└─────────────────────┘     └──────────┬───────────────────┘
                                        │
                               ┌────────▼────────┐
                               │ format_output()  │
                               │ ASCII art box    │
                               └────────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │ stdout / JSON    │
                               │ print()          │
                               └─────────────────┘
```

## Entry Points

| Entry Point | File | Line | Trigger |
|-------------|------|------|---------|
| `main()` | `etymolog.py` | 152 | `python3 etymolog.py <word>` or pip-installed CLI |
| Test runner | `test_etymolog.py` | 107 | `python3 -m unittest test_etymolog.py` |

## Error Handling Strategy

| Error | Where | Behavior |
|-------|-------|----------|
| Network failure (Datamuse) | `fetch_related_words()` | Returns partial data with error key in result dict |
| HTTP 404 (Wiktionary) | `fetch_etymology()` | Returns empty etymology string, continues with definitions |
| Missing OPENROUTER_API_KEY | `generate_narrative()` | Falls back to `_fallback_narrative()` template |
| LLM API timeout | `generate_narrative()` | Falls back to template + appends error note |
| No word provided | `main()` | Prints help and exits with code 1 |
| Invalid UTF-8 in API response | `json.loads()` | Propagates to caller as exception (rare, unhandled) |