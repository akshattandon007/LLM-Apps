# 🧮 abacus — Multi-Agent Financial Scenario Planner

**abacus** is a multi-agent CLI tool that models your personal finances and runs "what-if" scenarios. Tell it your income, expenses, and goals — 5 AI agents collaborate to produce a 5-year financial roadmap with actionable recommendations.

> Built with a supervisor-subordinate multi-agent architecture: Income Agent → Expense Agent → Scenario Engine → Goal Tracker → Supervisor synthesis.

## How it works

1. **Income Agent** — Parses your income streams, estimates net after taxes
2. **Expense Agent** — Categorizes spending (essential vs discretionary), calculates surplus
3. **Scenario Engine** — Pure math engine: compound interest, amortization, debt snowball
4. **Goal Tracker** — Checks if your goal is feasible, suggests monthly contributions
5. **Supervisor** — Coordinates the loop, runs what-if scenarios, produces the final report

Each agent communicates via typed dataclasses. The Scenario Engine never calls an LLM — all number crunching is Python stdlib math.

## Install

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/advanced-ai-agents/abacus
pip install -r requirements.txt
```

## Usage

### Quick start

```bash
# Basic scenario
python __main__.py \
  --income "salary 85000" \
  --expenses "rent 1800,groceries 600,netflix 15" \
  --savings 15000 \
  --goal "buy house" --target 60000
```

### Multiple income streams

```bash
python __main__.py \
  --income "salary 85000,freelance web 12000" \
  --expenses "rent 1800,groceries 600,utilities 250" \
  --debt 15000 \
  --goal "retire early" --target 500000 --years 15
```

### What-if scenarios

```bash
# "What if I get a $15k raise?"
python __main__.py \
  --income "salary 85000" \
  --expenses "rent 1800,groceries 600" \
  --what-if "what if I get a 15k raise"

# "What if I cut expenses by 30%?"
python __main__.py \
  --income "salary 85000" \
  --expenses "rent 1800,groceries 600" \
  --what-if "cut discretionary spending 30%"
```

### Interactive mode

```bash
python __main__.py --interactive
```

### JSON output

```bash
python __main__.py --income "salary 85000" --expenses "rent 1800" --json
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | _(none)_ | LLM API key. Omit for fallback mode (demo/structuring only) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | For custom endpoints (Anthropic, local LLMs) |
| `ABACUS_MODEL` | `gpt-4o-mini` | Model name for LLM calls |

No LLM key? abacus works in **fallback mode** with deterministic responses — you get the full financial math without needing an API key. Add a key for richer natural-language analysis.

## Running tests

```bash
cd abacus
python -m pytest tests/ -v
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  Supervisor (orchestrator)                   │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │ Income   │  │ Expense   │  │ Scenario │ │
│  │ Agent    │  │ Agent     │  │ Engine   │ │
│  └──────────┘  └───────────┘  └──────────┘ │
│  ┌──────────┐  ┌───────────┐                │
│  │ Goal     │  │ Supervisor│                │
│  │ Tracker  │  │ Synthesis │                │
│  └──────────┘  └───────────┘                │
└─────────────────────────────────────────────┘
```

## Project files

| File | Purpose |
|------|---------|
| `__main__.py` | CLI entry point with argparse |
| `models.py` | Financial dataclasses (IncomeStream, Expense, Goal, etc.) |
| `llm.py` | LLM API helper (any OpenAI-compatible endpoint) |
| `agents/income_agent.py` | Income parsing & tax estimation |
| `agents/expense_agent.py` | Expense categorization & analysis |
| `agents/scenario_engine.py` | Financial math engine (no LLM) |
| `agents/goal_tracker.py` | Goal feasibility & contribution suggestions |
| `agents/supervisor.py` | Multi-agent orchestrator |
| `tests/test_abacus.py` | 19 unit tests |
| `Decisions.md` | Architecture decisions log |
| `Flow.md` | Execution flow & call chains |