# offdays 📅 — Max Your Time Off

**Plan the perfect leave.** Enter your country and how many leave days you're willing to spend — offdays fetches public holidays and tells you *exactly* which dates to book for the longest consecutive break.

> *"Book 1 day → 4 days off (Jan 2 → Jan 1–4)"*
> *"Book 2 days → 9 days off (Apr 14–19)"*

Powered by the free [Nager.Date API](https://date.nager.at) — no signup, no API key.

---

## Features

- ✅ **200+ countries** — any country Nager.Date supports
- ✅ **Any year** — past, present, future
- ✅ **Smart bridging** — connects holidays to weekends and merges adjacent holiday blocks
- ✅ **Ranked output** — best plans sorted by days-off per leave-day spent
- ✅ **Free weekend alerts** — long weekends you already have, no leave needed
- ✅ **JSON mode** — pipe into scripts or dashboards
- ✅ **Zero dependencies** — pure Python stdlib (urllib, datetime, argparse)

---

## Install

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/extensions/offdays
pip install -e .
```

Or run directly without install:

```bash
cd LLM-Apps/extensions/offdays
python -m offdays.cli --country US --year 2026 --days 5
```

---

## Usage

### Basic — current year, US, 3 leave days
```bash
offdays
```

### Specific country and year
```bash
offdays --country GB --year 2027 --days 5
```

### See all supported countries
```bash
offdays --list-countries
```

### JSON output (for scripts)
```bash
offdays --country DE --days 2 --json
```

### Filter by minimum stretch length
```bash
offdays --min-stretch 5
```

---

## Examples

```
$ offdays --country US --year 2026 --days 3

🇺🇸  2026 · United States (US)
Public holidays: 10 · Workdays: 260

✦ Free long weekends (no leave needed):
  Jul 03–05 (3 days) · Independence Day
  Jan 17–19 (3 days) · Martin Luther King, Jr. Day
  Dec 25–27 (3 days) · Christmas Day

🎯 TOP LEAVE PLANS (using up to 3 leave days):

  1. Book 1 day → 4 off (3 free)
       Fri Jan 02
       Jan 01 – Jan 04 · New Year's Day

  2. Book 1 day → 4 off (3 free)
       Fri Nov 27
       Nov 26 – Nov 29 · Thanksgiving Day

  3. Book 2 days → 5 off (3 free)
       Thu Jan 15, Fri Jan 16
       Jan 15 – Jan 19 · Martin Luther King, Jr. Day

  4. Book 1 day → 4 off (3 free)
       Thu Jul 02
       Jul 02 – Jul 05 · Independence Day
```

---

## How It Works

1. **Fetch** — offdays fetches all national public holidays from Nager.Date
2. **Map** — builds a full calendar of off-days (weekends + holidays)
3. **Find blocks** — identifies maximal consecutive off-day runs
4. **Bridge** — for each block, computes which workdays you can "book off" to bridge to adjacent weekends or holidays
5. **Rank** — all combinations ranked by consecutive days off, lowest leave days first

---

## Tests

```bash
cd extensions/offdays
pip install pytest
pytest tests/ -v
```

The test suite covers:
- API fetching (mocked network)
- Off-set construction (holidays + weekends)
- Block finding (MLK merging with weekend, Jan 1 isolated)
- Gap computation (left/right workday gaps)
- Full plan computation (UK, US, edge cases)
- Deduplication and sorting
- Plan dataclass ordering

---

## Project Structure

```
extensions/offdays/
├── offdays/
│   ├── __init__.py          # Package init, version
│   ├── api.py               # Nager.Date API client
│   ├── planner.py           # Core leave optimization algorithm
│   └── cli.py               # CLI entry point (argparse)
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API client tests
│   └── test_planner.py      # Planner algorithm tests
├── pyproject.toml
├── README.md
├── Decisions.md
└── Flow.md
```

---

## Data Source

All holiday data comes from [Nager.Date](https://date.nager.at) — a free, zero-auth public holiday API covering 200+ countries and territories. No API key required. No rate limiting for reasonable use.

---

## License

MIT — free to use, modify, and share.