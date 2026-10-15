# FairWheel — Flow

Execution trace and module dependency graph for the FairWheel car-purchase advisory team.

## Entry point

```
python -m fairwheel                              -> fairwheel/__main__.py
   └─ raise SystemExit(main())                   -> fairwheel/cli.py::main
        ├─ parse_args(argv)                      -> argparse: --year --make --model --budget
        │                                          --annual-miles --fuel-price --family-size
        │                                          --commute-miles --demo --output
        ├─ [interactive fallback] input()        -> prompts for year/make/model when flags missing
        ├─ VehicleQuery(...)                     -> fairwheel/models.py::VehicleQuery (dataclass)
        ├─ run_pipeline(query, demo)             -> fairwheel/orchestrator.py::run_pipeline
        │     ├─ (demo) safety_scorer._simulate / grievance_scout._simulate /
        │     │          recall_auditor._simulate / cost_analyst._simulate
        │     └─ (live)  safety_scorer.run(query)
        │               grievance_scout.run(query)
        │               recall_auditor.run(query)
        │               cost_analyst.run(query)
        │     └─ deal_reviewer.run(query, safety, complaints, recalls, cost)
        │                                        -> fairwheel/agents/deal_reviewer.py::run
        │     └─ FairWheelReport(...)            -> fairwheel/models.py::FairWheelReport
        ├─ render_markdown(report)               -> fairwheel/report.py::render_markdown
        └─ [--output] open(path).write(md)       -> writes report file; else print(md)
```

## Execution paths

### Path 1 — Live research (default)
```
cli.main
  └─ orchestrator.run_pipeline(demo=False)
       ├─ safety_scorer.run(query)
       │    ├─ api.get_json(SafetyRatings/modelyear/{y}/make/{m}/model/{mo})
       │    │    -> results[0].VehicleId  (+ VehicleDescription)
       │    ├─ api.get_json(SafetyRatings/VehicleId/{id}?format=json)
       │    │    -> OverallRating, OverallFrontCrashRating, OverallSideCrashRating
       │    └─ SafetyReport(...)  [source="live"]
       ├─ grievance_scout.run(query)
       │    ├─ api.get_json(complaints/complaintsByVehicle?make&model&modelYear)
       │    ├─ Counter over item["components"].split(",")   (cap 400 items)
       │    ├─ samples[comp] = first summary per component
       │    └─ ComplaintReport(total, clusters=top 6, source="live")
       ├─ recall_auditor.run(query)
       │    ├─ api.get_json(recalls/recallsByVehicle?make&model&modelYear)
       │    ├─ [RecallItem(campaign, component, summary, consequence, remedy)] per result
       │    └─ RecallReport(recalls, source="live")
       ├─ cost_analyst.run(query)
       │    ├─ api.get_text(menu/options?year&make&model)        [XML]
       │    ├─ ElementTree iterate <menuItem> -> first <value> = vehicle_id
       │    ├─ api.get_text(vehicle/{vehicle_id})                [XML]
       │    ├─ _parse_mpg -> {city08, highway08, comb08}
       │    ├─ CostReport(...); compute_fuel_costs(annual_miles, fuel_price)
       │    └─ CostReport(combined_mpg, city, hwy, annual, five_year, source="live")
       └─ deal_reviewer.run(query, safety, complaints, recalls, cost)
            ├─ _safety_score     = overall_rating / 5 * 100
            ├─ _complaint_score  = max(0, 100 - total*0.15 - critical_hits*5)
            ├─ _recall_score     = max(0, 100 - count*12)
            ├─ _cost_score       = 100 if 5yr fuel <= $8,400 else scaled down
            ├─ total = Σ(weight * score)   weights: safety .40, complaints .30, recalls .20, cost .10
            ├─ hard gate: overall_rating < 3  -> AVOID
            ├─ else: >=80 WORTH IT | >=55 WAIT | else AVOID
            └─ DealVerdict(verdict, score, reasons, talking_points, scores_by_factor)
```

### Path 2 — Demo / fallback (per-agent)
```
Any agent: HTTPError (non-200, connect fail, bad JSON/XML)
  └─ <agent>._simulate(query, error)
       ├─ seed = sha256(make+model) -> deterministic pseudo-data
       └─ Report(source="simulated", error=...)
Pipeline continues; render_markdown appends "⚠️ Simulated data" note per flagged section.
```

### Path 3 — Report output
```
render_markdown(report)
  ├─ header + verdict line (emoji by verdict)
  ├─ Safety section        (NHTSA stars / simulated note)
  ├─ Complaints section    (total + top 5 themes with counts)
  ├─ Recalls section       (count + up to 4 campaign lines)
  ├─ Fuel section          (combined/city/hwy mpg + 5-yr cost)
  ├─ Why (reasons)
  ├─ Negotiation talking points (numbered)
  └─ provenance footer if any source == "simulated"
```

## Module dependency graph

```
fairwheel/
├── __main__.py ──────────► cli.py
├── cli.py ───────────────► orchestrator.py, models.py, report.py
├── orchestrator.py ──────► agents/{safety_scorer, grievance_scout, recall_auditor, cost_analyst, deal_reviewer}.py
│                            └──► api.py, models.py
├── agents/deal_reviewer.py ──► models.py
├── report.py ────────────► models.py
├── models.py              (no deps — pure dataclasses)
└── api.py                 ──► httpx (only external runtime dep)
```

## Key data flow

```
User input ──► VehicleQuery ──► [Safety Scorer] ──► SafetyReport   ┐
 (year/make/    (budget,        [Grievance Scout]─► ComplaintReport ├─► Deal Reviewer ─► DealVerdict ─► Markdown report
  model/...)     miles, price)  [Recall Auditor] ─► RecallReport    │     (critic: weighted score
                                [Cost Analyst]  ─► CostReport      ┘      + hard gates + talking points)
```

## Test coverage map

| Test | Path exercised |
|------|----------------|
| `test_safety_scorer_live` | Path 1 safety (MockTransport JSON) |
| `test_safety_scorer_fallback_on_error` | Path 2 safety |
| `test_grievance_scout_live_clusters` | Path 1 complaints clustering |
| `test_recall_auditor_live` | Path 1 recalls |
| `test_cost_analyst_live_xml` | Path 1 fuel (XML parse + fuel math) |
| `test_cost_analyst_fallback_on_bad_xml` | Path 2 cost |
| `test_deal_reviewer_worth_it` | Path 1 verdict (WORTH IT) |
| `test_deal_reviewer_hard_gate_avoid` | Path 1 hard gate (AVOID) |
| `test_deal_reviewer_recall_leverage` | Path 1 talking points |
| `test_pipeline_demo_produces_full_report` | Path 2 full pipeline + render |
| `test_pipeline_live_with_mock_routes` | Path 1 full pipeline hermetic |
| `test_cli_demo_writes_output` | Path 3 CLI → file |