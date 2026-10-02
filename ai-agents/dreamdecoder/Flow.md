# Flow.md — DreamDecoder Execution Flow

## Module Dependency Graph

```
main.py
  └── src/cli.py         (argument parsing, command dispatch)
        ├── src/engine.py   (LLM dream interpretation)
        │     └── subprocess → /opt/venv/bin/hermes chat
        ├── src/journal.py  (persistent JSON journal)
        ├── src/models.py   (data models: DreamEntry, DreamStats)
        └── src/display.py  (terminal output formatting)
```

## Entry Point: `python main.py <command> [args]`

### 1. Command Dispatch (cli.py)

```
main()
  └── build_parser()         → argparse with subcommands:
                                  log, list, view, search, stats, delete, clear
  └── dispatch[command]()    → routes to handler
```

### 2. `log` — Record and interpret a dream

```
cmd_log(text, tags)
  │
  ├── engine.interpret(dream_text)
  │     │
  │     ├── _call_llm(dream_text)
  │     │     ├── subprocess.run(["hermes", "chat", "-p", "chief", "-q", prompt])
  │     │     └── _parse_json_response(raw_output)
  │     │           ├── Strip markdown code fences
  │     │           ├── Extract JSON object via regex
  │     │           └── Construct DreamInterpretation
  │     │
  │     └── _fallback_interpret(dream_text)   ← if LLM fails/times out
  │           ├── Check text against SYMBOL_LIBRARY (12+ keywords)
  │           ├── Aggregate symbols, themes, moods
  │           └── Construct DreamInterpretation
  │
  ├── DreamEntry(dream_text=..., interpretation=..., tags=...)
  │     └── Dataclass with auto-generated UUID + UTC timestamp
  │
  ├── journal.save_entry(entry)
  │     ├── _load_raw()         → read JSON file (or empty dict)
  │     ├── Append entry.to_dict()
  │     └── _save_raw()         → atomic write via tmp + rename
  │
  └── display.print_entry(entry)
        ├── Rule line with entry ID
        ├── Dream text + tags
        ├── Symbols, mood, themes (if interpreted)
        └── Full interpretation text (indented)
```

### 3. `list` — Browse journal

```
cmd_list()
  └── journal.load_all()
  │     ├── _load_raw() → read JSON → parse entries
  │     └── DreamEntry.from_dict() for each → sort by date DESC
  └── display.print_entry_list(entries)
        └── Numbered list: ID, date, preview, top 3 symbols
```

### 4. `view <id>` — Show single entry

```
cmd_view(entry_id)
  └── journal.get_entry(entry_id)
  │     └── Linear scan through load_all() → match by ID
  └── display.print_entry(entry, detailed=True)
```

### 5. `search <query>` — Keyword search

```
cmd_search(query)
  └── journal.search_entries(query)
  │     ├── load_all() → for each entry:
  │     │     Check dream_text (lower)
  │     │     Check interpretation text
  │     │     Check symbols
  │     │     Check themes
  │     │     Check tags
  │     └── Return matching entries
  └── display.print_entry_list(results)
```

### 6. `stats` — Dream insights

```
cmd_stats()
  └── journal.compute_stats()
  │     ├── load_all() → aggregate:
  │     │     - Total entry count
  │     │     - Symbol frequency (Counter)
  │     │     - Theme frequency (Counter)
  │     │     - Mood distribution (Counter)
  │     │     - First/last entry dates
  │     └── Return DreamStats dataclass
  └── display.print_stats(stats)
        ├── Entry count + date range
        ├── Top symbols table
        ├── Top themes table
        └── Mood distribution ASCII bar chart
```

### 7. `delete <id>` — Remove entry

```
cmd_delete(entry_id, force)
  ├── journal.get_entry(entry_id) → confirm exists
  ├── (if not --force) prompt for confirmation
  └── journal.delete_entry(entry_id)
        └── _load_raw() → filter out ID → _save_raw()
```

### 8. `clear` — Remove all entries

```
cmd_clear(force)
  ├── journal.load_all() → count
  ├── (if not --force) prompt for "yes"
  └── journal.clear_all()
        └── _load_raw() → empty entries array → _save_raw()
```

## Data Flow Summary

```
 User Input (CLI args)
     │
     ▼
 cli.py: argparse parsing
     │
     ├── log → engine.interpret(text)
     │              │
     │              ├── [LLM available] ──→ Hermes CLI ──→ JSON parse ──→ DreamInterpretation
     │              └── [LLM offline]  ──→ Symbol library ──→ DreamInterpretation
     │
     └── other commands → journal module
              │
              └── ~/.dreamdecoder_journal.json (JSON file)
                       │
                       ├── read  → DreamEntry.from_dict()
                       └── write ← DreamEntry.to_dict()

 display.py: format & print
     │
     ▼
 Terminal output (emoji-rich, box-drawn)
```

## File Layout

```
dreamdecoder/
├── main.py               → calls src/cli.py::main()
├── src/
│   ├── cli.py            → Argparse, command dispatch
│   ├── engine.py         → LLM + fallback interpretation
│   ├── journal.py        → JSON file CRUD
│   ├── models.py         → DreamEntry, DreamInterpretation, DreamStats
│   └── display.py        → Terminal formatting
├── tests/
│   ├── test_models.py    → Model serialization tests
│   └── test_journal.py   → Journal persistence tests
├── Decisions.md          → Architectural decisions
├── Flow.md               → This file
├── README.md             → Quick start
└── requirements.txt      → Dependencies (none external)
```