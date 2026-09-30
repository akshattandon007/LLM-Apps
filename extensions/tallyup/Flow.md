# Flow.md

## Module dependency graph

```
tallyup/
  ┌─────────────────────────────────────────┐
  │            cli.py (entry)               │
  │  argparse CLI — dispatches to commands  │
  └──────────┬──────────────────────────────┘
             │ depends on
             ▼
  ┌──────────────────┐     ┌──────────────────────┐
  │   core.py        │◄────│    storage.py         │
  │  Expense (dataclass)│   │  JSON load/save       │
  │  Settlement (dclass)│   │  DecimalEncoder       │
  │  compute_balances() │   │  expense_to_dict()    │
  │  settle_debts()     │   │  dict_to_expense()    │
  │  format_report()    │   └──────────────────────┘
  └──────────────────┘
             │ depends on
             ▼
  ┌──────────────────┐
  │  __init__.py     │
  │  version info    │
  └──────────────────┘
```

## Function-level call chains

### `tallyup` (no args)
```
main() → build_parser() → parser.print_help()
```

### `tallyup add -d "Dinner" -a 42.00 -p Alice -s Alice Bob Carol`
```
main() → build_parser()
       → cmd_add(args)
         → load_expenses(DEFAULT_DATA_FILE)
           → storage.load_expenses()
             → Path.exists()
             → json.load() → dict_to_expense() for each
         → Expense(...)  # creates new expense
         → expenses.append(expense)
         → save_expenses(DEFAULT_DATA_FILE, expenses)
           → storage.save_expenses()
             → expense_to_dict() for each → json.dump()
         → print("✓ Recorded...")
```

### `tallyup list`
```
main() → build_parser()
       → cmd_list(args)
         → load_expenses(DEFAULT_DATA_FILE)
         → print table header
         → for each expense: print id, date, desc, amount, paid_by, participants
```

### `tallyup settle`
```
main() → build_parser()
       → cmd_settle(args)
         → load_expenses(file_path)
         → settle_debts(expenses)
           → compute_balances(expenses)
             → For each expense: credit payer, debit each participant
             → Return {person: net_balance}
           → Separate creditors (+balance) and debtors (-balance)
           → Sort both descending
           → Greedy match:
             while ci < len(creditors) and di < len(debtors):
               transfer = min(creditor_amount, debtor_amount)
               Settlement(from_person=debtor, to_person=creditor, amount=transfer)
               reduce both amounts
               advance index if reduced to < $0.01
           → Return [Settlement]
         → format_report(expenses, settlements)
           → Build visual box with expense list + settlement list + total
```

### `tallyup clear`
```
main() → build_parser()
       → cmd_clear(args)
         → if not --yes: prompt confirmation
         → save_expenses(DEFAULT_DATA_FILE, [])
```

### `tallyup summary`
```
main() → build_parser()
       → cmd_summary(args)
         → load_expenses(DEFAULT_DATA_FILE)
         → compute_balances(expenses)
         → print sorted table of person → net balance
```

## Data flow

```
User input (CLI args)
    │
    ▼
cli.py parses arguments
    │
    ▼
core.py computes balances & settlements
    │
    ▼
storage.py persists to ~/.tallyup/expenses.json
    │
    ▼
cli.py outputs formatted report to stdout
```

No external APIs, no network calls. All data stays local on the machine.