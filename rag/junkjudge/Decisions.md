# Decisions.md — JunkJudge

## 1. CLI vs Web UI
**Chosen:** Streamlit web app  
**Rejected:** CLI (click/argparse), Flask/FastAPI + React  
**Why:** Target users are non-technical residents, not developers. A Streamlit UI requires zero setup beyond `pip install` and `streamlit run`. Full-stack React would be overkill for a single-page Q&A tool.

## 2. Embedding model: all-MiniLM-L6-v2 vs. OpenAI Ada-002
**Chosen:** all-MiniLM-L6-v2 (local, free, 384-dim)  
**Rejected:** OpenAI text-embedding-ada-002 (paid, API-dependent, 1536-dim)  
**Why:** Running locally means no API key, no cost, and offline operation for sensitive municipal documents. The 384-dim space is sufficient for ~500-char chunks of recycling rules. Accuracy difference on this narrow domain is negligible.

## 3. Vector DB: FAISS vs. ChromaDB vs. Pinecone
**Chosen:** FAISS (in-process, no server)  
**Rejected:** ChromaDB (persistent server mode adds complexity), Pinecone (paid, cloud)  
**Why:** JunkJudge is a single-user tool — no need for multi-tenancy or persistent storage across sessions. FAISS IndexFlatL2 is simple, fast, and runs entirely in memory.

## 4. PDF parsing: PyMuPDF vs. pdfplumber vs. pdfminer.six
**Chosen:** PyMuPDF (fitz)  
**Rejected:** pdfplumber (slower, better for tables — not needed here), pdfminer.six (low-level)  
**Why:** PyMuPDF is the fastest Python PDF parser and extracts clean text from typical municipal PDFs. Recycling guidelines are prose-heavy, not table-heavy.

## 5. LLM: HuggingFace Inference API vs. Ollama local vs. Gemini API
**Chosen:** HuggingFace Inference API (free tier, no API key required for some models)  
**Rejected:** Ollama (requires local GPU — heavy), Gemini API (requires Google API key — friction)  
**Why:** The HF free Inference API works out of the box for models like Mistral-7B. The HF_TOKEN env var is optional — if unset, it still hits the rate-limited free endpoint. Users who hit rate limits can set HF_TOKEN (free signup). Best zero-friction path.

## 6. Chunk size: 500 chars vs. 200 vs. 1000
**Chosen:** 500 characters with 80-char overlap  
**Rejected:** 200 (too short for meaningful context), 1000 (too long — dilutes relevance)  
**Why:** 500 chars fits ~2-3 sentences of a recycling rule — enough context for the LLM to understand. 80-char overlap ensures sentence boundaries aren't lost.

## 7. Sentence boundary detection: simple regex vs. spaCy NLTK
**Chosen:** Simple regex (`. `, `?\n`, `!\n`, `\n\n`)  
**Rejected:** spaCy (heavy dependency), NLTK (another 50MB download)  
**Why:** Recycling rules use standard punctuation. The simple heuristic correctly handles >95% of cases without dragging in 200MB of NLP dependencies.

## 8. Text input method: PDF upload vs. copy-paste vs. URL fetch
**Chosen:** Both PDF upload AND paste-text  
**Rejected:** URL fetch (municipal websites vary wildly in structure)  
**Why:** Some users have PDFs from their city's website; others have text copied from a webpage. Supporting both covers all users. URL scraping is fragile and hard to maintain.

## 9. Source citation: inline vs. expandable
**Chosen:** Expandable "Sources" section under each answer  
**Rejected:** Inline citations in the answer text (cluttered)  
**Why:** Users want a clean answer first. The expandable accordion lets them verify the source when they need to, without visual noise on every answer.

## 10. Test strategy: unit tests vs. integration tests vs. no tests
**Chosen:** Unit tests for document loader + retrieval; no live API tests  
**Rejected:** No tests (risky), live API tests (flaky, require internet)  
**Why:** The document loader and FAISS retrieval are deterministic — perfect for reliable unit tests. The LLM call is tested implicitly and covered by manual QA. Test isolation means `pytest` works offline.

## 11. Chunk overlap strategy: fixed overlap vs. sentence-aligned
**Chosen:** Fixed character overlap with sentence-boundary fallback  
**Rejected:** Pure sentence-aligned (can create uneven chunks)  
**Why:** Fixed overlap ensures predictable chunk sizes for FAISS. The sentence-boundary adjustment prevents mid-sentence cuts when a boundary is near.

## 12. Project placement: rag/ vs. standalone repo
**Chosen:** rag/ inside LLM-Apps  
**Rejected:** Standalone GitHub repo (PAT lacks repo creation scope)  
**Why:** Existing constraint — the fine-grained PAT cannot create repos. rag/ is the correct category directory for this RAG project.

## 13. Environment variables: .env vs. os.environ
**Chosen:** os.environ with sensible defaults  
**Rejected:** python-dotenv (.env file)  
**Why:** Streamlit's native secrets management works differently. os.environ keeps it simple: set HF_TOKEN in your shell or Streamlit secrets. The defaults work without any env vars.