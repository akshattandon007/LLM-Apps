# 🗑️ Subscription Slayer — MCP Server

> *Find every subscription you forgot about and kill the ones you don't need.*

An MCP server that exposes tools for AI agents to scan bank statements and email inboxes, detect forgotten subscriptions, categorize them, estimate annual costs, and generate cancellation links. The average person has 4–7 forgotten subscriptions draining **$50–150/month**.

## MCP Tools

| Tool | Description |
|------|-------------|
| `scan_statements(csv_path)` | Parse bank CSV for recurring charges |
| `detect_recurring(charges)` | Identify which charges are recurring subscriptions |
| `categorize(subscriptions)` | Group into streaming/cloud/fitness/news/software |
| `estimate_annual_cost(subscriptions)` | Total per category and overall |
| `identify_unused(subscriptions, answers)` | Flag subscriptions the user doesn't use |
| `get_cancellation_info(service_name)` | Cancellation URL and process for known services |
| `track_trials(subscriptions)` | Detect trials nearing conversion |

## Merchant Database

24 known services including Spotify, Netflix, Disney+, Hulu, HBO Max, Apple Music, Amazon Prime, YouTube Premium, Patreon, New York Times, Dropbox, Google Drive, iCloud, Adobe CC, Microsoft 365, Canva Pro, Headspace, Calm, Duolingo Plus, Peloton, ClassPass, and gym memberships.

## Usage

```bash
# Search for cancellation info
python main.py find spotify

# Scan a bank statement
python main.py scan --csv statements.csv

# Start the MCP server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |