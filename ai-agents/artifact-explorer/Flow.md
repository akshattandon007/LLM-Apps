# Flow — Execution trace from CLI entry to gallery output

## High-level pipeline

```
main.py entry ──► identifier.identify_*() ──► historian.generate_story()
                ──► gallery.print_card()
```

## Detailed call chain

### 1. Entry point: `main.py`

```
main()
├── argparse parses: --describe QUERY | --snap PATH | --simulate | --list
│
├── cmd_describe(query)
│   ├── src.identifier.identify_from_text(query)
│   │   └── _fuzzy_match(query) → name_key
│   │       scans KEYWORD_MAP for keyword hits → ARTIFACT_LIBRARY
│   │   └── returns IdentificationResult | None
│   ├── [if None] print "not identified" → sys.exit(1)
│   └── src.historian.generate_story(ident)
│       └── lookup STORIES[ident.name] | _fallback_story(ident)
│       └── returns Artifact model
│       └── src.gallery.print_card(artifact)
│           └── format_card() → ArtifactCard (with CARD_TEMPLATE)
│           └── print card.body to stdout
│
├── cmd_snap(path)
│   ├── src.identifier.identify_from_image(path)
│   │   ├── [image file missing] → None
│   │   ├── [simulated] guess from filename stem via _fuzzy_match
│   │   └── [live, future] LLM vision endpoint → IdentificationResult
│   └── [same pipeline as describe]
│
├── cmd_simulate()
│   ├── iterate ARTIFACT_LIBRARY
│   ├── create IdentificationResult for each
│   ├── generate_story() + print_card() for each
│   └── separator between cards
│
└── cmd_list()
    └── enumerate ARTIFACT_LIBRARY with index, name, category
```

## Dependency graph

```
main.py
  ├── src/identifier.py
  │     └── src/models.py (IdentificationResult)
  ├── src/historian.py
  │     └── src/models.py (Artifact)
  └── src/gallery.py
        └── src/models.py (Artifact, ArtifactCard)
```

## Data flow per artifact

```
Text query ("aloe vera")
     │
     ▼
identifier._fuzzy_match()
     │  matches keywords ["aloe", "succulent", "plant", ...]
     ▼
ARTIFACT_LIBRARY["aloe vera"]
     │  {"name": "Aloe Vera ...", "category": "plant", "description": "..."}
     ▼
IdentificationResult(name, category, description)
     │
     ▼
historian.generate_story()
     │  lookup STORIES["Aloe Vera (Aloe barbadensis miller)"]
     ▼
Artifact(name, category, description, origin, era, history,
         cultural_significance, practical_uses, fun_facts, briefing_date)
     │
     ▼
gallery.format_card()
     │  CARD_TEMPLATE with word-wrapping, section dividers, bullet facts
     ▼
ArtifactCard(title, body, tags)
     │
     ▼
stdout (shareable card)
```

## Module responsibilities

| Module | Responsibility | Test strategy |
|--------|---------------|---------------|
| `identifier.py` | Parse query, match keywords, return `IdentificationResult` or None | Test exact match, partial match, miss, empty query |
| `historian.py` | Enrich identification into full `Artifact` story | Test every preset has all fields, fallback for unknowns |
| `gallery.py` | Render `Artifact` as formatted text card | Test output contains all sections, doesn't crash |
| `models.py` | Pydantic models — pure data | Test schema validation, alias serialization |
| `main.py` | CLI arg parsing, dispatch, error handling | Test each subcommand, exit codes, help text |