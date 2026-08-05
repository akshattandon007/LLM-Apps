# 💰 SpendLens

> *"Ask your bank account what happened to your money."*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-1.3-green)](https://langchain.com)
[![Claude](https://img.shields.io/badge/LLM-Claude%20Sonnet-purple)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![tests](https://img.shields.io/badge/tests-38%2F38%20passing-brightgreen)](tests/)

---

## What It Does

SpendLens ingests your bank and credit card statements (PDFs, CSVs, or Plaid) and lets you ask natural-language questions about your spending — grounded in your actual transaction data, not guesses.

```
📄 Statement files  →  🔍 Parse & Embed  →  🤖 Claude RAG  →  💬 Plain-English Answers
```

### Example Interactions

```
You: How much did I spend on coffee this month?

SpendLens: You spent $18.25 across 3 transactions:
  • STARBUCKS COFFEE  —  $5.75  on 2025-01-20  [Dining]
  • DUNKIN DONUTS      —  $12.50  on 2025-01-22  [Dining]

  Total: $18.25
```

```
You: What's that $14.99 charge I keep seeing?

SpendLens: That's AMAZON PRIME MEMBERSHIP — it appears 3 times
  (2025-01-07, 2025-02-07, 2025-03-07). Looks like a monthly subscription.
  Category: Subscriptions | Total: $44.97
```

```
You: Show me my top spending categories.

SpendLens: [Returns category breakdown with charts]
  • Groceries:      $482.72  (24%)
  • Housing:        $4,400.00 (58%)
  • Dining:         $155.40  (8%)
  • Transport:      $258.00  (13%)
  • Entertainment:  $41.97   (2%)
```

---

## Architecture

```
Next.js Frontend (chat UI + upload)
         │
         ▼
   FastAPI Server (main.py)
         │
    ┌────┴─────┬──────────┐
    ▼          ▼          ▼
Document    Vector     Analytics
Loader      Store      Engine
    │          │
    ▼          ▼
Claude RAG Chain
```

### Key Design Decisions

- **LLM:** Claude Sonnet 4.5 via Anthropic API — accurate financial answers
- **Embeddings:** `all-MiniLM-L6-v2` — runs on CPU, 384-dim, no extra API key
- **Vector Store:** FAISS (in-memory with disk persistence option)
- **Retrieval:** MMR with k=10 — diverse, relevant transaction chunks
- **Statement Parsing:** pdfplumber for PDFs, pandas for CSVs, auto-column detection
- **Analytics:** Category breakdowns, monthly trends, top merchants, subscription detection

---

## Quick Start

### 1. Prerequisites

- Python **3.10+**
- An [Anthropic API key](https://console.anthropic.com/)

### 2. Install

```bash
cd rag/spend-lens

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 4. Run

```bash
# CLI mode — ingest statements and chat
python main.py --cli --files data/sample/jan_mar_2025.csv

# API server mode
python main.py
# Then open http://localhost:8000/docs for interactive API docs
```

---

## Modes

### CLI Mode (`python main.py --cli --files ...`)

Full interactive terminal experience with commands:
- `/stats` — Spending summary
- `/cats` — Category breakdown with bar charts
- `/subs` — Detected subscriptions
- `/reset` — Clear conversation history
- `/quit` — Exit

### API Server (`python main.py`)

REST endpoints:
- `POST /ingest` — Upload PDF/CSV statements
- `POST /chat` — Natural-language questions about your spending
- `GET /stats` — Category breakdowns, monthly trends, top merchants, subscriptions
- `GET /health` — Health check
- `POST /reset` — Clear all data

Full docs at `http://localhost:8000/docs`

---

## API Examples

```bash
# Upload a CSV statement
curl -F "file=@statement.csv" http://localhost:8000/ingest

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "how much did I spend on coffee?"}'

# Get stats
curl http://localhost:8000/stats?top_merchants_n=5&period_days=30
```

---

## Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Claude model identifier |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `MAX_TOKENS` | `2048` | Max Claude response tokens |
| `RETRIEVAL_K` | `10` | Transaction chunks retrieved per query |
| `PLAID_CLIENT_ID` | *(optional)* | Plaid client ID (for live bank connections) |
| `PLAID_SECRET` | *(optional)* | Plaid secret |
| `PLAID_ENV` | `sandbox` | Plaid environment |

---

## Supported Statement Formats

- ✅ **CSV** — Any bank export with date, description, and amount columns (auto-detected)
- ✅ **PDF** — Bank/credit card statements with table-structured transaction data
- 🔜 **Plaid** — Live bank connections (coming soon)

### Auto-Detected CSV Column Names

SpendLens recognizes common column naming conventions:
- **Date:** Date, Transaction Date, Post Date, Posted Date
- **Description:** Description, Merchant, Payee, Name, Memo, Transaction
- **Amount:** Amount, Debit, Credit, Withdrawal, Deposit
- **Category:** Category, Tag, Label, Group

---

## Project Structure

```
spend-lens/
├── main.py                  # FastAPI + CLI entry point
├── src/
│   ├── document_loader.py   # PDF/CSV parsing, transaction normalization
│   ├── vector_store.py      # HuggingFace embeddings + FAISS indexing
│   ├── rag_chain.py         # Claude RAG chain with conversation memory
│   └── analytics.py         # Category breakdowns, trends, subscription detection
├── tests/
│   ├── test_document_loader.py
│   └── test_rag_chain.py
├── data/
│   └── sample/              # Sample CSV statements for testing
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## How RAG Works (For Non-Technical Users)

1. **Ingest** — Upload your bank statement PDF or CSV. SpendLens parses every transaction.
2. **Chunk** — Each transaction becomes a searchable snippet with date, merchant, amount, and category metadata.
3. **Embed** — Each snippet is converted into a numerical "fingerprint" that captures its meaning.
4. **Retrieve** — When you ask a question, SpendLens finds the most relevant transactions.
5. **Answer** — Claude reads those transactions and writes a grounded, citation-backed answer — no hallucinations.

---

## Related Projects

- [API Docs RAG Agent](../rag-agent/) — Ask questions about any API documentation
- [Slack MCP Agent](../../mcp-agents/slack_mcp_agent/) — AI assistant for Slack via MCP

---

## License

MIT — see [LICENSE](LICENSE).
