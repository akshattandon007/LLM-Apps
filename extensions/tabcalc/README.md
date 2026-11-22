# ⚖️ TabCalc — Settle Group Expenses with Minimum Transfers

**TabCalc** is a zero-dependency CLI tool that figures out who owes whom after a group outing. Enter who paid what and who was there — it computes each person's balance and spits out the **minimum number of transfers** needed to settle up.

No more spreadsheets, no more mental math, no more "wait, I think you owe me $12.50 but you paid for the Uber so..."

---

## ✨ Features

- **Minimum-transfers algorithm** — greedy settlement means fewer Venmo requests
- **Flexible split rules** — each expense can split among any subset of the group
- **Multiple input modes** — file, inline `-e` flags, or interactive stdin
- **JSON output** — pipe into your own tools or scripts
- **Zero external dependencies** — pure Python stdlib (3.9+)

---

## 🚀 Installation

```bash
pip install /path/to/tabcalc
```

Or run directly:

```bash
cd tabcalc
python -m tabcalc.cli
```

---

## 📖 Usage

### Quick start (interactive)

```bash
tabcalc
```

Type one expense per line:

```
Dinner | Alice | 45.00 | Alice,Bob,Charlie
Drinks | Bob | 30.00 | Alice,Bob
Taxi | Charlie | 15.00 | Alice,Bob,Charlie
```
Press Ctrl+D and get your settlement plan.

### File input

```bash
tabcalc -f expenses.txt
```

Where `expenses.txt` contains:

```
# Weekend trip — June 2026
Hotel | Alice | 200.00 | Alice,Bob,Charlie
Gas   | Bob   | 60.00  | Alice,Bob
Food  | Charlie | 90.00 | Alice,Bob,Charlie
```

### Inline expenses

```bash
tabcalc -e "Dinner|Alice|45|Alice,Bob,Charlie" -e "Drinks|Bob|30|Alice,Bob"
```

### JSON output

```bash
tabcalc -f expenses.txt --json
```

Output:
```json
{
  "total_spent": 350.0,
  "per_person": 116.67,
  "balances": {
    "Alice": 83.33,
    "Bob": -56.67,
    "Charlie": -26.66
  },
  "transfers": [
    {"from": "Bob", "to": "Alice", "amount": 56.67},
    {"from": "Charlie", "to": "Alice", "amount": 26.66}
  ]
}
```

### Expense line format

```
description | paid_by | amount | person1,person2,...
```

- Lines starting with `#` or `//` are comments
- Whitespace around fields is trimmed
- Amount supports decimals (e.g. `12.50`, `0.99`)

---

## 🧪 Tests

```bash
cd /path/to/tabcalc
python -m pytest tests/ -v
```

Tests cover:
- Balance computation (equal/uneven splits, edge cases)
- Minimum-transfers algorithm (2-person, N-person chain, balanced groups)
- Full pipeline integration
- CLI parsing (valid/invalid input, whitespace handling)
- Output formatting (human-readable + JSON)

---

## 📁 Project Structure

```
tabcalc/
├── pyproject.toml
├── README.md
├── Decisions.md
├── Flow.md
├── tabcalc/
│   ├── __init__.py
│   ├── core.py      # Balance computation & settlement algorithm
│   └── cli.py       # CLI parsing, input handling, formatting
└── tests/
    ├── __init__.py
    └── test_tabcalc.py
```

---

## 🔗 Related

Built as part of the daily rota — Extension category (position 3 of 5).