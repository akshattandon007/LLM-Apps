# 🔬 triallight — Plain-Language Clinical Trial Assistant

**triallight** searches active clinical trials on [ClinicalTrials.gov](https://clinicaltrials.gov/) and explains them in plain, compassionate English — eligibility criteria, study purpose, what participation involves, all translated from dense regulatory text into something anyone can understand.

> **Why triallight?** ClinicalTrials.gov is the world's most authoritative registry of clinical studies, but its records are written for researchers and regulators — full of medical jargon, nested legal prose, and scattered across multiple pages. triallight pulls the key information and uses AI to explain it like a patient advocate would.

## ✨ Features

- **Search by condition** — Type any medical condition and get active trials
- **Geographic filtering** — Pass `--city "San Francisco"` to find trials near you
- **Plain-language digests** — Every study gets a 4-section breakdown: what it's about, who can participate (plain English), what participation involves, key logistics
- **PubMed context** — Automatically fetches recent research articles about your condition (toggle with `--no-pubmed`)
- **No sign-up** — All data comes from free public APIs; no accounts needed

## 📋 How It Works

```
You:  "multiple sclerosis --city Seattle"
       │
       ▼
  ┌─────────────────┐
  │ ClinicalTrials   │  ← search for active studies
  │ .gov API v2      │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  PubMed          │  ← recent articles on MS
  │  E-utilities     │
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  LLM (OpenAI-    │  ← translate each study into
  │  compatible)     │    plain-language digest
  └────────┬────────┘
           ▼
    You get: clear, actionable
    summaries of each trial
```

The RAG pipeline: **search** (ClinicalTrials.gov) → **retrieve** (full study records + PubMed abstracts) → **augment** (LLM generates plain-language eligibility rewrite).

## 🚀 Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set your API key (for AI digests)
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Search for trials
python main.py "type 2 diabetes"
python main.py "multiple sclerosis" --city "San Francisco"
python main.py "lung cancer" --city "Houston" --trials 8 --no-pubmed
python main.py "asthma" --raw   # no AI, just raw data
```

## 🧪 Examples

```bash
# Basic search
python main.py "rheumatoid arthritis"

# With location filtering
python main.py "alzheimer's" --city "Boston"

# Show more results, skip PubMed
python main.py "crohn's disease" --trials 10 --no-pubmed

# Raw mode (no API key needed)
python main.py "psoriasis" --raw
```

## ⚙️ Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | LLM provider key (OpenAI, OpenRouter, etc.) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom endpoint (OpenRouter: `https://openrouter.ai/api/v1`) |
| `OPENROUTER_API_KEY` | — | Fallback if `OPENAI_API_KEY` not set |

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

## 📁 Project Structure

```
rag/triallight/
├── main.py                 ← CLI entry point
├── requirements.txt        ← Python dependencies
├── AGENTS.md
├── Decisions.md            ← Architecture decisions
├── Flow.md                 ← Module dependency graph
├── README.md               ← This file
├── src/
│   ├── __init__.py
│   ├── clinicaltrials.py   ← ClinicalTrials.gov API v2 wrapper
│   ├── geo.py              ← Open-Meteo geocoding
│   ├── llm.py              ← LLM prompt assembly + API calls
│   ├── models.py           ← Data classes
│   └── pubmed.py           ← PubMed E-utilities wrapper
└── tests/
    ├── __init__.py
    └── test_triallight.py  ← Unit tests (mock-based)
```

## ⚠️ Disclaimer

This tool provides AI-generated plain-language summaries of official clinical trial records. Always verify eligibility and details with the trial coordinator listed on ClinicalTrials.gov. **triallight is not medical advice.**

## 🔗 Data Sources

- **ClinicalTrials.gov API v2** — Free, no auth, generous rate limits
- **PubMed E-utilities** — Free, no auth (3 req/s without key)
- **Open-Meteo Geo API** — Free, no auth, unlimited
- **OpenAI-compatible LLM** — Any model that speaks the OpenAI API

## 📜 License

MIT — see [LICENSE](../../LICENSE).