# Flow.md — DebtSlayer Execution Flow

## Entry Point

```
__main__.py  main()
     │
     ├── cmd_analyze(args)
     │       Argument parsing: --debt, --income, --expenses
     │
     ├── cmd_letter(args)
     │       --creditor, --balance, --apr, --hardship
     │
     └── cmd_progress(args)
             --plan (path to saved JSON)
```

## Primary Execution Path (cmd_analyze)

### Phase 1: Data Loading

```
cmd_analyze()
  └─ parse_debt_spec(raw: str) -> dict
       Parse "Label:Balance:APR:MinPayment" into {"label","balance","apr","min_payment"}
       
  └─ DebtSlayerCoordinator.__init__()
       ├─ CreditorAgent()        → empty debt list
       ├─ SpendingAgent()        → empty profile (income=0, expenses=0)
       ├─ StrategyAgent()        → stateless strategy (no init data)
       ├─ LetterAgent()          → static templates (no API key by default)
       └─ ProgressAgent()        → static stateless methods
       
  └─ coordinator.load_debts(specs)
       │
       └─ CreditorAgent.add_debt(label, balance, apr, min_payment)
            Creates Debt model, appends to internal list
            Returns Debt for confirmation
       
  └─ coordinator.set_budget(income, expenses)
       │
       └─ SpendingAgent.set_profile(income, expenses)
            Creates SpendingProfile(income, expenses)
```

### Phase 2: Analysis Pipeline

```
coordinator.run_full_analysis()
    │
    ├── CreditorAgent.total_balance()
    │    sum(d.balance for d in self.debts) → float
    │
    ├── CreditorAgent.total_min_payments()
    │    sum(d.min_payment for d in self.debts) → float
    │
    ├── SpendingAgent.analyze()
    │    Returns {
    │        "monthly_income":       income,
    │        "monthly_expenses":     expenses,
    │        "monthly_surplus":      max(0, income - expenses),
    │        "deficit":              income < expenses,
    │        "savings_rate_pct":     surplus / income * 100
    │    }
    │
    ├── SpendingAgent.suggestions()
    │    Rule-of-thumb tips based on expense/income ratio
    │    Returns list[str]
    │
    ├── StrategyAgent.compare_strategies(debts, surplus)
    │    │
    │    ├── compute_plan(debts, surplus, "avalanche")
    │    │    Sorts debts by APR desc, simulates month-by-month
    │    │    Returns PayoffPlan {months_to_payoff, total_interest, schedule[]}
    │    │
    │    ├── compute_plan(debts, surplus, "snowball")
    │    │    Sorts debts by balance asc, same simulator
    │    │    Returns PayoffPlan
    │    │
    │    └── Compare total_interest → pick recommendation
    │        Returns {
    │            "recommendation": "avalanche"|"snowball"|"none",
    │            "reason": str,
    │            "avalanche": {"months": N, "total_interest": $},
    │            "snowball": {"months": N, "total_interest": $}
    │        }
    │
    ├── StrategyAgent.compute_plan(debts, surplus, recommended_method)
    │    [Same simulator, with recommended method]
    │    Returns PayoffPlan (full schedule)
    │
    ├── LetterAgent.draft_letter(creditor, balance, apr, hardship)
    │    │
    │    └── _template_letter(creditor, balance, apr, hardship)
    │         ├── Keyword matching (reduced hours / medical / job loss / general)
    │         ├── Template selection
    │         └── Fill template with actual values
    │    → Returns CreditorLetter (creates .to_text() for print)
    │
    └── StrategyAgent.compute_plan(debts, 0.0, "avalanche")
         [Minimum-only simulation]
         If months_to_payoff < 1200 → compare total interest
         Else → "N/A (minimums don't cover interest)"
         
    Returns {
        "inventory": {
            "debts": [{label, balance, apr, min_payment}],
            "total_balance": $,
            "total_min_payments": $
        },
        "spending": {surplus analysis},
        "savings_tips": [...],
        "strategy_comparison": {...},
        "recommended_plan": PayoffPlan.to_json(),
        "interest_saved_vs_minimum_only": $ or 0,
        "letters": [{"creditor": str, "letter_text": str}]
    }
```

### Phase 3: Output

```
cmd_analyze()
    │
    ├── Print box-drawn inventory table
    ├── Print strategy comparison (Avalanche vs Snowball side-by-side)
    ├── Print recommended plan (method, months, interest)
    ├── Print savings tips
    ├── Print generated creditor letters + save to /tmp/
    │
    └── return True
```

## Secondary Execution Paths

### cmd_letter(args)

```
cmd_letter(args)
  └─ LetterAgent.draft_letter(
         creditor=args.creditor,
         balance=args.balance,
         apr=args.apr,
         hardship_reason=args.hardship
     )
  └─ print(letter.to_text())
       Template-based letter with date, salutation, body, signature
  └─ return True
```

### cmd_progress(args)

```
cmd_progress(args)
  ├─ json.load(open(args.plan))
  ├─ Parse Debt list from JSON
  ├─ Build PayoffPlan model
  └─ ProgressAgent.progress_summary(plan, payments_made=0)
       ├─ percent_complete = payments_made / total_months
       ├─ projected_completion = Month Year
       ├─ on_track = pct >= expected (linear)
       └─ Return summary dict
  └─ Print progress report
  └─ return True
```

## Month-by-Month Simulation Detail

```
compute_plan(debts, monthly_surplus, method)
    │
    ├── Sort debts by method
    │   avalanche → APR desc
    │   snowball  → balance asc
    │
    ├── Initialize:
    │   balances = {label: d.balance}
    │   aprs = {label: d.apr}
    │   min_pays = {label: d.min_payment}
    │   target_index = 0
    │   month = 0
    │   total_interest = 0
    │
    └── Loop until all balances <= 0.01 OR month > 1200:
         │
         month += 1
         │
         ├── Apply interest to each active debt
         │    interest = balance * (APR / 100 / 12)
         │    balance += interest
         │    total_interest += interest
         │
         ├── Make minimum payments
         │    for each active debt (in original order):
         │        pmt = min(min_payment, balance)
         │        balance -= pmt
         │
         ├── Apply surplus to target debt
         │    while target is paid off → target_index += 1
         │    if target exists:
         │        extra = min(surplus, balance)
         │        balance -= extra
         │
         └── Record month data (payment amounts, balances)
    
    Return PayoffPlan(months_to_payoff=month, total_interest, schedule)
```

## Module Dependency Graph

```
__main__.py
    ├── coordinator.py
    │    ├── models.py                (Debt, PayoffPlan, SpendingProfile, CreditorLetter)
    │    ├── agents/__init__.py
    │    ├── agents/creditor_agent.py (→ models.Debt)
    │    ├── agents/spending_agent.py (→ models.SpendingProfile)
    │    ├── agents/strategy_agent.py (→ models.Debt, models.PayoffPlan)
    │    ├── agents/letter_agent.py   (→ models.CreditorLetter)
    │    └── agents/progress_agent.py (→ models.PayoffPlan)
    │
    ├── models.py                     (standalone — no internal deps)
    │
    └── agents/
         ├── __init__.py              (empty — package marker)
         ├── creditor_agent.py
         ├── spending_agent.py
         ├── strategy_agent.py
         ├── letter_agent.py
         └── progress_agent.py

tests/
    ├── test_models.py        → debtslayer.models
    ├── test_strategy.py      → debtslayer.agents.strategy_agent
    └── test_coordinator.py   → debtslayer.coordinator
```

## Data Flow

```
User Input (CLI args)         CLI Parser
    │                              │
    │  --debt "V:4500:22.99:50"    │ parse_debt_spec()
    │  --income 4800               │
    │  --expenses 3200             │
    ▼                              ▼
DebtSpec dicts              Debt models
    │                              │
    ▼                              ▼
DebtSlayerCoordinator        CreditorAgent(+), SpendingAgent(+)
    │                              │
    │  ┌─────────────────────┐    │
    │  │  StrategyAgent      │    │
    │  │  ┌──────────────┐   │    │
    │  │  │ Avalanche    │───┤    │
    │  │  │ Simulator    │   │    │
    │  │  └──────────────┘   │    │
    │  │  ┌──────────────┐   │    │
    │  │  │ Snowball     │───┤    │
    │  │  │ Simulator    │   │    │
    │  │  └──────────────┘   │    │
    │  │  Comparison → rec   │    │
    │  └─────────────────────┘    │
    │         │                    │
    ▼         ▼                    ▼
PayoffPlan JSON            CreditorLetter templates
    │                              │
    ▼                              ▼
stdout (box-drawn tables)   /tmp/{creditor}_letter.txt
```