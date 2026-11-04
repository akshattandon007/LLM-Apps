# HealthGuard

> **Multi-agent medication interaction checker & health query system**

HealthGuard runs 4 specialized agents in sequence to give you a plain-language health report. Check drug interactions via OpenFDA, triage symptoms, research conditions from MedlinePlus, and get a compiled report — all from your terminal.

## 🧠 Agent Architecture

| Agent | Role | Data Source |
|-------|------|-------------|
| **Agent 1 — Drug Checker** | Checks pairwise drug-drug interactions | OpenFDA + curated clinical DB |
| **Agent 2 — Symptom Triage** | Assesses symptom urgency | Curated severity DB (10+ symptoms) |
| **Agent 3 — Condition Researcher** | Researches medical conditions | MedlinePlus API + curated DB |
| **Agent 4 — Report Compiler** | Combines all findings into a report | Cross-agent aggregation |

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Check drug interactions
python main.py check --drugs warfarin aspirin ibuprofen

# Assess symptoms
python main.py check --symptoms "chest pain" headache fever

# Run it all at once
python main.py check --drugs lisinopril metformin --symptoms dizziness

# Research a condition
python main.py condition hypertension

# Interactive mode
python main.py
```

## 📋 Usage Examples

### Drug interaction check
```bash
python main.py check --drugs warfarin aspirin
```
Detects: ⚠️ Warfarin + Aspirin = HIGH severity (increased bleeding risk)

### Full health check
```bash
python main.py check --drugs simvastatin amlodipine --symptoms "chest pain" headache
```
Outputs: interactions table, symptom triage, condition research, compiled report.

### Look up drug info
```bash
python main.py info --drugs lisinopril
```

### Interactive mode
```bash
python main.py
healthguard> aspirin, ibuprofen, headache
```

## 🌐 Data Sources

- **OpenFDA** (drug labels, interactions) — free, zero-auth, US Government
- **RxNorm via NIH/NLM** (drug identity) — free, zero-auth
- **MedlinePlus via NIH/NLM** (condition info) — free, zero-auth
- **Curated clinical interaction DB** (10 high-value interactions for offline use)

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

## 📦 Requirements

- Python 3.10+
- httpx, rich, typer, pydantic

## ⚠️ Disclaimer

This tool is for **informational purposes only**. It does NOT replace professional medical advice. If in doubt, consult a qualified healthcare provider or call emergency services.