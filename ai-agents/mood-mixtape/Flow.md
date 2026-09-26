# Flow.md — Mood Mixtape Execution Trace

## Module Dependency Graph

```
mood_mixtape/
├── cli.py           ← entry point (depends on: curator, card, musicbrainz, models)
├── card.py          ← output formatter (depends on: models)
├── curator.py       ← LLM-based curation (depends on: models, openai)
├── musicbrainz.py   ← MusicBrainz API client (depends on: models, httpx)
├── models.py        ← data classes (no deps outside stdlib)
└── __init__.py      ─ package marker
```

## Execution Flow: `mood-mixtape "feeling nostalgic"`

### Phase 1 — CLI Parsing
```
entry: cli.main()
  └─ argparse parses argv: mood="feeling nostalgic", interactive=False
  └─ calls cli.run(mood="feeling nostalgic")

flow:
  [1] input: mood="feeling nostalgic"      → mood_input = "feeling nostalgic"
  [2] output: "[bold cyan]Analyzing mood:[/bold cyan] ..."
```

### Phase 2 — Mood Analysis (LLM Call #1)
```
flow:
  [3] cli.run calls curator.analyze_mood("feeling nostalgic")
  [4] curator.analyze_mood:
        ├─ creates OpenAI client (env: OPENAI_API_KEY + OPENAI_BASE_URL)
        ├─ builds user prompt: "Analyze this mood description and extract music-relevant metadata..."
        ├─ calls chat.completions.create(
        │    model=os.environ["LLM_MODEL"] or "deepseek/deepseek-v4-flash",
        │    messages=[{"role": "user", "content": prompt}],
        │    response_format={"type": "json_object"},
        │    temperature=0.7
        │  )
        └─ returns dict { mood, description, search_keywords, genres }
```

### Phase 3 — MusicBrainz Search
```
flow:
  [5] cli.run calls _get_mood_keywords(mood_analysis) → extracts keywords + genres
  [6] cli.run calls musicbrainz.search_by_mood_keywords(keywords, limit=40)
  [7] musicbrainz.search_by_mood_keywords:
        ├─ for each keyword in keywords:
        │     ├─ query MusicBrainz /ws/2/recording with tag:{keyword}
        │     ├─ rate-limit wait (1 req/s enforcement)
        │     └─ parse response JSON into Track objects
        ├─ deduplicate by (title, artist) key
        └─ returns list[Track] (up to 40)
```

### Phase 4 — Mixtape Curation (LLM Call #2)
```
flow:
  [8] cli.run calls curator.curate_mixtape("feeling nostalgic", tracks)
  [9] curator.curate_mixtape:
        ├─ builds track_text: numbered list of up to 40 tracks
        ├─ builds user prompt: "Create a themed mixtape of exactly 8 songs..."
        ├─ calls chat.completions.create(
        │    model=..., messages=[...],
        │    response_format={"type": "json_object"},
        │    temperature=0.8
        │  )
        ├─ also calls analyze_mood again for mood_label (reuses same result in practice)
        ├─ parses JSON into MixtapeSong objects
        └─ returns Mixtape { mood, playlist_name, cover_art_description, songs }
```

### Phase 5 — Output (Card Formatting)
```
flow:
  [10] cli.run calls card.print_mixtape(mixtape)
  [11] card.print_mixtape:
        ├─ card.format_mixtape(mixtape):
        │     ├─ builds Title: "🎵 MOOD MIXTAPE 🎵" (centered, magenta)
        │     ├─ builds Mood Panel: mood label + description
        │     ├─ builds Cover Art Panel: ASCII art frame + DALL-E prompt
        │     ├─ builds Vibe Panel: playlist name + vibe description
        │     ├─ builds Tracklist Table: 8 rows × 4 columns
        │     │   (#, Song, Artist, Why It Fits)
        │     └─ builds Footer: ✨ Curated by Mood Mixtape • N tracks
        └─ prints via rich.console (captured and assembled)
```

## Alternative Execution Paths

### Path A: Interactive Mode
```
mood-mixtape -i
  └─ cli.main() sees args.interactive=True
  └─ cli.run(interactive=True)
        └─ [1] prompts: "🎵 How are you feeling right now?"
        └─ [2] same as Phase 2-5 above
```

### Path B: No Results from MusicBrainz
```
search_by_mood_keywords returns []
  └─ cli.run falls back to search_by_mood_keywords(["popular", "recording"], limit=30)
  └─ still empty: prints error and exits with code 1
```

### Path C: Help / No Args
```
mood-mixtape (no args, no -i)
  └─ cli.main() prints help text + example
  └─ exits with code 0
```

## Data Flow Diagram

```
User Mood Input ("stressed after work...")
        │
        ▼
┌─────────────────┐
│  curator.py     │  ◄── LLM Call #1
│  analyze_mood() │       → mood analysis + search keywords
└────────┬────────┘
         │ dict {mood, description, keywords, genres}
         ▼
┌─────────────────┐
│ musicbrainz.py  │  ◄── HTTP GET × N (rate-limited)
│ search_by_      │       → MusicBrainz Recording API
│ mood_keywords() │       → list of Track objects
└────────┬────────┘
         │ list[Track] (up to 40)
         ▼
┌─────────────────┐
│  curator.py     │  ◄── LLM Call #2
│ curate_mixtape()│       → 8-song mixtape with explanations
└────────┬────────┘
         │ Mixtape object
         ▼
┌─────────────────┐
│  card.py        │  ◄── Rich formatting engine
│ format_mixtape()│       → colored terminal output
└────────┬────────┘
         │ str (Rich markup)
         ▼
    Terminal Output
  (beautiful mixtape card)
```

## Key Call Chains (Function Level)

```python
# Primary execution path
main() → run(mood)
  ├── analyze_mood(mood_input, client=None) → dict
  │     └── _get_openai_client() → OpenAI
  │     └── OpenAI.chat.completions.create(...) → ChatCompletion
  │
  ├── _get_mood_keywords(mood_analysis) → list[str]
  │
  ├── search_by_mood_keywords(keywords, limit) → list[Track]
  │     ├── _rate_limit() → sleep if <1s since last call
  │     ├── _get(endpoint, params) → dict
  │     │     └── _get_client() → httpx.Client
  │     │     └── client.get(url, headers=..., params=...) → Response
  │     └── deduplicate before returning
  │
  ├── curate_mixtape(mood_input, tracks, client=None) → Mixtape
  │     └── analyze_mood() [reuses same result]
  │     └── OpenAI.chat.completions.create(...) → ChatCompletion
  │     └── parse JSON → list[MixtapeSong]
  │
  └── print_mixtape(mixtape)
        └── format_mixtape(mixtape) → str
              └── Rich Panel, Table, Text composition
```