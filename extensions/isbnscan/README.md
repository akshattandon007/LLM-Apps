# 📚 ISBNScan

**Batch ISBN lookup tool** — resolve ISBNs (both ISBN-10 and ISBN-13) to full book metadata via the [Open Library API](https://openlibrary.org/).

---

## What It Does

Enter one or many ISBNs and get back:

- 📖 **Title, authors, publisher, publish year**
- 📄 **Page count, subjects/genres**
- 🖼️ **Cover image URL**
- 📊 **Formatted terminal output** with color-coded found/missing status
- 📁 **CSV export** for spreadsheet import

Perfect for used-book sellers cataloging inventory, librarians processing donations, teachers building reading lists, or anyone who needs to identify a stack of books by ISBN.

---

## Installation

```bash
# From the project directory
pip install .

# Or with pip in development mode
pip install -e .
```

Requires Python 3.10+.

---

## Usage

### Look up one or more ISBNs

```bash
isbnscan 9780141036144 9780061120084
```

### Read from a file

```bash
isbnscan --file isbns.txt
```

File format — one ISBN per line:
```
9780141036144
9780061120084
# Lines starting with # are ignored
9780439554930
```

### Pipe from stdin

```bash
cat isbns.txt | isbnscan
```

### Export to CSV

```bash
isbnscan --file isbns.txt --csv results.csv
```

### Sample output

```
================================================================================
  ISBN LOOKUP RESULTS — 3/4 found
================================================================================

[1] 9780141036144 — ✓ FOUND
  Title:    1984
  Authors:  George Orwell
  Publisher: Penguin
  Year:     2008
  Pages:    336
  Subjects: Dystopian fiction

[2] 9780000000000 — ✗ NOT FOUND
  No metadata found for this ISBN.
```

---

## Features

- **ISBN-10 and ISBN-13** — automatically normalizes both formats
- **Auto-detects invalid ISBNs** — skips them with a warning
- **Multiple input methods** — command-line args, file, stdin
- **Color-coded output** — green for found, red for missing (auto-disables in pipes)
- **CSV export** — shareable, importable into spreadsheets
- **Zero signup** — no API keys, no accounts, free to use

---

## API

The Open Library Books API is completely free and requires no API key. Rate limits are generous for moderate use. See [Open Library API docs](https://openlibrary.org/dev/docs/api/books).

---

## Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
python -m pytest tests/ -v
```

All tests use `httpx.MockTransport` — no network calls, no external dependencies.

---

## Project Structure

```
isbnscan/
├── isbnscan/
│   ├── __init__.py    # Package metadata
│   ├── __main__.py    # `python -m isbnscan` entry point
│   ├── cli.py         # CLI argument parsing and output formatting
│   └── lookup.py      # Open Library API lookup logic
├── tests/
│   └── test_lookup.py # Tests with mocked HTTP
├── pyproject.toml     # Build and dependency config
├── README.md          # This file
├── Decisions.md       # Design decisions and rejected alternatives
└── Flow.md            # Function-level call chains and module dependencies
```

---

## License

MIT
