# ♻️ JunkJudge

**Never guess at the recycling bin again.**

Upload your municipality's recycling and waste-disposal guidelines (PDF or pasted text), then ask plain-English questions. JunkJudge retrieves the exact rule from your documents and answers in plain language.

## ✨ Features

- **Upload any format** — PDF files or copy-pasted text from your city's website
- **Ask anything** — "Can I recycle pizza boxes?", "Is #5 plastic accepted?", "When is bulk pickup?"
- **Cited answers** — Every answer shows which document and page it came from
- **Fully offline retrieval** — Embedding and search run locally on your machine
- **Free LLM** — Uses HuggingFace's free Inference API (no API key required)

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

### Optional: Set a HuggingFace token (for higher rate limits)

```bash
export HF_TOKEN="your_huggingface_token"
```

Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

## 📖 Usage

1. **Load your guidelines** using the sidebar:
   - Upload PDF(s) of your city's recycling rules, OR
   - Paste text copied from your municipality's website
2. Click **📥 Load Documents**
3. Ask questions in the main panel:
   - *"Can I recycle pizza boxes?"*
   - *"What day is bulk pickup?"*
   - *"Is #5 plastic recyclable here?"*
   - *"How do I dispose of old paint?"*
4. Click **🔍 Ask** — JunkJudge retrieves the relevant rule and answers in plain English
5. Click **📎 Sources** to see which document and page the answer came from

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests cover:
- Document chunking logic (overlap, metadata, multiple sources)
- FAISS retrieval (relevance, source metadata, empty index)
- Edge cases (empty text, missing docs)

## 🏗️ Project Structure

```
junkjudge/
├── app.py                # Streamlit UI
├── document_loader.py    # PDF loading and text chunking
├── rag_engine.py         # Embedding, retrieval, and LLM query
├── requirements.txt      # Python dependencies
├── Decisions.md          # Architecture decisions with trade-offs
├── Flow.md               # Execution trace and module dependencies
├── README.md             # This file
└── tests/
    ├── __init__.py
    ├── test_loader.py    # Tests for document_loader.py
    └── test_rag.py       # Tests for rag_engine.py (retrieval only)
```

## ⚙️ How It Works

1. **Document Loading** — PyMuPDF extracts text from PDFs; text is split into 500-char overlapping chunks
2. **Embedding** — sentence-transformers (all-MiniLM-L6-v2) converts each chunk into a 384-dim vector
3. **Indexing** — FAISS builds an in-memory similarity index from the vectors
4. **Retrieval** — Your question is embedded, and FAISS finds the most relevant chunks
5. **Answering** — Context + question are sent to a free LLM (Mistral-7B via HuggingFace) for a concise answer

## 🔧 Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HF_TOKEN` | (empty) | HuggingFace API token for higher rate limits |
| `HF_QA_MODEL` | `mistralai/Mistral-7B-Instruct-v0.3` | Model to use for answering |

## 📝 License

MIT