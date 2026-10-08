# Flow.md — VibeCaster

## Execution Trace

### Startup Path (CLI entry point)

```
shell
└─ $ python vibecaster.py ["optional mood string"]
    │
    ├─ [sys.argv > 1]
    │     YES → mood = sys.argv[1]
    │     NO  → Prompt.ask("How are you feeling?")  # interactive
    │
    ├─ VibeClient.__init__()
    │     ├─ Resolve API key:
    │     │     os.environ["OPENROUTER_API_KEY"] or
    │     │     os.environ["OPENAI_API_KEY"] or
    │     │     ~/.env file parse
    │     ├─ If none found → raise RuntimeError
    │     └─ Create OpenAI client (base_url = openrouter.ai)
    │
    ├─ Console.status("Summoning your vibe package...")
    │
    ├─ VibeClient.generate(mood)
    │     ├─ Call OpenAI client.chat.completions.create(
    │     │     model = "google/gemini-2.5-flash",
    │     │     system_prompt = [SCHEMA + rules],
    │     │     user_message = f"Mood: {mood}",
    │     │     temperature = 0.8,
    │     │     max_tokens = 1500,
    │     │   )
    │     ├─ Parse response:
    │     │     raw = response.choices[0].message.content
    │     │     Strip markdown ``` fences if present
    │     │     data = json.loads(raw)
    │     └─ Return VibePackage(
    │           mood = mood,
    │           palette_hexes = [...],
    │           palette_names = [...],
    │           poem = ...,
    │           playlist = [...],
    │           vibe_shift = ...,
    │           description = ...,
    │         )
    │
    └─ render(vibe)
          ├─ Console.rule("VibeCaster — {mood}")
          ├─ Panel(Markdown(description))
          ├─ "Colour Palette" section:
          │     zip(palette_hexes, palette_names)
          │       → Columns of " ●  #HEX  Name"
          ├─ Panel(poem) with border_style="yellow"
          ├─ "3-Song Playlist" section:
          │     enumerate(playlist) → "N. Title — Artist"
          │                           "   reason"
          └─ Panel(vibe_shift) with border_style="green"
```

### Error Paths

```
VibeClient.__init__() ── no API key found
  → Console.print("[red]❌  No API key found...[/]")
  → sys.exit(1)

VibeClient.generate() ── network/API error
  → caught by `except Exception`
  → Console.print("[red]❌  Vibe generation failed: {e}[/]")
  → sys.exit(1)

Input empty string
  → Console.print("[red]No mood entered. Exiting.[/]")
  → sys.exit(1)
```

---

## Module Dependency Graph

```
vibecaster.py  (entry point)
├── openai.Client           → HTTP → api.openrouter.ai
│                              └─ Returns ChatCompletion
├── json (stdlib)           → parse structured AI response
├── rich.console.Console
│   ├── .print()
│   ├── .rule()
│   ├── .status()           → spinner animation
│   └── Panel, Columns, Markdown, Prompt
├── os.environ / Path       → API key resolution
└── sys.argv / sys.exit()   → CLI arg handling

tests/test_vibecaster.py
└── vibecaster (imported)
    ├── VibePackage
    ├── VibeClient
    │   └── unittest.mock.MagicMock  → injected in tests
    └── render()
        └── capsys (pytest fixture)  → capture & verify output
```

---

## Data Flow

```
User Input
    │
    ▼
String: "tired but hopeful"
    │
    ▼
OpenRouter API (Gemini 2.5 Flash)
    │  System: "<structured JSON schema instructions>"
    │  User:   "Mood: tired but hopeful"
    │
    ▼
JSON Response
    {
      "description": "...",
      "palette": [{"hex": "#...", "name": "..."}, ...],
      "poem": "...",
      "playlist": [{"title": "...", "artist": "...", "reason": "..."}, ...],
      "vibe_shift": "..."
    }
    │
    ▼  json.loads()
    │
VibePackage (dataclass)
    │
    ▼  render()  →  Rich Terminal Panels
    │
    ▼
━━ VibeCaster ── tired but hopeful ━━
┌──────────────────────────┐
│ ✨ description            │
├──────────────────────────┤
│ 🎨 Colour Palette        │
│   ● #HEX1  ● #HEX2 ...  │
├──────────────────────────┤
│ ✍  Poem                  │
├──────────────────────────┤
│ 🎵 3-Song Playlist       │
│  1. Title — Artist       │
│     reason               │
├──────────────────────────┤
│ 🌀 Vibe Shift             │
│   Do-able activity       │
└──────────────────────────┘
```

---

## Key Functions and Their Signatures

| Function | File | Lines | Role |
|---|---|---|---|
| `main()` | vibecaster.py | ~200 | Parse args, init client, call generate & render |
| `VibeClient.__init__()` | vibecaster.py | ~55 | Resolve API key, build OpenAI client |
| `VibeClient.generate(mood)` | vibecaster.py | ~80 | Call LLM, parse & return VibePackage |
| `VibePackage` (dataclass) | vibecaster.py | ~15 | Data model with defaults for all fields |
| `render(vibe)` | vibecaster.py | ~130 | Render VibePackage with Rich panels/sections |
| `_colour_block(hex_code)` | vibecaster.py | ~120 | Create ANSI-coloured text block |