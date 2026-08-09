# Recall — Meeting Transcript RAG

> **"What did we actually decide in that meeting?"**

Upload meeting transcripts (.txt, .srt, .vtt) and ask natural-language questions. Get speaker-attributed answers with timestamps — not a wall of text, but who said what and when.

## How It Works

### Ingestion
1. Parse transcript → extract speaker names, timestamps, utterances
2. Chunk at speaker-turn boundaries (each utterance = one chunk)
3. Prepend speaker name: `[Sarah] The pricing model should be usage-based…`
4. Tag with metadata: meeting title, speaker, timestamps
5. Embed with `sentence-transformers/all-MiniLM-L6-v2` → store in FAISS

### Retrieval
1. Query gets classified into intent: `DECISION`, `ACTION_ITEM`, `OPINION`, `FACT`, or `FOLLOW_UP`
2. Speaker detection extracts who the question is about
3. Semantic search + optional metadata filter → top-k chunks
4. Claude generates answer with citations

## Architecture

```
rag/recall/
├── main.py                   # FastAPI server
├── requirements.txt          # Python dependencies
├── .env.example              # Config template
├── .gitignore
├── README.md
├── src/
│   ├── document_loader.py    # Parse TXT/SRT/VTT → structured utterances
│   ├── chunker.py            # Speaker-turn boundary chunking
│   ├── embedder.py           # sentence-transformers embeddings
│   ├── vector_store.py       # FAISS index + metadata filtering
│   ├── classifier.py         # Intent classification + speaker detection
│   ├── rag_chain.py          # LangChain retrieval + generation chain
│   └── models.py             # Pydantic models
├── tests/
│   └── test_smoke.py         # 26 tests: loader, chunker, embedder, store, classifier, end-to-end
├── frontend/
│   ├── package.json          # Next.js + Tailwind
│   ├── pages/
│   │   ├── index.js          # Upload page + chat interface
│   │   └── api/proxy.js      # Proxy to FastAPI backend
│   ├── components/
│   │   ├── ChatPanel.jsx     # Chat UI with message history
│   │   ├── FileUpload.jsx    # Transcript upload
│   │   └── AnswerCard.jsx    # Answer + speaker badge + timestamp + meeting tag
│   └── styles/globals.css
└── data/
    ├── generate_sample_transcript.py  # Creates sample meeting
    └── q3_pricing_meeting.txt         # 4 speakers, 15 utterances about SaaS pricing
```

## Quick Start

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Sample Transcript

The project ships with `data/q3_pricing_meeting.txt` — a 15-utterance meeting about SaaS pricing with 4 speakers (Sarah, Mike, Alex, Priya).

## Example Queries

| Query | Expected |
|-------|----------|
| "What did Sarah propose for pricing?" | Hybrid model: flat base + usage-based overage |
| "What were the action items?" | Alex → pricing tiers by Tue, Mike → metering specs by Wed, Priya → comms by Thu |
| "Who disagreed with the usage-based model?" | Alex — concerned about enterprise churn |
| "What did the team decide?" | Hybrid model + 12-month grandfathering for existing customers |

## Smoke Tests

```bash
python tests/test_smoke.py
```

Runs 26 tests covering: document parsing, chunking, embedding (384-dim), FAISS retrieval, intent classification, speaker detection, and 3 end-to-end queries.