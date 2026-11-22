# Flow.md — TabCalc Execution Flow

## Entry Point

```
python -m tabcalc.cli [args...]    # OR
tabcalc [args...]                   # (after pip install)
```

## Module Dependency Graph

```
tabcalc/
├── __init__.py        ← package marker (exports version)
├── core.py            ← no internal imports (pure logic)
│   depends on:        datetime, decimal, math (stdlib)
│   exports:           Expense, Settlement, ParticipantBalance, SettlementPlan,
│                      compute_balances(), compute_minimum_transfers(), compute_settlement()
│
└── cli.py             ← CLI wrapper
    depends on:        tabcalc.core (Expense, SettlementPlan, compute_settlement)
                       argparse, json, sys, decimal, pathlib (stdlib)
    exports:           main(), parse_expense_line(), parse_expense_file(),
                       parse_expense_text(), format_settlement(), format_json()
```

## Execution Paths

### Path A: Interactive stdin (no flags)

```
main(None)
  ├── parse_args([])
  │     └── argparse: no -f, no -e → stdin_used = True
  ├── (if stdin): sys.stdin.read() → raw text
  ├── parse_expense_text(raw_text)
  │     └── for each non-empty, non-comment line:
  │           parse_expense_line(line)
  │             ├── split("|") → 4+ parts
  │             ├── Decimal(parts[2]) → amount
  │             ├── parts[3].split(",") → split_among
  │             └── return Expense(description, paid_by, amount, split_among)
  │     └── return List[Expense]
  ├── compute_settlement(expenses)
  │     ├── compute_balances(expenses)
  │     │     └── for each Expense:
  │     │           share = amount / len(split_among)
  │     │           balances[paid_by] += amount
  │     │           for person in split_among: balances[person] -= share
  │     │     └── return List[ParticipantBalance]
  │     ├── compute_minimum_transfers(balances)
  │     │     ├── sort creditors descending by balance
  │     │     ├── sort debtors descending by debt
  │     │     └── two-pointer greedy: min(creditor, debtor) per iteration
  │     │     └── return List[Settlement]
  │     └── return SettlementPlan(balances, transfers, total_spent, per_person)
  ├── format_settlement(plan)       (if not --json)
  │     └── build string with header, balances table, transfers table
  └── print(...)
```

### Path B: File input (`-f expenses.txt`)

```
main(["-f", "expenses.txt"])
  ├── parse_args → args.file = Path("expenses.txt")
  ├── parse_expense_file(Path("expenses.txt"))
  │     ├── Path.read_text() → raw text
  │     └── parse_expense_text(text) → ... (same as Path A)
  ├── compute_settlement(expenses) → ... (same)
  └── print(...)
```

### Path C: Inline expenses (`-e "..." -e "..."`)

```
main(["-e", "Dinner|Alice|45|Alice,Bob,Charlie", "-e", "..."])
  ├── parse_args → args.inline_expenses = ["Dinner|Alice|45|Alice,Bob,Charlie", "..."]
  ├── for each inline string: parse_expense_line(s) → Expense
  ├── compute_settlement(expenses) → ... (same)
  └── print(...)
```

### Path D: JSON output (`-f expenses.txt --json`)

```
main(["-f", "expenses.txt", "--json"])
  ├── parse_args → args.json = True
  ├── parse_expense_file → expenses
  ├── compute_settlement(expenses) → plan
  └── format_json(plan)
        └── json.dumps({total_spent, per_person, balances dict, transfers list})
```

## Key Data Flow

```
User Input (stdin/file/inline)
        │
        ▼
parse_expense_line() / parse_expense_text()
        │
        ▼
List[Expense]          ← Data Model
        │
        ▼
compute_balances()
        │
        ▼
List[ParticipantBalance]   ← net_balance per person
        │
        ▼
compute_minimum_transfers()
        │
        ▼
List[Settlement]        ← from_person → to_person : amount
        │
        ▼
SettlementPlan          ← Aggregate result object
        │
        ├── format_settlement() → pretty-printed table
        └── format_json()       → JSON string
        │
        ▼
stdout
```

## Algorithm: Minimum-Transfer Settlement

```
Input: Balances (name → net_balance)
  ───────────────────────────────────
  1. Split into creditors (balance > 0) and debtors (balance < 0)
  2. Sort both lists descending by absolute balance
  3. While creditors and debtors remain:
     a. Let C = biggest creditor, D = biggest debtor
     b. transfer = min(C.balance, D.debt)
     c. D pays C: transfer amount
     d. Reduce both balances by transfer
     e. If C.balance == 0: move to next creditor
     f. If D.debt == 0: move to next debtor
  Output: List[Settlement] — exactly N-1 transfers for N participants
          (where no one is already settled)
```

### Example Walkthrough

```
Expenses:
  Dinner  | Alice | $45 | Alice,Bob,Charlie
  Drinks  | Bob   | $30 | Alice,Bob
  Taxi    | Charlie | $15 | Alice,Bob,Charlie

Shares:
  Dinner: $15/person → Alice +45, Alice/Bob/Charlie -15 each
  Drinks: $15/person → Bob +30, Alice -15, Bob -15
  Taxi:   $5/person  → Charlie +15, Alice -5, Bob -5, Charlie -5

Balances:
  Alice:   +45 -15 -15 -5  = +10  (owed)
  Bob:     -15 +30 -15 -5  = -5   (owes)
  Charlie: -15 -5 +15 -5   = -5   (owes)   [wait, this seems off]

Let me recalculate:
  Dinner ($45 split 3 ways = $15 each):
    Alice: +45 (paid) -15 (her share) = +30
    Bob: -15
    Charlie: -15

  Drinks ($30 split 2 ways = $15 each):
    Bob: +30 (paid) -15 (his share) = +15
    Alice: -15

  Taxi ($15 split 3 ways = $5 each):
    Charlie: +15 (paid) -5 (her share) = +10
    Alice: -5
    Bob: -5

  Final:
    Alice:   +30 -15 -5  = +10
    Bob:     -15 +15 -5  = -5
    Charlie: -15 +10     = -5

  Creditors:  Alice (+10)
  Debtors:    Bob (-5), Charlie (-5)
  
  Transfer 1: Bob pays Alice $5
  Transfer 2: Charlie pays Alice $5
  Result: 2 transfers, all settled.
```