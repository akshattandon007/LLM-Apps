# Flow.md — SpillBuddy Execution Flow

## Module Dependency Graph

```
spillbuddy/__main__.py
    └─> spillbuddy/cli.py
            └─> spillbuddy/data.py

spillbuddy/cli.py
    ├─> spillbuddy/__init__.py  (for __version__)
    └─> spillbuddy/data.py      (for lookup, list_stains, list_fabrics, STAIN_DB)

spillbuddy/data.py
    └─> (stdlib only — no imports)
```

## Entry Point: `spillbuddy` command

```
shell
  │
  ▼
setup.py entry_points → console_scripts → spillbuddy=spillbuddy.cli:main
  │
  ▼
main()
  │
  ├─ build_parser()  ──→  argparse.ArgumentParser
  │       │
  │       ├─ subcommand: lookup <stain> <fabric>
  │       ├─ subcommand: list
  │       └─ subcommand: interactive
  │
  ├─ args.command == "lookup"    ──→ cmd_lookup(args)
  ├─ args.command == "list"      ──→ cmd_list(args)
  ├─ args.command == "interactive" ──→ cmd_interactive(args)
  └─ else                        ──→ parser.print_help() + sys.exit(1)
```

## Execution Path: `spillbuddy lookup "red wine" cotton`

```
cmd_lookup(args)
  │
  ├─ args.stain = "red wine"
  ├─ args.fabric = "cotton"
  │
  ▼
data.lookup("red wine", "cotton")
  │
  ├─ stain = "red wine".strip().lower()  → "red wine"
  ├─ fabric = "cotton".strip().lower()   → "cotton"
  │
  ├─ STAIN_DB["red wine"] exists?  ✓
  │     │
  │     └─ STAIN_DB["red wine"]["cotton"] exists?  ✓
  │           │
  │           └─ return {stain, fabric, method, caution}
  │
  └─ returns dict
  │
  ▼
format_result(result)
  │
  ├─ f"🧴 SpillBuddy — {stain.title()} on {fabric.title()}"
  ├─ f"📋 Method:\n  {method}"
  └─ f"⚠️  Caution:\n  {caution}"
  │
  ▼
print to stdout
```

## Execution Path: `spillbuddy lookup "blue paint" cotton`

```
cmd_lookup(args)
  │
  ├─ args.stain = "blue paint"
  ├─ args.fabric = "cotton"
  │
  ▼
data.lookup("blue paint", "cotton")
  │
  ├─ stain = "blue paint"
  │
  ├─ STAIN_DB["blue paint"] exists?  ✗
  │
  └─ return None
  │
  ▼
cmd_lookup → prints error + known stains → sys.exit(1)
```

## Execution Path: `spillbuddy lookup "coffee" linen`

```
cmd_lookup(args)
  │
  ▼
data.lookup("coffee", "linen")
  │
  ├─ stain = "coffee"  →  STAIN_DB["coffee"] exists?  ✓
  ├─ fabric = "linen"  →  STAIN_DB["coffee"]["linen"] exists?  ✗
  │
  └─ STAIN_DB["coffee"]["all"] exists?  ✓
        │
        └─ return {stain="coffee", fabric="linen", method, caution}
  │
  ▼
format_result → stdout (using the "all" fabric fallback)
```

## Execution Path: `spillbuddy list`

```
cmd_list(args)
  │
  ├─ for stain in list_stains():
  │     ├─ fabrics = STAIN_DB[stain].keys() (excluding "all")
  │     ├─ print(f"• {stain.title()}")
  │     └─ print(f"  Fabrics: {fabric_str}")
  │
  └─ print total count + usage tip
```

## Execution Path: `spillbuddy interactive`

```
cmd_interactive(args)
  │
  ├─ print welcome message
  │
  └─ LOOP:
       ├─ input("What did you spill? ")
       │    ├─ "quit"/"exit"/"q" → break
       │    ├─ "list" → print stain names, continue
       │    └─ else → validate stain exists
       │
       ├─ input("On what fabric? ")
       │    ├─ "quit"/"exit"/"q" → break
       │    └─ else → validate fabric
       │
       ├─ data.lookup(stain, fabric)
       │    ├─ found → format_result + print
       │    └─ not found → error message
       │
       └─ (loop continues)
```

## Data Flow

```
User Input (CLI args or interactive prompt)
       │
       ▼
  normalize: .strip().lower()
       │
       ▼
  STAIN_DB dict lookup  ── key: stain_name
       │
       ▼
  fabric dict lookup  ── key: fabric_type (falls back to "all")
       │
       ▼
  (method_text, caution_text) tuple
       │
       ▼
  format_result() → formatted string
       │
       ▼
  stdout
```

## Key Functions

| Function | File | Called By | Purpose |
|---|---|---|---|
| `main()` | `cli.py` | entry point | Parse args, dispatch command |
| `build_parser()` | `cli.py` | `main()` | Build argparse with subcommands |
| `cmd_lookup()` | `cli.py` | `main()` | Handle lookup subcommand |
| `cmd_list()` | `cli.py` | `main()` | Handle list subcommand |
| `cmd_interactive()` | `cli.py` | `main()` | Handle interactive mode |
| `format_result()` | `cli.py` | `cmd_lookup()`, `cmd_interactive()` | Format output for display |
| `lookup()` | `data.py` | `cmd_lookup()`, `cmd_interactive()` | Query the stain database |
| `list_stains()` | `data.py` | `cmd_list()`, `cmd_interactive()` | Get sorted stain names |
| `list_fabrics()` | `data.py` | `cmd_interactive()` | Get fabric types for prompt |