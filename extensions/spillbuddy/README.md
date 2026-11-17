# 🧴 SpillBuddy — Stain Removal Guide for the Real World

**Never panic over a spill again.** SpillBuddy tells you exactly what to do when you spill red wine on a white carpet, coffee on a silk blouse, or grease on your favorite jeans.

```bash
spillbuddy lookup "red wine" cotton
```

## ✨ What It Does

- **12+ stain types** — red wine, coffee, blood, grass, grease, ink, tomato sauce, mud, wax, marker, sweat, chocolate, berry, pet stains, white wine
- **7 fabric categories** — cotton, silk, wool, synthetic, carpet, upholstery, plus a general fallback
- **Three ways to use it** — direct lookup, interactive mode, or list all stains

## 🚀 Install

```bash
pip install -e .
```

## 📖 Usage

### Look up a stain

```bash
spillbuddy lookup "red wine" cotton
```

Output:
```
🧴 SpillBuddy — Red Wine on Cotton

📋 Method:
  Blot excess immediately. Cover stain with salt to absorb remaining wine.
  Rinse with cold water from the back. Apply liquid laundry detergent and
  let sit 5 min. Launder in warm water with oxygen bleach.

⚠️  Caution:
  Do NOT use hot water — it sets the stain.
```

### List all stain types

```bash
spillbuddy list
```

### Interactive mode

```bash
spillbuddy interactive
```

Then just answer the prompts:
```
What did you spill? coffee
On what fabric? (cotton, silk, wool, synthetic, carpet, upholstery, all): carpet
```

## 🧪 Tests

```bash
pip install pytest
pytest tests/ -v
```

21 tests covering:
- Every stain/fabric combination returns valid data
- Unknown stains return None gracefully
- Case-insensitive matching
- All entries have non-empty methods and cautions
- CLI argument parsing and output formatting

## 🗂️ Project Structure

```
spillbuddy/
├── spillbuddy/
│   ├── __init__.py      # Package metadata
│   ├── __main__.py      # python -m support
│   ├── cli.py           # CLI parser and commands
│   └── data.py          # Stain removal database
├── tests/
│   ├── conftest.py
│   ├── test_data.py     # Data integrity + lookup tests
│   └── test_cli.py      # CLI parsing tests
├── Decisions.md         # Architectural decisions
├── Flow.md              # Execution flow documentation
├── setup.py
├── pyproject.toml
└── README.md
```