# Chart — Medical Records RAG Assistant

Ask questions about your personal medical records. Upload lab reports, doctor's notes, and discharge summaries (PDF/TXT), then get answers with document citations and temporal trend awareness.

## Architecture

```
rag/chart/
├── main.py                  # FastAPI server (port 8000)
├── src/
│   ├── document_loader.py   # PDF ingestion (PyMuPDF) + OCR fallback (tesserocr)
│   ├── chunker.py           # Section-aware chunking with medical metadata tags
│   ├── embedder.py          # all-MiniLM-L6-v2 sentence embeddings
│   ├── vector_store.py      # FAISS index (build/search/save/load)
│   ├── classifier.py        # Query intent classification (keyword-based)
│   ├── rag_chain.py         # Retrieval + generation with temporal reasoning
│   └── models.py            # Pydantic request/response models
├── tests/
│   └── test_smoke.py        # Ingest sample records, verify 3 queries
├── frontend/                 # Next.js chat UI
└── data/                     # Runtime data (gitignored)
```

## Pipeline

1. **Ingestion**: PDF -> PyMuPDF text extraction -> OCR fallback (tesserocr) for scanned docs -> metadata extraction (dates, labs, medications, values) -> section-aware chunking -> embedding (all-MiniLM-L6-v2) -> FAISS index
2. **Query**: Intent classification (LAB_VALUE, MEDICATION_HISTORY, TEMPORAL_TREND, VACCINATION, GENERAL_INFO) -> semantic retrieval -> answer generation (Claude via langchain-anthropy, or local fallback)

## Quick Start

### Backend

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set API key for Claude-powered answers
cp .env.example .env
# Edit .env with your key

# Generate sample records
python generate_sample_records.py

# Run the server
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Smoke Test

```bash
# From the project root, with venv activated
python tests/test_smoke.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server status + document count |
| `/ingest` | POST | Upload a single file (path) |
| `/ingest-directory` | POST | Ingest all files in a directory |
| `/query` | POST | Ask a question (returns answer + citations) |
| `/reset` | POST | Clear the vector store |

### Example Query

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question": "What was my HbA1c in March 2023?", "top_k": 5}'
```

## Intent Classification

| Intent | Example Question |
|--------|-----------------|
| LAB_VALUE | "What was my HbA1c in March 2023?" |
| MEDICATION_HISTORY | "What medications was I on in 2022?" |
| TEMPORAL_TREND | "How has my LDL cholesterol changed over 2 years?" |
| VACCINATION | "When did I get my last tetanus shot?" |
| GENERAL_INFO | "What does my latest lab report say?" |

## Dependencies

- **Python**: FastAPI, uvicorn, PyMuPDF, tesserocr, Pillow, sentence-transformers, FAISS, langchain-anthropic, reportlab
- **Frontend**: Next.js, React, Tailwind CSS
- **System**: tesserocr (installed via pip — bundles its own library)

## Privacy

Chart is designed for local use. All data stays on your machine. The answer includes a privacy disclaimer: *"This answer is generated from your uploaded medical records. It is not a substitute for professional medical advice."*