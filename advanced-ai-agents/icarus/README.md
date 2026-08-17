# 🛡️ Icarus — Incident Remediation Agent

> *Your SRE on autopilot — alert comes in, root cause found, fix applied, post-mortem drafted, all before your pager wakes you.*

**Icarus** is an end-to-end incident remediation agent. It ingests alerts, triages logs/metrics/deployments, performs root cause analysis, proposes remediation plans (human-gated for destructive actions), and drafts post-mortem reports.

## Pipeline

```
Alert → Ingest → Triage → RCA → Remediate (gated) → Post-Mortem
                            ↑                      ↓
                        Memory (past incidents) ←──┘
```

## Phases

1. **Alert Ingest** — Accept alerts from PagerDuty, Prometheus webhooks, CloudWatch, or simulated input
2. **Triage** — Fetch recent logs, metrics, and deployment history related to the incident
3. **RCA** — Correlate events across data sources to identify the probable root cause
4. **Remediation** — Propose a fix (rollback, restart, scale up, toggle feature flag). Destructive actions require human approval
5. **Post-Mortem** — Draft a structured markdown report: timeline, impact, root cause, action items

## Usage

```bash
# Simulated mode (no API keys needed)
python main.py --simulate

# Real alert
python main.py --alert "API latency spiked 5x at 10:42 UTC on production"

# Feed a JSON alert payload
python main.py --alert-file /path/to/alert.json
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env (optional — simulated mode works without them)
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

- Python · httpx · Pydantic
- Simulated mode for zero-config dev
- Human approval gate for destructive remediation
- Incident memory for pattern matching across incidents