# Flow — Roster Execution Trace

**How `main.py` takes user input → tone → roasts → card output.**

---

## Entry point

```
$ python main.py --simulate --tone siblings
```

```
main.py::main()
  ├─ argparse parses --simulate, --tone=siblings
  └─ cmd_simulate(args)
```

```
main.py::cmd_simulate()
  ├─ TONE_MAP["siblings"] → Tone(name="siblings", intensity=4)
  ├─ EXAMPLE_GROUPS[0..2]
  ├─ Roaster()
  └─ for each group:
       └─ roaster.generate_roasts(group, tone, simulate=True)
            → RoastCard
            └─ format_card(card) → str
```

---

## Interactive flow

```
$ python main.py --roast
```

```
main.py::cmd_roast(args)
  ├─ _select_tone()          # user picks from list
  ├─ _describe_people()      # user enters names + descriptions
  │     └─ GroupPhoto(title, setting, people=[Person, ...])
  ├─ Roaster()
  └─ roaster.generate_roasts(group, tone, simulate=True)
       → RoastCard
       └─ format_card(card) → str  (optionally saved to file)
```

---

## Call chain

```
main.py                         # CLI parsing, user prompts
  │
  ├── src.tones.list_tones()    # returns all Tone objects
  ├── src.tones.TONE_MAP        # name → Tone lookup
  │
  ├── src.roaster.Roaster()
  │     ├── __init__()          # loads LLM_API_KEY from .env
  │     ├── set_client(key)     # inject API key (testing / reconfigure)
  │     └── generate_roasts(group, tone, simulate)
  │           ├── _simulated_roast()     # (simulate=True)
  │           │     ├── _pick_roasts(person, tone)     # templates lookups
  │           │     ├── _group_roast(group, tone)      # one-liner for group
  │           │     └── _make_footer(tone)              # closing line
  │           │
  │           └── _live_roast()   # (simulate=False + api_key set)
  │                 └── falls back to _simulated_roast
  │
  └── src.card.format_card(card)
        ├── _rule()           # horizontal rule chars
        ├── _center()         # centre text in card width
        ├── _wrap()           # textwrap for interior
        └── (optional) file write
```

---

## Dependency graph

```
main.py
  ├── src.card ─────────────────────────┐
  │   ├── (no sub-deps, pure formatting)│
  │   └── imports: src.models           │
  │                                     │
  ├── src.roaster ──────────────────────┤
  │   ├── src.models                    │
  │   ├── src.tones                     │
  │   └── external: python-dotenv       │
  │                                     │
  ├── src.models (no deps on src)       │
  │   └── external: pydantic            │
  │                                     │
  └── src.tones                         │
      └── src.models                    │
```

No circular dependencies. `models.py` is the root — everything depends on it.
`tones.py` depends only on models. `roaster.py` depends on models + tones.
`card.py` depends only on models. `main.py` depends on all four.

---

## Data flow (end-to-end)

```
User input / Example Group
  │
  ▼
GroupPhoto(title, people=[Person, ...])
  │
  ├── Tone(name, intensity, vibe, ...)
  │
  ▼
Roaster.generate_roasts(group, tone)
  │
  ├── For each Person:
  │     pick targets (expression, vibe, outfit, etc.)
  │     pull template lines from _SIMULATED_ROASTS[tone][target]
  │     assemble Roast(person, lines, insult, verdict)
  │
  ├── _group_roast: one-liner about the group
  │
  └── _make_footer: tone-specific closing
  │
  ▼
RoastCard(title, tone, group, roasts, group_roast, footer)
  │
  ▼
format_card(card) → formatted text block
  │
  ├── Card header: title, tone, vibes
  ├── Group roast section
  ├── Per-person roasts with emoji labels
  └── Footer + timestamp
  │
  ▼
Printed to terminal / saved to file
```

---

## Test execution flow

```
pytest tests/
  │
  ├── conftest.py
  │     ├── family_group fixture → 3 Person objects
  │     ├── coworkers_group fixture → 3 Person objects
  │     └── all_tones fixture → all Tone objects from TONE_MAP
  │
  ├── TestTones
  │     ├── test_builtin_tones_have_minimum_count  (≥4)
  │     ├── test_each_tone_has_all_fields
  │     └── test_tone_map_has_all_tones
  │
  ├── TestRoaster
  │     ├── test_generate_roasts_returns_card       (RoastCard type)
  │     ├── test_each_person_gets_a_roast            (1:1)
  │     ├── test_roast_has_insult_and_verdict        (mandatory fields)
  │     ├── test_group_roast_is_present
  │     ├── test_all_tones_produce_output            (all 5 tones)
  │     └── test_set_client_toggles_live_flag
  │
  ├── TestCard
  │     ├── test_format_card_returns_string
  │     ├── test_format_card_includes_group_name
  │     ├── test_format_card_includes_roast_lines
  │     └── test_format_card_writes_to_file
  │
  ├── TestGroups
  │     ├── test_family_group_has_people
  │     └── test_coworkers_group_has_people
  │
  └── TestIntegration
        ├── test_full_pipeline_with_siblings_tone
        ├── test_full_pipeline_with_merciless_tone
        └── test_empty_group_returns_empty_card
```