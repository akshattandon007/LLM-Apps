# Flow — HealthGuard

## Execution Trace

### Command: `python main.py check --drugs warfarin aspirin --symptoms "chest pain"`

```
main.py:check()
  │
  ├── Agent 1: Drug Interaction Checker
  │   └── check_all_interactions(["warfarin", "aspirin"])
  │       └── check_interaction("warfarin", "aspirin")
  │           ├── normalize_drug_name("warfarin") → "warfarin"
  │           ├── normalize_drug_name("aspirin") → "aspirin"
  │           ├── KNOWN_INTERACTIONS scan → match found
  │           │   └── severity="high", description="...", management="..."
  │           └── return InteractionResult(interaction_found=True, severity=Severity.HIGH)
  │
  ├── Agent 2: Symptom Triage
  │   └── assess_multiple_symptoms(["chest pain"])
  │       └── assess_symptom("chest pain")
  │           ├── KNOWN_SYMPTOMS["chest pain"] → match
  │           │   ├── conditions=["heart attack","angina","costochondritis"]
  │           │   ├── urgency="emergency"
  │           │   ├── recommendations=["Call 911","Don't drive",...]
  │           │   └── immediate=True
  │           └── return SymptomAssessment(requires_immediate_care=True, urgency=Urgency.EMERGENCY)
  │
  ├── Agent 3: Condition Researcher
  │   └── search_multiple_conditions(["heart attack", "angina"])
  │       ├── search_condition("heart attack")
  │       │   ├── CONDITION_DB scan → no exact match
  │       │   ├── _search_medlineplus("heart attack") → HTTP GET MedlinePlus API
  │       │   └── return ConditionInfo(source="medlineplus")
  │       └── search_condition("angina")
  │           └── return ConditionInfo(source="simulated", description="No detailed info")
  │
  └── Agent 4: Report Compiler
      └── compile_report(interactions, symptoms, conditions)
          ├── Collect key_warnings:
          │   ├── "⚠️ SEVERE interaction: warfarin + aspirin — ..."
          │   └── "🚨 IMMEDIATE CARE NEEDED: chest pain — Call 911..."
          ├── Collect recommendations from all agents
          ├── Build summary string
          └── return HealthReport(summary, key_warnings, recommendations, drug_interactions, ...)
```

### Command: `python main.py condition hypertension`

```
main.py:condition()
  └── search_multiple_conditions(["hypertension"])
      └── search_condition("hypertension")
          ├── CONDITION_DB["hypertension"] → match
          │   ├── description="High blood pressure..."
          │   ├── symptoms=["No symptoms (silent)", "Headaches", ...]
          │   ├── treatments=["ACE inhibitors", "Diuretics", ...]
          │   └── prevention_tips=["Reduce sodium", "Exercise", ...]
          └── return ConditionInfo(source="known-db")
```

### Command: `python main.py` (interactive mode)

```
main.py:main()
  └── interactive()
      └── while True:
          ├── console.input("healthguard> ") → "aspirin, ibuprofen, headache"
          ├── Split by comma → ["aspirin", "ibuprofen", "headache"]
          ├── Heuristic: drug or symptom?
          │   ├── "aspirin" → drug (no symptom keyword match)
          │   ├── "ibuprofen" → drug (no symptom keyword match)
          │   └── "headache" → symptom (matches symptom_keywords)
          └── check(drugs=["aspirin", "ibuprofen"], symptoms=["headache"])
              └── (same flow as `check` subcommand above)
```

## Module Dependency Graph

```
main.py
  ├── agents/drug_checker.py
  │     └── models.py (DrugInfo, InteractionResult, Severity)
  ├── agents/symptom_triage.py
  │     └── models.py (SymptomAssessment, Urgency)
  ├── agents/condition_researcher.py
  │     ├── models.py (ConditionInfo)
  │     └── httpx (MedlinePlus API calls)
  └── agents/report_compiler.py
        ├── models.py (HealthReport, InteractionResult, SymptomAssessment, ConditionInfo)
        └── all agent outputs → compiled HealthReport
```

## Data Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    main.py (Orchestrator)                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Drug Checker  │  │ Symptom      │  │ Condition      │ │
│  │ Agent 1      │  │ Triage       │  │ Researcher     │ │
│  │              │  │ Agent 2      │  │ Agent 3        │ │
│  │ OpenFDA API  │  │ Curated DB   │  │ MedlinePlus    │ │
│  │ + Curated DB │  │ + Heuristics │  │ + Curated DB   │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘ │
│         └─────────────────┼──────────────────┘          │
│                           ▼                            │
│                   ┌──────────────┐                     │
│                   │ Report       │                     │
│                   │ Compiler     │                     │
│                   │ Agent 4      │                     │
│                   │              │                     │
│                   │ Warnings     │                     │
│                   │ Summary      │                     │
│                   │ Recommendations│                   │
│                   └──────┬───────┘                     │
└──────────────────────────┼──────────────────────────────┘
                           ▼
                 Terminal Output
                 (Rich Table + Panel + Markdown)
```

## Key Execution Paths

| Path | Entry | Agents Used | Data Source |
|------|-------|-------------|-------------|
| Drug check only | `check --drugs X Y` | 1, 4 | Curated DB + OpenFDA |
| Symptom only | `symptom "chest pain"` | 2, 3, 4 | Curated DB + MedlinePlus |
| Full pipeline | `check --drugs X --symptoms Y` | 1, 2, 3, 4 | All sources |
| Condition research | `condition hypertension` | 3, 4 | Curated DB + MedlinePlus |
| Drug info lookup | `info --drugs lisinopril` | 1 | RxNorm API + OpenFDA |
| Interactive | `main.py` | All (dynamic) | All sources |