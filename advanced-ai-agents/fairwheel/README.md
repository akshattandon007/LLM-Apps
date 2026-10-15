# FairWheel

**FairWheel — Car-Purchase Advisory Team.** Type in a make/model/year plus your budget and commute, and a crew of specialist agents returns a one-page buying report: real NHTSA crash ratings, trending complaint themes with counts, open recalls (a dealer must fix these free), 5-year fuel cost, and a final **WORTH IT / WAIT / AVOID** verdict with negotiation talking points.

Zero API keys, zero signup. All data from free federal APIs (NHTSA + fueleconomy.gov).

## Features

- **Multi-agent orchestration** — 5 specialist agents (Safety Scorer, Grievance Scout, Recall Auditor, Cost Analyst, Deal Reviewer) coordinated by an orchestrator.
- **Real data, no keys** — NHTSA SafetyRatings (crash stars), NHTSA complaints, NHTSA recalls, fueleconomy.gov MPG.
- **Deterministic verdict** — weighted scoring with hard safety gates; the Deal Reviewer explains *why*.
- **Negotiation talking points** — open recalls are free-fix leverage; complaint clusters become dealer questions.
- **Demo mode** — if an API fails, that agent falls back to plausible simulated data and marks it `simulated`, so the pipeline always produces output.
- **CLI + file output** — one-page markdown report to stdout or `--output report.md`.

## Quick start

```bash
pip install -r requirements.txt
python -m fairwheel --year 2021 --make Honda --model Accord --budget 25000 --annual-miles 12000
```

Or interactive:

```bash
python -m fairwheel
```

Add `--fuel-price 3.80` to override the default $3.50/gal, and `--demo` to force simulated data (no network).

## What you get

A buying report with:
1. Safety score (NHTSA 5-star crash ratings, front + side)
2. Top complaint themes with real complaint counts
3. Open recalls — campaign numbers, what's wrong, the free fix
4. 5-year fuel cost from real combined MPG
5. Verdict: **WORTH IT / WAIT / AVOID** + reasons + negotiation talking points

## Project layout

```
fairwheel/
├── fairwheel/
│   ├── __main__.py        # python -m fairwheel entry
│   ├── cli.py             # argument parsing + report rendering
│   ├── models.py          # dataclasses shared across agents
│   ├── api.py             # httpx client wrapper + set_client for tests
│   ├── orchestrator.py    # coordination: run all agents → deal reviewer
│   ├── report.py          # markdown report builder
│   └── agents/
│       ├── safety_scorer.py    # NHTSA crash ratings
│       ├── grievance_scout.py  # NHTSA complaints → themes
│       ├── recall_auditor.py   # NHTSA recalls
│       ├── cost_analyst.py     # fueleconomy.gov MPG + fuel math
│       └── deal_reviewer.py    # critic: verdict + talking points
├── tests/
│   └── test_fairwheel.py
├── Decisions.md
├── Flow.md
└── requirements.txt
```

## Notes

- A dealer must fix open recalls **free of charge** — the report uses this as leverage, not as a hard reject.
- Fuel math: `annual_miles / combined_mpg * fuel_price * 5` for a 5-year horizon.
- The Deal Reviewer is deterministic: safety 40%, complaints 30%, recalls 20%, cost 10%, with hard safety gates (rating < 3 → never WORTH IT).