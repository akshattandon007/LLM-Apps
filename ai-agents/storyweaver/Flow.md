# Flow.md

## Execution flow for StoryWeaver

### Entry point

```
storyweaver <command> [options]
  │
  └─► cli.py:main()
       │
       ├─► argparse.parse_args()
       │    └─► dispatches to:
       │         ├─► cmd_new()     for "new" command
       │         ├─► cmd_continue() for "continue" command
       │         └─► cmd_list()    for "list" command
```

---

### Path A: `storyweaver new` — Starting a new story

```
cmd_new(args)
  │
  ├─► Prompt user for: title, genre, setting, characters, premise
  │    (or read from --flags if provided non-interactively)
  │
  ├─► StorySession(title, genre, setting, characters, premise)
  │    └─► models.StorySession.__init__()
  │         Initialises empty nodes list, current_node_id=0, history=[]
  │
  ├─► _get_engine(args)
  │    └─► StoryEngine(api_key, api_base, model, max_tokens, temperature)
  │         └─► engine.StoryEngine.__init__()
  │              Reads LLM_API_KEY from env if not passed explicitly
  │
  ├─► engine.generate_first_chapter(session)
  │    └─► engine.StoryEngine.generate_first_chapter()
  │         ├─► FIRST_CHAPTER_PROMPT.format(title, genre, setting, characters, premise)
  │         │    └─► prompts.FIRST_CHAPTER_PROMPT — template string
  │         ├─► _call_api([system_prompt, user_prompt])
  │         │    └─► engine.StoryEngine._call_api()
  │         │         ├─► requests.post(
  │         │         │     "{api_base}/v1/chat/completions",
  │         │         │     headers={Authorization, ...},
  │         │         │     json={model, messages, max_tokens, temperature, response_format}
  │         │         │   )
  │         │         ├─► resp.raise_for_status()
  │         │         ├─► json.loads(content)  (with markdown-fence fallback)
  │         │         └─► returns parsed dict {narrative, choices}
  │         │
  │         ├─► Build StoryNode(id=1, narrative, choices) from response
  │         └─► Returns StoryNode
  │
  ├─► session.add_node(node)
  │    └─► models.StorySession.add_node()
  │         ├─► Appends node to session.nodes[]
  │         ├─► Sets session.current_node_id = node.id
  │         └─► Updates session.updated_at timestamp
  │
  ├─► _display_node(node) — prints narrative + choices to terminal
  │    └─► cli._display_node()
  │
  ├─► _save_and_continue(session, engine, args)
  │    └─► cli._save_and_continue()
  │
  │    LOOP:
  │    ├─► session.get_current_node()
  │    │    └─► models.StorySession.get_current_node()
  │    │         └─► Find node in nodes[] where id == current_node_id
  │    │
  │    ├─► IF no choices left → generate epilogue
  │    │    └─► engine.generate_epilogue(session)
  │    │         ├─► SUMMARY_PROMPT.format(title, genre, chapter_count)
  │    │         └─► _call_api(...) → returns epilogue text
  │    │
  │    ├─► _get_choice(node) — prompt user for 1-3 or 's'
  │    │    └─► cli._get_choice()
  │    │         └─► Returns choice index (0-2) or None for save & quit
  │    │
  │    ├─► IF choice is None → session.save(path), return
  │    │
  │    ├─► chosen = current.choices[choice]
  │    ├─► _find_node_by_id(session, chosen.next_node_id)
  │    │    └─► cli._find_node_by_id() — linear search nodes[]
  │    │
  │    ├─► IF next_node already exists → set current_node_id and loop
  │    │
  │    ├─► ELSE → generate next chapter
  │    │    └─► engine.generate_next_chapter(session, chosen_text)
  │    │         ├─► _build_narration_history(session)
  │    │         │    └─► Concatenates recent node narratives (newest-first, capped at 3000 chars)
  │    │         ├─► max node id + 1 → next_id
  │    │         ├─► NEXT_CHAPTER_PROMPT.format(...)
  │    │         ├─► _call_api([system_prompt, user_prompt])
  │    │         └─► Returns StoryNode(id=next_id, narrative, choices)
  │    │
  │    ├─► session.add_node(node)
  │    ├─► session.save(path)
  │    └─► _display_node(node) — show new chapter
  │         ↓
  │    REPEAT until user quits or story ends
```

---

### Path B: `storyweaver continue` — Resuming a saved story

```
cmd_continue(args)
  │
  ├─► Resolve save path (--story-id → ~/.storyweaver/saves/{id}.json)
  │    or use explicit --path
  │
  ├─► StorySession.load(path)
  │    └─► models.StorySession.load() [classmethod]
  │         ├─► json.load(file)
  │         └─► from_dict(data)
  │              └─► models.StorySession.from_dict()
  │                   ├─► Session(**metadata)
  │                   └─► For each node dict: StoryNode(id, narrative, choices)
  │                        └─► For each choice dict: Choice(text, next_node_id)
  │
  ├─► StoryEngine(api_key, api_base, model, ...)
  │
  └─► Same LOOP as Path A (line 71 onwards)
```

---

### Path C: `storyweaver list` — Listing saved stories

```
cmd_list(args)
  │
  ├─► _resolve_saves_dir()
  │    └─► Path.home() / ".storyweaver" / "saves"
  │         mkdir(parents=True, exist_ok=True)
  │
  ├─► saves = sorted(saves_dir.glob("*.json"))
  │
  └─► For each save file:
       ├─► StorySession.load(path)
       └─► Print: [id] title (genre) | Chapters: N | Created: YYYY-MM-DD
```

---

### Module dependency graph

```
         cli.py
        /   |   \
       /    |    \
      /     |     \
engine.py  models.py  prompts.py
     |         |
     |    requests (JSON I/O)
     |
  requests (HTTP → LLM API)
       ↓
   openai-compatible API
   (OpenRouter / OpenAI / local)
```

**Directional edges (imports):**
- `cli.py` → `engine.py`, `models.py`
- `engine.py` → `models.py`, `prompts.py`, `requests`
- `models.py` → `json`, `dataclasses`, `datetime`
- `prompts.py` — leaf module (no internal imports)

---

### Key data flow: User input → Story output

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  User input  │────►│  cli.py      │────►│  models.py  │
│  (title,     │     │  (argparse)  │     │ (dataclass) │
│   genre,     │     └──────┬───────┘     └──────┬──────┘
│   choice)    │            │                    │
└─────────────┘            ▼                    ▼
                     ┌──────────────┐     ┌─────────────┐
                     │  engine.py   │     │  JSON file  │
                     │  (prompts +  │────►│  on disk    │
                     │   API call)  │     │  (persist)  │
                     └──────┬───────┘     └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  LLM API     │
                     │  (generates  │
                     │   narrative) │
                     └──────────────┘
```

**Direction of data flow:**
1. User enters story parameters (title, genre, setting, characters, premise)
2. `cli.py` constructs a `StorySession` object and passes it to `engine.py`
3. `engine.py` builds prompts, sends them to the LLM API via `requests`
4. API response is parsed into `StoryNode` (with `Choice` children)
5. Node is added to the session, session is serialized to JSON on disk
6. User reads the narrative, makes a choice
7. Choice loops back to step 3-5 for the next chapter
8. When the user quits or the story ends, final state is saved

### File overview

| File | Lines | Purpose |
|------|-------|---------|
| `cli.py` | ~210 | CLI entry point, all 3 commands, user interaction loop |
| `engine.py` | ~170 | API communication, prompt construction, response parsing |
| `models.py` | ~90 | Data classes: StorySession, StoryNode, Choice |
| `prompts.py` | ~70 | All LLM prompt templates in one place |
| `tests/test_models.py` | ~120 | Unit tests for data models |
| `tests/test_engine.py` | ~110 | Unit tests for engine with mocked API |
| `tests/test_cli.py` | ~70 | Unit tests for CLI interaction |
