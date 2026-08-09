# 🧠 Recall — Chat With Your Meetings 🎯

**Turn meeting transcripts into searchable Q&A. Ask anything. Get who said what, and when.**

Recall is a FastAPI + Next.js app that ingests meeting transcripts (.txt, .srt, .vtt) and lets you ask natural-language questions. Instead of a wall of search results, you get **speaker-attributed answers with timestamps** — like having a superpowered assistant who actually paid attention in every meeting. 🗣️⏱️

---

## ✨ Why Recall?

| Other RAG tools | Recall |
|---|---|
| Give you chunks of text | Give you **speaker-attributed answers** 🗣️ |
| Ignore who said what | **Detects speaker mentions** — knows Sarah said X, Alex disagreed |
| No timestamp context | Answers include **timestamps** ⏱️ |
| One-size retrieval | **Intent-aware search** — classifies queries as DECISION, ACTION_ITEM, OPINION, FACT, or FOLLOW_UP |
| Boring UX | Clean chat interface with **expandable citations** 🔍 |

---

## ⚡ Quick Start

```bash
# 1. Get the code
cd rag/recall

# 2. Python setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Frontend dependencies
cd frontend
npm install
cd ..

# 4. Environment
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

# 5. Generate sample data
python data/generate_sample_transcript.py

# 6. Launch!
uvicorn main:app --reload --port 8000 &
cd frontend
npm run dev
```

Open **http://localhost:3000** and start asking questions! 🚀

---

## 🗺️ How It Works (Plain English)

```
                  📄 Upload Transcript (.txt / .srt / .vtt)
                              │
                              ▼
              ┌──────────────────────────────┐
              │  1. Document Loader          │
              │     Parse into utterances    │
              │     (speaker + text + time)  │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼───────────────┐
              │  2. Chunker                 │
              │     Speaker-turn boundary   │
              │     → one chunk per turn     │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼───────────────┐
              │  3. Embedder                │
              │     sentence-transformers    │
              │     → vector embeddings      │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼───────────────┐
              │  4. FAISS Vector Store       │
              │     + metadata filter        │
              │     (by speaker, intent)     │
              └──────────────┬───────────────┘
                             │
     ┌───────────────────────┼──────────────────────────┐
     │                       │                          │
     │              ┌────────▼────────┐                │
     │              │  You ask:       │                │
     │              │  "What did      │                │
     │              │  Sarah propose?" │                │
     │              └────────┬────────┘                │
     │                       │                          │
     │              ┌────────▼────────┐                │
     │              │  5. Classifier  │                │
     │              │  Intent: OPINION │                │
     │              │  Speaker: Sarah │                │
     │              └────────┬────────┘                │
     │                       │                          │
     │              ┌────────▼────────┐                │
     │              │  6. RAG Chain   │                │
     │              │  Semantic search│                │
     │              │  + Claude gen   │                │
     │              │  → Answer +     │                │
     │              │    citations    │                │
     │              └────────┬────────┘                │
     │                       │                          │
     │              ┌────────▼────────┐                │
     │              │  Sarah proposed │                │
     │              │  a hybrid model │                │
     │              │  (flat base +   │                │
     │              │   usage overage)│                │
     │              │  @ 3:21 ──── 🎯 │                │
     │              └─────────────────┘                │
```

### The 6-Step Pipeline

1. **📄 Ingest** — Upload a transcript. The document loader parses TXT, SRT, or VTT into structured utterances: `{speaker, text, timestamp}`.

2. **✂️ Chunk** — Split at speaker-turn boundaries. Each chunk gets the speaker's name prepended so embeddings capture *who* spoke, not just *what* was said.

3. **🧮 Embed** — Run through `sentence-transformers/all-MiniLM-L6-v2` to get dense vector embeddings.

4. **🗂️ Store** — Vectors go into a **FAISS** index with metadata (speaker, timestamp, intent labels).

5. **🔍 Classify** — When you ask a question, it classifies the **intent** (DECISION, ACTION_ITEM, OPINION, FACT, FOLLOW_UP) and detects any **speaker mentions**.

6. **🤖 Generate** — Semantic search + optional speaker filter → Claude picks the best chunks → answer with speaker + timestamp citations.

### Intent Types

| Intent | Example |
|---|---|
| `DECISION` | "What was decided about pricing?" |
| `ACTION_ITEM` | "What do we need to do next?" |
| `OPINION` | "Who disagreed with the usage model?" |
| `FACT` | "How many customers are on enterprise?" |
| `FOLLOW_UP` | "Tell me more about the hybrid pricing" |

---

## 🎤 Sample Queries

Upload `data/q3_pricing_meeting.txt` (4 speakers, 15 utterances about SaaS pricing) and try these:

| You ask | Recall answers back |
|---|---|
| `"What did Sarah propose for pricing?"` | 🗣️ **Sarah** @ 3:21 — *"A hybrid model: flat base fee + usage overage to capture both SMB and enterprise."* |
| `"What were the action items?"` | 📋 **Alex** (by Tue): Define pricing tiers. **Mike** (by Fri): Spec out metering. **Priya** (by Wed): Draft customer comms. |
| `"Who disagreed with the usage-based model?"` | 🤨 **Alex** @ 5:47 — *"Enterprise customers might churn if they can't predict costs."* |
| `"What decisions were made?"` | ✅ Go with hybrid pricing. ✅ Market research before launch. ✅ Beta with 10 enterprise customers. |

Every answer comes with **expandable citations** so you can click through to the source chunk. No black boxes. 🔍

---

## 📁 Project Tree

```
rag/recall/
├── main.py                       # 🚀 FastAPI server
├── requirements.txt              # Python dependencies
├── .env.example                  # API keys template
├── .gitignore
├── README.md                     # You are here 🫵
├── src/
│   ├── document_loader.py        # Parse TXT/SRT/VTT → utterances
│   ├── chunker.py                # Speaker-turn boundary chunking
│   ├── embedder.py               # sentence-transformers embeddings
│   ├── vector_store.py           # FAISS index + metadata filter
│   ├── classifier.py             # Intent + speaker detection
│   ├── rag_chain.py              # LangChain retrieval + generation
│   └── models.py                 # Pydantic models
├── tests/
│   └── test_smoke.py             # 26 tests — all passing ✅
├── frontend/
│   ├── package.json              # Next.js + Tailwind
│   ├── pages/
│   │   ├── index.js              # Upload + chat UI
│   │   └── api/proxy.js          # API proxy to FastAPI
│   └── components/
│       ├── ChatPanel.jsx         # Chat interface
│       ├── FileUpload.jsx        # Drag-and-drop upload
│       └── AnswerCard.jsx        # Speaker-attributed answer card
└── data/
    ├── generate_sample_transcript.py  # 🏭 Generate test data
    └── q3_pricing_meeting.txt         # Sample: SaaS pricing meeting
```

---

## 🛠️ Build & Run

### Backend

```bash
cd rag/recall
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Frontend (separate terminal)

```bash
cd rag/recall/frontend
npm run dev
```

Open **http://localhost:3000**.

### Tests

```bash
cd rag/recall
source venv/bin/activate
python -m pytest tests/ -v
# → 26 passed ✅
```

### Generate Sample Data

```bash
source venv/bin/activate
python data/generate_sample_transcript.py
```

Generates `data/q3_pricing_meeting.txt` — a 4-speaker SaaS pricing discussion ready to query.

---

## 🧠 Tech Stack

| Layer | What |
|---|---|
| **API** | Python + FastAPI 🐍 |
| **Frontend** | Next.js + Tailwind CSS ⚛️ |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) 🧮 |
| **Vector Store** | FAISS (in-memory, local) 🗂️ |
| **LLM** | Anthropic Claude via LangChain 🤖 |
| **Chunking** | Speaker-turn boundary + speaker prepend ✂️ |
| **Intent Classifier** | Classifies queries into 5 intent types + speaker detection |
| **Tests** | pytest — 26 passing ✅ |

---

## 🤝 Contributing

PRs welcome! Here's how you can help:

- **📄 New parsers** — Add support for DOCX, audio-to-text, or other formats in `document_loader.py`
- **✂️ Better chunking** — Speaker-turn boundary is simple; semantic boundary detection would be an upgrade
- **🧠 More intents** — Add new intent types to `classifier.py` and wire them into the RAG chain
- **✅ Tests first** — Keep `test_smoke.py` green. 26 and counting! 🟢

---

## 📜 License

MIT — go build something great.

---

*Made with 🧠, 🎧, and way too many meetings transcribed manually before this existed.*