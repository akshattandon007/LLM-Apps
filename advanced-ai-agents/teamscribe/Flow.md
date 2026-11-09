# Flow.md — TeamScribe

## Execution Trace

### Main Path: `python -m teamscribe process` (CLI)

```
__main__.py
  └── cli.main()
       ├── argparse: parse "process" subcommand, extract title, notes, participants, date
       │
       ├── build_record_from_args()
       │    └── creates MeetingRecord(title, date, participants, raw_notes)
       │
       ├── Orchestrator(model, archive_path)
       │    └── initializes 4 agents:
       │         ├── Transcriber(model)
       │         ├── MinuteTaker(model)
       │         ├── Scribe(model)
       │         └── Archivist(archive_path, model)
       │
       ├── orchestrator.run(record)
       │    │
       │    ├── [AGENT 1] Transcriber.process(record)
       │    │    ├── calls BaseAgent.call_llm(system_prompt, user_prompt)
       │    │    │    └── openai.ChatCompletion.create(model, messages)
       │    │    └── writes record.cleaned_notes = LLM response
       │    │
       │    ├── [AGENT 2] MinuteTaker.process(record)
       │    │    ├── calls BaseAgent.call_llm() → returns JSON
       │    │    ├── json.loads() parses decisions, action_items, key_points
       │    │    │    └── fallback: re.search() for { } block
       │    │    └── writes:
       │    │         ├── record.decisions = [Decision(...), ...]
       │    │         ├── record.action_items = [ActionItem(...), ...]
       │    │         └── record.key_points = [str, ...]
       │    │
       │    ├── [AGENT 3] Scribe.process(record)
       │    │    ├── Scribe._generate_summary(record)
       │    │    │    └── call_llm() with cleaned_notes + decisions + actions
       │    │    │    └── writes record.summary
       │    │    └── Scribe._generate_email(record)
       │    │         └── call_llm() with same context
       │    │         └── writes record.follow_up_email
       │    │
       │    └── [AGENT 4] Archivist.process(record)
       │         ├── load_archive() → reads ~/.teamscribe/archive.json
       │         ├── appends current meeting's decisions + summary to archive
       │         ├── if > 1 meeting: _detect_trends(archive)
       │         │    └── call_llm() with last 5 meetings as context
       │         └── save_archive() → writes updated archive.json
       │
       ├── Storage.save(record)
       │    ├── generates filename: {date}--{sanitized_title}.json
       │    └── writes MeetingRecord.to_json() to ~/.teamscribe/meetings/
       │
       └── prints summary, action items, file path
```

### Secondary Path: `python -m teamscribe list`

```
__main__.py → cli.main()
  └── Storage.list_meetings()
       └── glob("*.json") in output_dir
            ├── json.loads() each file → extract title, date, counts
            └── return sorted list (newest first)
```

### Secondary Path: `python -m teamscribe show <path>`

```
__main__.py → cli.main()
  └── Storage.load(path)
       ├── Path(path).read_text()
       ├── json.loads() → dict
       └── MeetingRecord.from_dict() → MeetingRecord
            └── print record.to_json()
```

---

## Module Dependency Graph

```
teamscribe/
│
├── __main__.py          → cli
├── cli.py               → argparse, orchestrator, storage, models
├── orchestrator.py      → models, agents.*
├── storage.py           → models
├── models.py            ← (no deps — dataclasses + json)
├── agent_base.py        → openai
│
├── agents/
│   ├── __init__.py      → re-exports Transcriber, MinuteTaker, Scribe, Archivist
│   ├── transcriber.py   → agent_base, models
│   ├── minute_taker.py  → agent_base, models
│   ├── scribe.py        → agent_base, models
│   └── archivist.py     → agent_base, models, json, pathlib
│
tests/
├── test_models.py       → models
├── test_agents.py       → models, agents.* (mock openai)
└── test_orchestrator.py → models, orchestrator, storage
```

---

## Data Flow

```
User Input (raw notes + metadata)
         │
         ▼
┌──────────────────────────────────────────────────┐
│              MeetingRecord                        │
│  title, date, participants, raw_notes            │
└───────┬──────────────────────────────────────────┘
        │
        ▼ [Transcriber]
┌──────────────────────────────────────────────────┐
│  MeetingRecord.cleaned_notes = structured text   │
└───────┬──────────────────────────────────────────┘
        │
        ▼ [MinuteTaker]
┌──────────────────────────────────────────────────┐
│  MeetingRecord.decisions      → [Decision]       │
│  MeetingRecord.action_items   → [ActionItem]     │
│  MeetingRecord.key_points     → [str]            │
└───────┬──────────────────────────────────────────┘
        │
        ▼ [Scribe]
┌──────────────────────────────────────────────────┐
│  MeetingRecord.summary         = prose summary   │
│  MeetingRecord.follow_up_email = email text      │
└───────┬──────────────────────────────────────────┘
        │
        ▼ [Archivist]
┌──────────────────────────────────────────────────┐
│  Archive file (archive.json)                     │
│  └── meetings: [{title, date, summary}, ...]    │
│  └── decisions: [{meeting, topic, outcome}, ...]│
│  └── trends: [str]                              │
└───────┬──────────────────────────────────────────┘
        │
        ▼ [Storage]
┌──────────────────────────────────────────────────┐
│  JSON file on disk                               │
│  ~/.teamscribe/meetings/{date}--{title}.json    │
│  └── Full MeetingRecord serialized to JSON       │
└──────────────────────────────────────────────────┘
        │
        ▼ Output to User
     Summary, action items, decisions, email, file path
```