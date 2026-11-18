# Flow.md — JunkJudge

## Execution Trace

### Entry Point: `streamlit run app.py`

```
streamlit run app.py
  │
  ├── app.py:set_page_config()         → title, icon, layout
  ├── app.py:st.title("♻️ JunkJudge")
  ├── app.py:st.markdown(description)
  │
  ├── [Sidebar: Document Loading]
  │   ├── st.radio("Source")           → "Upload PDF(s)" or "Paste text"
  │   ├── st.file_uploader() / st.text_area()
  │   └── st.button("📥 Load Documents")
  │       │
  │       ├── [PDF path]
  │       │   ├── tempfile.NamedTemporaryFile()   → save uploaded bytes
  │       │   ├── document_loader.load_and_chunk(temp_paths)
  │       │   │   ├── fitz.open(path)             → open PDF
  │       │   │   ├── page.get_text()             → extract text per page
  │       │   │   ├── _chunk_text(text, source, page)
  │       │   │   │   ├── while pos < len(text)
  │       │   │   │   │   ├── find sentence boundary near CHUNK_SIZE
  │       │   │   │   │   ├── append chunk dict {id, text, source, page}
  │       │   │   │   │   └── pos = end - CHUNK_OVERLAP
  │       │   │   └── return list[dict]
  │       │   └── os.unlink(tmp_path)             → cleanup temp file
  │       │
  │       └── [Text path]
  │           └── document_loader.load_and_chunk_from_text({name: text})
  │               └── _chunk_text(text, source, page=1)
  │                   (same chunking logic as above)
  │
  │       └── rag_engine.RAGEngine(chunks)
  │           ├── SentenceTransformer("all-MiniLM-L6-v2")
  │           ├── model.encode([texts])           → np.array (float32)
  │           ├── faiss.IndexFlatL2(dim)
  │           └── index.add(embeddings)
  │
  ├── [Main: Q&A Interface]
  │   ├── st.text_input("What do you want to know?")
  │   ├── st.button("🔍 Ask")
  │   │   └── engine.query(question, top_k=5)
  │   │       │
  │   │       ├── engine.retrieve(question, top_k)
  │   │       │   ├── model.encode([question])    → query embedding
  │   │       │   ├── index.search(q_emb, top_k)  → [distances], [indices]
  │   │       │   └── return [{"text", "source", "page", "score"}, ...]
  │   │       │
  │   │       ├── engine._build_prompt(question, context)
  │   │       │   └── QA_SYSTEM_PROMPT + context + question
  │   │       │
  │   │       ├── engine._call_hf_inference(prompt)
  │   │       │   ├── POST https://api-inference.huggingface.co/models/...
  │   │       │   ├── urllib.request.urlopen(req, timeout=60)
  │   │       │   └── return result[0].generated_text
  │   │       │
  │   │       └── return {"answer": str, "sources": [...]}
  │   │
  │   └── st.chat_message("assistant")            → display answer + sources
  │       └── st.expander("📎 Sources")            → expandable citations
  │
  └── st.chat_input("Ask a follow-up...")         → follow-up via chat widget
      └── (same query path as above)
```

## Module Dependency Graph

```
app.py
  ├── document_loader.py
  │   └── fitz (PyMuPDF)          [external]
  └── rag_engine.py
      ├── sentence_transformers    [external]
      ├── faiss                    [external]
      └── numpy                    [external]
```

## Data Flow

```
User Uploads PDF
  │
  ▼
[PDF bytes] ──fitz──▶ [page text strings]
  │
  ▼
[_chunk_text()] ──▶ [chunk dicts: {id, text, source, page}]
  │
  ▼
[SentenceTransformer.encode()] ──▶ [float32 embeddings]
  │
  ▼
[FAISS IndexFlatL2.add()]         ◀── index ready
  │
  ┌──────────────────────────────────────────┐
  │                                          │
  ▼                                          │
User types question                         │
  │                                          │
  ▼                                          │
[SentenceTransformer.encode(question)]       │
  │                                          │
  ▼                                          │
[FAISS index.search()]  ──▶ [top-k chunks]  │
  │                                          │
  ▼                                          │
[_build_prompt(question + context)]          │
  │                                          │
  ▼                                          │
[HuggingFace Inference API]                  │
  │                                          │
  ▼                                          │
[LLM answer text]                            │
  │                                          │
  ▼                                          │
[Streamlit UI: answer + sources]  ──────────▶ (loop for follow-ups)
```

## Key Paths

| Path | Trigger | Files Touched |
|------|---------|---------------|
| **PDF upload** | User uploads PDF(s) | `app.py` → `document_loader.py` → `rag_engine.py` |
| **Text paste** | User pastes text | `app.py` → `document_loader.py` → `rag_engine.py` |
| **Ask question** | User submits query | `app.py` → `rag_engine.retrieve()` → `rag_engine._call_hf_inference()` |
| **Follow-up** | Chat input | Same as Ask, via session state |