# Flow.md — LearnerLane

## Execution flow, call chains, and module dependency graph.

---

## Entry Point

```
python -m learnerlane [topic] [--demo] [--level] [--time] [--goal]
                │
                ▼
         learnerlane/__main__.py
         main()
           │
           ├── args.demo == True  ──► run 3 demo curricula
           │                              (photography, guitar, python)
           │
           ├── args.topic given   ──► run_pipeline(topic=args.topic, ...)
           │
           └── interactive mode   ──► input() → run_pipeline(...)
```

---

## Pipeline: `run_pipeline()` (orchestrator.py)

```
run_pipeline(topic, level, time_per_week, goal, mode)
  │
  ├── [Stage 1] SKILL ASSESSMENT
  │   │
  │   ├── IF goal given AND no topic:
  │   │   └── parse_goal_freeform(goal)          ← skill_assessor.py
  │   │       ├── Regex: extract level hints
  │   │       ├── Regex: extract topic from "I want to learn X"
  │   │       └── Returns: SkillProfile
  │   │
  │   └── ELSE:
  │       └── assess_skill(topic, level, time, goal)  ← skill_assessor.py
  │           ├── Normalize level string → "beginner"|"dabbler"|"intermediate"
  │           ├── Normalize time string → one of 4 TIME_BUCKETS
  │           └── Returns: SkillProfile
  │
  ├── [Stage 2] CURRICULUM DESIGN
  │   │
  │   └── build_curriculum(profile)               ← curriculum_builder.py
  │       ├── Match profile.topic → CURRICULUM_TEMPLATES keys
  │       │   ├── Exact match? → use template
  │       │   ├── Partial match (50%+ word overlap)? → use template
  │       │   └── No match? → use GENERIC_MODULES
  │       ├── Adjust module count by level + time
  │       ├── Build Module dataclasses (week, title, goal, topics, hours)
  │       └── Returns: Curriculum
  │
  ├── [Stage 3] RESOURCE HUNTING
  │   │
  │   └── For EACH module in curriculum.modules:
  │       └── hunt_resources(module, topic)        ← resource_hunter.py
  │           ├── search_wikipedia(query, limit=2)  ← Wikipedia API (free, no auth)
  │           ├── search_open_library(query, limit=2) ← Open Library API (free, no auth)
  │           ├── search_web_fallback(query)         ← URL generation (no network)
  │           │   ├── YouTube search URL
  │           │   └── Google search URL
  │           ├── Deduplicate by URL
  │           └── Returns: ModuleResources (list of Resource)
  │
  └── [Stage 4] PRACTICE PLANNING
      │
      └── generate_plan(curriculum, profile)      ← practice_planner.py
          ├── Match profile.topic → PRACTICE_TEMPLATES keys
          │   ├── Exact/partial match? → use template
          │   └── No match? → use GENERIC practice tasks
          ├── Map practice tasks → modules by index
          │   ├── index < len(template) → use template[i]
          │   └── index >= len(template) → wrap around: template[i % len]
          └── Returns: PracticePlan (list of PracticeTask)
```

---

## Module Dependency Graph

```
learnerlane/
├── __main__.py          ← entry point (no deps)
├── orchestrator.py      ← depends on: agents/*
│   │
│   ├── agents/
│   │   ├── skill_assessor.py     ← standalone (stdlib only: re, dataclasses)
│   │   ├── curriculum_builder.py ← depends on: skill_assessor (SkillProfile)
│   │   ├── resource_hunter.py    ← depends on: curriculum_builder (Module)
│   │   │                         ← external: httpx (Wikipedia, Open Library APIs)
│   │   └── practice_planner.py   ← depends on: curriculum_builder (Curriculum, Module)
│   │                            ← depends on: skill_assessor (SkillProfile)
│   │
│   └── (no other internal deps)
│
tests/
└── test_learnerlane.py   ← depends on: all agent modules + orchestrator
```

**Dependency direction:** `__main__` → `orchestrator` → `agents/*` (leaf modules have no inter-agent deps except those listed).

---

## Data Flow

```
User Input (string)
    │
    ▼
╔══════════════════════════════════════╗
║         SkillProfile                  ║
║  ┌──────────────────────────────────┐║
║  │ topic: "photography"            │║
║  │ level: "beginner"               │║
║  │ time_per_week: "1-3 hours/week" │║
║  │ goal: "Learn photography"       │║
║  └──────────────────────────────────┘║
╚══════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════╗
║           Curriculum                  ║
║  ┌──────────────────────────────────┐║
║  │ modules: [                      │║
║  │   Module(week=1, "Your Camera"), │║
║  │   Module(week=2, "Composition"), │║
║  │   Module(week=3, "Genres"),      │║
║  │   Module(week=4, "Editing"),     │║
║  │   Module(week=5, "Portfolio")   │║
║  │ ]                               │║
║  └──────────────────────────────────┘║
╚══════════════════════════════════════╝
    │
    ▼  (per module)
╔══════════════════════════════════════╗
║       ModuleResources[]              ║
║  ┌──────────────────────────────────┐║
║  │ module_title: "Your Camera"     │║
║  │ resources: [                    │║
║  │   Resource(source="wikipedia"), │║
║  │   Resource(source="openlibrary"),│║
║  │   Resource(source="web"),        │║
║  │ ]                               │║
║  └──────────────────────────────────┘║
╚══════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════╗
║          PracticePlan                ║
║  ┌──────────────────────────────────┐║
║  │ tasks: [                        │║
║  │   PracticeTask(week=1, ✏️),    │║
║  │   PracticeTask(week=2, ✏️),    │║
║  │   PracticeTask(week=3, ✏️),    │║
║  │   PracticeTask(week=4, 📷),    │║
║  │   PracticeTask(week=5, 🔨)     │║
║  │ ]                               │║
║  └──────────────────────────────────┘║
╚══════════════════════════════════════╝
    │
    ▼
╔══════════════════════════════════════╗
║         CompletePlan                 ║
║  (profile + curriculum + resources   ║
║   + practice)                        ║
║         │                            ║
║         ▼                            ║
║   format_plan() → Rich text output   ║
╚══════════════════════════════════════╝
    │
    ▼
  STDOUT (terminal)
```

---

## Key Execution Paths

### Path A: `--demo` flag
```
main()
  → args.demo == True
  → for topic in [photography, guitar, python]:
      → run_pipeline(topic, mode="simulated")
      → format_plan(plan)
      → print()
  → exit
```
No user input required. Shows 3 complete curricula back-to-back.

### Path B: Topic specified
```
main()
  → args.topic = "photography"
  → run_pipeline(topic="photography", level="beginner", time="1-3 hours/week")
  → format_plan(plan)
  → print()
  → exit
```
Quick mode. One topic, default level & time.

### Path C: Interactive mode
```
main()
  → no args
  → input("What skill? ")
  → topic = "photography"
  → run_pipeline(topic, level, time, goal)
  → format_plan(plan)
  → print()
  → exit
```
Prompts user for topic, runs pipeline, prints plan.

---

## Error Handling

| Failure Point | Handling | User Sees |
|---|---|---|
| Empty/blank topic | `ValueError` raised | "No valid topic provided" |
| Wikipedia API down | `except Exception` → empty list | No Wikipedia resources that module |
| Open Library API down | `except Exception` → empty list | No Open Library resources that module |
| All APIs down | Web fallback still generates URLs | YouTube + Google search links only |
| Practice planner fails | `except Exception` → empty PracticePlan | No practice tasks |
| Module index > practice templates | Wrap-around: `i % len(template)` | Repurposed practice tasks |