# GradPath

**Find affordable US colleges with real outcome data.**
Powered by the College Scorecard API (data.gov).

## What it does

GradPath helps families find colleges they can afford with confidence about
graduation rates and post-grad earnings. Instead of clicking through individual
college websites, you ask one question:

> "Find me colleges in California with net price under $15,000 that offer
> Computer Science."

## Features

- **Search** 6,300+ US schools by net price, state, major, and size
- **Profile** — tuition, graduation rate, median earnings, SAT/ACT scores
- **Compare** — head-to-head cost vs outcome for any two colleges
- **Earnings** — what graduates earn by field of study

## Quick start

```bash
# 1. Set up
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure API key (optional — simulated mode works without it)
cp .env.example .env
# Edit .env and add your College Scorecard API key

# 3. Run smoke tests
pytest tests/ -v

# 4. Use via CLI
python main.py find --budget-max 15000 --state CA --major "Computer Science"
python main.py profile "State University of Technology"
python main.py compare "State University of Technology" "Preston Liberal Arts College"
python main.py earnings "State University of Technology" "Computer Science"

# 5. Run as MCP server (stdio — connect Claude Desktop etc.)
python main.py

# 6. Run as HTTP SSE server
python main.py --http --port 8080
```

## MCP Tools

| Tool | Description |
|---|---|
| `find_colleges` | Search 6,300+ US schools by budget, state, major, size |
| `college_profile` | Tuition, grad rate, median earnings, demographics |
| `compare_colleges` | Head-to-head cost vs outcome comparison |
| `earnings_by_program` | What graduates earn by field of study |

## Simulated mode

When `COLLEGE_SCORECARD_API_KEY` is not set in `.env`, GradPath runs in
simulated mode with 8 realistic sample colleges. This is great for
development, testing, and demos without needing an API key.

To get a free API key: https://api.data.gov/signup/

## Data source

[College Scorecard](https://collegescorecard.ed.gov/data/) — the US Department
of Education's database of 6,300+ institutions with data on costs,
completion rates, earnings, and more.

## Project structure

```
gradpath/
├── server.py              # MCP server entry point (4 tools)
├── main.py                # CLI entry point for testing
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Decisions.md           # Architectural decisions
├── Flow.md                # Execution flow documentation
├── src/
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── scorecard.py       # College Scorecard API client
│   ├── searcher.py        # College search logic
│   ├── profile.py         # College profile logic
│   ├── comparer.py        # Side-by-side comparison
│   └── earnings.py        # Earnings by program
└── tests/
    ├── __init__.py
    ├── conftest.py         # Fixtures with mock data
    └── test_smoke.py       # Smoke tests
```