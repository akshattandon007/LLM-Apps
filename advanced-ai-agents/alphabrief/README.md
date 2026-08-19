# 📊 AlphaBrief — Financial Intelligence Multi-Agent System

> *Your personal quantitative analyst — tracks your portfolio, reads SEC filings, monitors sentiment, and briefs you every morning.*

**AlphaBrief** is a multi-agent financial intelligence system. It runs 5 parallel specialist agents daily, then a coordinator synthesizes everything into a structured morning briefing.

## Pipeline

```
5 Parallel Agents ──────────────────────┐
├─ 📈 Portfolio Agent  (holdings, P&L)  │
├─ 📉 Technical Agent  (RSI, MACD, MAs) │
├─ 📋 Fundamental Agent (SEC filings)   │
├─ 📰 Sentiment Agent  (news analysis)  │
├─ ⚠️  Risk Agent      (beta, VaR, corr)│
    ↓                                   │
Coordinator (synthesizes → briefing)  ←─┘
    ↓
Daily Briefing (markdown report)
```

## Usage

```bash
# Simulated mode (no API keys needed)
python main.py --simulate

# Real portfolio
python main.py --portfolio "AAPL:10,MSFT:15,NVDA:5" --cash 50000

# Load portfolio from JSON file
python main.py --portfolio-file my_portfolio.json
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## What Each Agent Does

| Agent | Analysis | Output |
|-------|----------|--------|
| **Portfolio** | Holdings, prices, daily P&L, allocation % | Ticker-by-ticker breakdown |
| **Technical** | RSI, MACD, 20/50 SMA, Bollinger Bands | Divergence flags & signals |
| **Fundamental** | SEC EDGAR 10-K/10-Q/8-K parsing | Key changes & material events |
| **Sentiment** | News headline analysis per holding | Bullish/bearish/neutral score |
| **Risk** | Beta, Sharpe ratio, VaR, concentration | Risk metrics & action alerts |
| **Coordinator** | Merges all 5 → structured briefing | 2-page markdown report |

## Tech Stack

- Python · yfinance · pandas · numpy · httpx
- SEC EDGAR API · news feeds
- Pydantic · python-dotenv
- 5 parallel specialists + 1 synthesizer