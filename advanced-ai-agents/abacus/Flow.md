# Flow — abacus

## Execution flow

```
User CLI command
       │
       ▼
__main__.py::main()
  ├── build_profile(args)          # Parse CLI args → FinancialProfile
  │   ├── IncomeAgent.parse_income_line()   # For each income string
  │   └── ExpenseAgent.parse_expense_line() # For each expense string
  ├── build_goal(args)            # Parse goal args → Goal
  │
  ▼
Supervisor.run(profile, goal, what_if)
  │
  ├── [Round 1] IncomeAgent.process()
  │   └── Logs: streams × amounts, net/monthly breakdown
  │
  ├── [Round 2] ExpenseAgent.process()
  │   └── Logs: total expenses, essential/discretionary split, surplus
  │
  ├── [Round 3] ScenarioEngine.project()
  │   └── 5-year projection (no LLM)
  │       ├── _apply_adjustments()        # Copy profile, apply what-if deltas
  │       ├── _debt_payment()             # Standard amortization formula
  │       ├── Month-by-month loop:
  │       │   ├── Add surplus to savings
  │       │   ├── Yearly compound interest (4% APY)
  │       │   └── Annual debt snowball payment
  │       ├── _assess_risk()               # low/medium/high
  │       └── _generate_summary()          # Human-readable string
  │       └── → ScenarioResult
  │
  ├── [Round 4] GoalTracker.process()
  │   └── Compares surplus vs monthly_needed → feasible bool
  │
  ├── [Round 5] Supervisor._suggest_scenarios()
  │   ├── _parse_what_if()                 # Regex-based (if user provided)
  │   └── Or default: save_more, debt_paydown, cut_expenses
  │   └── For each: ScenarioEngine.project() → ScenarioResult
  │
  └── [Round 6] Supervisor._synthesize()
      ├── Finds best scenario (max savings)
      ├── Determines recommendation
      └── → dict (full report)
            │
            ▼
      __main__.py: prints formatted report
        ├── Profile summary
        ├── Goal status
        ├── Baseline projection
        ├── Scenario comparisons
        └── Recommendation + planner message
```

## Agent communication

```
                      Supervisor
                     /    |     \
                    /     |      \
              ┌─────┐ ┌─────┐ ┌──────┐
              │ IA  │ │ EA  │ │  SE  │
              └─────┘ └─────┘ └──────┘
              Income   Expense  Scenario
              Agent    Agent    Engine
                 \       |       /
                  \      |      /
                ┌───────────────┐
                │ Goal Tracker │
                └───────────────┘
                       │
                       ▼
                ┌───────────────┐
                │  Supervisor   │
                │  Synthesis    │
                └───────────────┘
```

**IA** = IncomeAgent — sends enriched profile to Supervisor
**EA** = ExpenseAgent — sends categorized expenses to Supervisor
**SE** = ScenarioEngine — computes projections, returns ScenarioResult
**GT** = GoalTracker — checks feasibility, returns tracking dict

All communication uses typed dataclasses from `models.py`. No raw dicts pass between agents.

## Module dependency graph

```
__main__.py
  ├── models.py              # Dataclasses enums, FinancialEncoder
  ├── agents/supervisor.py    # Supervisor (orchestrator)
  │   ├── agents/income_agent.py
  │   ├── agents/expense_agent.py
  │   ├── agents/scenario_engine.py
  │   ├── agents/goal_tracker.py
  │   └── llm.py              # LLM helper (optional, for what-if NL parsing)
  ├── agents/__init__.py
  └── tests/test_abacus.py
      ├── models.py
      ├── agents/income_agent.py
      ├── agents/expense_agent.py
      ├── agents/scenario_engine.py
      └── agents/goal_tracker.py
```

## Data flow diagram

```
CLI args / interactive input
       │
       ▼
  ┌──────────────┐
  │ FinancialProfile │  ◄── IncomeStream[], Expense[], savings, debt, age
  └──────────────┘
       │
       ▼
  ┌────────────────┐
  │   Supervisor   │
  │   .run()        │
  └────────────────┘
       │
       ├─► IncomeAgent    → profile (enriched)
       ├─► ExpenseAgent   → profile (enriched)
       ├─► ScenarioEngine → ScenarioResult (savings_5y, goal_met, risk, summary)
       ├─► GoalTracker    → tracking dict (feasible, monthly_needed, gap)
       └─► Synthesis      → report dict (json-serializable)
                                │
                                ▼
                        Formatted CLI output / --json
```

## Key call chains

**Income parsing:** `IncomeAgent.parse_income_line(text)` → `IncomeStream(amount, type, tax_rate)` → added to `FinancialProfile.income_streams`

**Expense parsing:** `ExpenseAgent.parse_expense_line(text)` → `Expense(amount, category, essential)` → added to `FinancialProfile.expenses`

**Financial projection:** `ScenarioEngine.project(profile, goal, years, adjustments)` → `_apply_adjustments()` → `_debt_payment()` → monthly loop → `_assess_risk()` → `_generate_summary()` → `ScenarioResult`

**What-if parsing:** `Supervisor._parse_what_if(query)` → regex keyword matching → `{income_boost, cut_expenses, save_more, debt_paydown}` → passed to `ScenarioEngine.project(adjustments={...})`

**Report synthesis:** `Supervisor._synthesize(results, tracking, goal)` → `max(results, key=lambda r: r.total_savings_5y)` → `_planner_message(baseline, best)` → final report dict