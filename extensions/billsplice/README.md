# 🧾 BillSplice

**Split restaurant/group bills effortlessly** — a CLI tool that divides items, tax, and tip among people, telling everyone exactly what they owe.

No API keys. No accounts. No signup. Just Python and your terminal.

## What it does

1. Enter menu items and prices
2. Say who had what
3. Add tax % and tip %
4. Get a per-person breakdown showing subtotal, tax share, tip share, and total

## Install

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/extensions/billsplice
pip install -e .
```

Requires Python 3.10+.

## Usage

### Interactive mode (recommended)

```bash
billsplice
```

Walk through the wizard:

```
🧾 BillSplice — Bill Splitter
==================================================

📋 Enter items (one per line). Blank line to finish.
   Format: ItemName,Price  (e.g. Pizza,24.50)
   Add ! at end for shared items (e.g. Fries,8.00!)
   Item: Steak,45.00
   ✓ Steak — $45.00
   Item: Pasta,22.00
   ✓ Pasta — $22.00
   Item: Shared Salad,12.00!
   ✓ Shared Salad — $12.00 (shared)
   Item: [enter]
```

Then assign items to people, set tax and tip, and get the result.

### Quick mode (non-interactive)

```bash
billsplice --quick \
  --names "Steak,Pasta,Shared Salad" \
  --prices "45.00,22.00,12.00" \
  --people "Alice,Bob" \
  --assign "Alice,Bob," \
  --tax 8.875 --tip 18
```

Assignments: `--assign` takes one entry per item (`""` = shared item).

## Tests

```bash
cd extensions/billsplice
pip install -e ".[test]"  # or: pip install pytest
python -m pytest tests/ -v
```

## Example

**The $67 dinner:** Alice had steak ($45), Bob had pasta ($22), shared salad ($12) split equally. Tax 8.875%, tip 18%.

| Person | Subtotal | Tax | Tip | **Total** |
|--------|----------|-----|-----|-----------|
| Alice  | $49.00   | $4.35 | $8.82 | **$62.17** |
| Bob    | $26.00   | $2.31 | $4.68 | **$32.99** |
| **Total** | **$75.00** | **$6.66** | **$13.50** | **$95.16** |

## Project Files

- `billsplice/models.py` — Data classes (Item, Person, Bill, SplitResult)
- `billsplice/splitter.py` — Core splitting algorithm
- `billsplice/cli.py` — Interactive wizard & quick mode
- `tests/test_splitter.py` — Unit tests

See [Decisions.md](./Decisions.md) for architectural choices and [Flow.md](./Flow.md) for execution traces.