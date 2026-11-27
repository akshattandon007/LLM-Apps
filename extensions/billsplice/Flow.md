# Flow.md — BillSplice Execution Trace

## Module Dependency Graph

```
billsplice/              # package root
├── __init__.py          # empty — namespace only
├── cli.py               # ENTRY POINT — CLI / interactive wizard
│   depends on:
│   ├── models.py        # → Item, Person, Bill
│   └── splitter.py      # → split_bill()
│
├── splitter.py          # CORE LOGIC — bill splitting arithmetic
│   depends on:
│   └── models.py        # → Bill, Person, Item, SplitResult
│
└── models.py            # DATA LAYER — pure dataclasses, no deps

tests/
└── test_splitter.py     # TESTS — imports splitter, models
```

## Execution Path 1: Interactive Mode (`billsplice`)

```
main()                                  # cli.py:117  — argparse parse, dispatches
└── run_interactive()                    # cli.py:13   — interactive wizard
    ├── [PRINT header + instructions]     # cli.py:16-18
    ├── [LOOP: read items from stdin]     # cli.py:22-36
    │   └── Bill.items.append(Item(...))  # models.py:13
    ├── [LOOP: read person names]         # cli.py:39-43
    │   └── Bill.people.append(Person())  # models.py:18
    ├── [LOOP: assign items to people]    # cli.py:48-73
    │   └── Person.items.append(item)     # models.py:20
    ├── [INPUT: tax_percent, tip_percent] # cli.py:76-84
    ├── split_bill(bill)                  # splitter.py:17  ← CORE CALL
    │   ├── _calculate_subtotals(bill)    # splitter.py:41  — per-person subtotals
    │   │   ├── sum(person.items.price)   # individual items
    │   │   └── shared_items / n_people   # shared items split equally
    │   ├── [for each person:]
    │   │   ├── fraction = subtotal / total_subtotal
    │   │   ├── tax_share = tax_amount × fraction
    │   │   ├── tip_share = tip_amount × fraction
    │   │   └── SplitResult(...)          # models.py:36   — per-person result
    │   └── return [SplitResult, ...]
    └── [PRINT per-person breakdown]      # cli.py:89-101
```

## Execution Path 2: Quick Mode (`billsplice --quick ...`)

```
main()                                    # cli.py:117
└── run_quick(args)                       # cli.py:103
    ├── Parse --names, --prices into Item[]
    ├── Parse --people into Person[]
    ├── Apply --assign (or mark all shared)
    ├── split_bill(bill)                  # splitter.py:17  ← CORE CALL (same path)
    └── [PRINT "PersonName: $X.XX" per line]
```

## Execution Path 3: Tests

```
python -m pytest tests/ -v
└── test_splitter.py
    ├── test_single_person_everything()
    │   └── split_bill(bill) → assert subtotal == 32.50
    ├── test_two_people_separate_items()
    │   └── split_bill(bill) → assert each person's total
    ├── test_with_tax_and_tip()
    │   └── split_bill(bill) → assert proportional tax/tip
    ├── test_shared_items()
    │   └── split_bill(bill) → assert 3-way equal split
    ├── test_no_items()
    │   └── split_bill(bill) → assert []
    ├── test_no_people()
    │   └── split_bill(bill) → assert []
    ├── test_zero_subtotal()
    │   └── split_bill(bill) → assert no ZeroDivisionError
    └── test_three_way_equal_split()
        └── split_bill(bill) → assert $20 each
```

## Data Flow

```
USER INPUT (items, people, assignments, tax%, tip%)
    │
    ▼
cli.py ──builds──► Bill(items=[Item...], people=[Person...],
    │               tax_percent=Decimal, tip_percent=Decimal)
    │
    ▼
split_bill(bill) ──calls──► _calculate_subtotals(bill)
    │                           │
    │                           ▼
    │                   for each person:
    │                       subtotal = sum(their items)
    │                           + (shared / n_people)
    │                           │
    │                           ▼
    │                   {person_name: subtotal, ...}
    │
    ▼
    for each person:
        fraction = person.subtotal / total_subtotal
        tax_share = bill.tax_amount × fraction
        tip_share = bill.tip_amount × fraction
        total = subtotal + tax_share + tip_share
    │
    ▼
    [SplitResult(person_name, items, subtotal,
                 tax_share, tip_share, total)]
    │
    ▼
cli.py ──formats──► terminal output (per-person breakdown)
```

## Key Design Notes

- **All arithmetic in Decimal** — no float rounding errors on money.
- **Two-phase splitting** — items first, then assign to people. Reflects real-world bill flow.
- **Shared items distributed evenly** before prorating tax/tip.
- **Tax and tip prorated by subtotal fraction** — the fairest default. If Alice's items are 60% of the subtotal, she pays 60% of tax and tip.
- **Rounding**: `ROUND_HALF_UP` on every division and multiplication that produces money amounts. The sum of all person totals equals the bill total (within ±$0.02 due to rounding).