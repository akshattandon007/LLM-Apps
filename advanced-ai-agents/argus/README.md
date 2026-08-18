# 👁️ ARGUS — Deep Research Agent

> *Give it a question, get back a cited research report — with sub-questions generated, sources crawled, cross-referenced, and synthesized autonomously.*

**ARGUS** is a multi-agent deep research system. Give it a complex question and it plans research, searches across 4 independent sources, extracts content, cross-references findings, and delivers a structured markdown report with inline citations.

## Pipeline

```
User Query
    ↓
Research Planner (decomposes into sub-questions)
    ↓
4 Parallel Searchers ──────────────────┐
├─ 🌐 Web Search (DuckDuckGo)          │
├─ 📄 arXiv (academic papers)          │
├─ 💬 Hacker News (social signals)     │
├─ 📝 Blog/RSS (industry analysis)    │
    ↓                                  │
Content Extractor (crawl + extract)  ←─┘
    ↓
Cross-Reference Engine (consensus, contradictions, gaps)
    ↓
Synthesis Writer (structured report with citations)
    ↓
Markdown Report
```

## Usage

```bash
# Simulated mode (no API keys needed)
python main.py --simulate

# Real research
python main.py --query "What are the production failure rates of multi-agent frameworks?"
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# No API keys needed — DuckDuckGo, arXiv, and HN Algolia are free
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

- Python · httpx · BeautifulSoup · duckduckgo_search
- arXiv API · HN Algolia API
- Pydantic · FastAPI (optional)
- 4 parallel search sources with independent mock data for tests