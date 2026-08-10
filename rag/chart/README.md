# 🏥 Chart — Medical Records RAG Assistant

**Your lab results, doctor's notes, and discharge summaries — searchable by meaning. Ask your medical records anything.** 🩺

---

## What it does ✨

Chart turns your pile of medical PDFs and text files into a conversational knowledge base. Upload lab reports, annual physical notes, and discharge summaries, then ask questions in plain English:

| You ask | Chart answers |
|---------|--------------|
| *"How has my LDL changed over 2 years?"* | 📈 Shows trend with dates and values from each report |
| *"What was my levothyroxine dose in 2023?"* | 💊 Finds the exact medication + dosage across all 2023 docs |
| *"When did I get my last tetanus shot?"* | 💉 Searches all vaccination records, returns the date + document |
| *"What does my latest lab report say?"* | 📋 Summarises the most recent panel with key markers |

It handles **scanned lab images** (OCR fallback), understands **temporal trends** (rising / falling / stable), and **warns you** when data is missing or conflicting — no guesswork, no hallucinations.

---

## Architecture 🏛️

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌────────────┐   ┌──────────┐
│  Ingest  │ → │  Chunk   │ → │  Embed   │ → │ Classify  │ → │  Retrieve  │ → │ Generate │
│ (PDF/TXT)│   │(section) │   │(MiniLM)  │   │ (intent)  │   │  (FAISS)   │   │  (Claude) │
└──────────┘   └──────────┘   └──────────┘   └───────────┘   └────────────┘   └──────────┘
```

### Pipeline detail

1. **📄 Ingest** — `document_loader.py` reads PDFs via PyMuPDF (text extraction) with **tesserocr OCR fallback** for scanned images. Extracts metadata: dates, lab names, medication names, values.
2. **✂️ Chunk** — `chunker.py` splits documents into sections (lab results, history, assessment...) with medical metadata tags. Respects section boundaries — doesn't split mid-table.
3. **🧬 Embed** — `embedder.py` encodes chunks with **all-MiniLM-L6-v2** (384-dim sentence embeddings). Fast, local, no cloud API needed.
4. **🏷️ Classify** — `classifier.py` classifies the query intent (keyword-based, no model required):
   - `LAB_VALUE` — "What was my HbA1c in March 2023?"
   - `MEDICATION_HISTORY` — "What medications was I on in 2022?"
   - `TEMPORAL_TREND` — "How has my LDL changed over 2 years?"
   - `VACCINATION` — "When did I get my last tetanus shot?"
   - `GENERAL_INFO` — "What does my latest lab report say?"
5. **🔍 Retrieve** — `vector_store.py` builds a **FAISS** index (cosine similarity). Searches with `top_k` results, ranks by relevance, filters by intent.
6. **🤖 Generate** — `rag_chain.py` feeds retrieved chunks + query to **Claude** (via `langchain-anthropic`) with a temporal-reasoning prompt. Falls back to local summarisation when no API key is set.

### Project structure

```
rag/chart/
├── main.py                  # 🚀 FastAPI server (port 8000)
├── src/
│   ├── document_loader.py   # PDF ingestion + OCR fallback
│   ├── chunker.py           # Section-aware chunking with medical tags
│   ├── embedder.py          # all-MiniLM-L6-v2 embeddings
│   ├── vector_store.py      # FAISS index (build/search/save/load)
│   ├── classifier.py        # Query intent classification
│   ├── rag_chain.py         # Retrieval + generation + temporal reasoning
│   └── models.py            # Pydantic request/response schemas
├── generate_sample_records.py  # 🎲 Creates test PDFs + TXT files
├── tests/
│   └── test_smoke.py        # Ingest → 3 queries → verify
├── frontend/                 # ⚛️ Next.js chat UI
└── data/                     # 📂 Runtime docs (gitignored)
```

---

## Quick Start 🚀

### Backend

```bash
# 1. Clone and enter the project
cd LLM-Apps/rag/chart

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set API key for Claude-powered answers
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
# Without a key, Chart falls back to local summarisation

# 5. Generate sample medical records
python generate_sample_records.py

# 6. Run the server
python main.py
# → Server starts at http://localhost:8000
```

### Frontend (optional)

```bash
cd frontend
npm install
npm run dev
# → UI at http://localhost:3000
```

### Smoke test

```bash
# With the server running and venv activated
python tests/test_smoke.py
```

---

## Try it out 🧪

Once the server is running, ask Chart a question:

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "How has my LDL cholesterol changed over 2 years?", "top_k": 5}'
```

You'll get back:

```json
{
  "answer": "Your LDL cholesterol has been trending upward:\n\n• **March 2023**: 130 mg/dL (borderline high)\n• **September 2023**: 145 mg/dL (high — above the 130 mg/dL threshold)\n\n⚠️ *This answer is generated from your uploaded medical records. It is not a substitute for professional medical advice.*",
  "citations": [
    {"source": "lab_results_march_2023.pdf", "relevance": 0.89},
    {"source": "lab_results_september_2023.pdf", "relevance": 0.91}
  ]
}
```

### API Endpoints

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/health` | GET | Server status + document count |
| `/ingest` | POST | Upload a single file (path) |
| `/ingest-directory` | POST | Ingest all files in a directory |
| `/query` | POST | Ask a question (returns answer + citations) |
| `/reset` | POST | Clear the vector store |

---

## Tech Stack 🛠️

| Layer | What it uses |
|-------|-------------|
| **API** | FastAPI + Uvicorn 🚀 |
| **PDF** | PyMuPDF (extract) + ReportLab (generate) 📄 |
| **OCR** | TesserOCR (scanned docs) 👁️ |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) 🧬 |
| **Vector Store** | FAISS (CPU) 🔍 |
| **LLM** | Claude via langchain-anthropic (or local fallback) 🤖 |
| **Frontend** | Next.js + React + Tailwind CSS ⚛️ |
| **Validation** | Pydantic v2 ✅ |

---

## Privacy 🔒

Chart is designed for **local use**. All data stays on your machine. No medical records ever leave your computer — the only external call is the optional Claude API for answer generation, and even that only sends the retrieved chunks + query, not your full document set.

Every answer includes a privacy notice: *"This answer is generated from your uploaded medical records. It is not a substitute for professional medical advice."*