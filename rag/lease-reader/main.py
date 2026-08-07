"""Lease Reader — FastAPI backend entry point.

Provides:
- POST /ingest  — upload & index a lease PDF
- POST /query   — ask a question about the indexed lease
- GET  /health  — health check

Run with: uvicorn main:app --reload
"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.models import IngestResponse, QueryRequest, AnswerResponse, ErrorResponse
from src.vector_store import get_store, LeaseVectorStore
from src.rag_chain import answer_question

app = FastAPI(
    title="Lease Reader API",
    description="Upload a lease PDF and ask natural-language questions about it.",
    version="0.1.0",
)

# Allow CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/ingest", response_model=IngestResponse, responses={400: {"model": ErrorResponse}})
async def ingest_pdf(file: UploadFile = File(...)):
    """Upload a lease PDF, extract text, chunk by legal domain, and index it."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save to a temp file
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Create a fresh store for this ingestion
        store = LeaseVectorStore()
        num_chunks = store.ingest_pdf(tmp_path)
        domains = store.get_domains()

        # Replace the global singleton
        # (hack: swap the module-level store)
        import src.vector_store as vs
        vs._store = store

        return IngestResponse(
            status="ok",
            num_chunks=num_chunks,
            domains_found=domains,
            message=f"Successfully indexed {num_chunks} chunks across {len(domains)} legal domains.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.post("/query", response_model=AnswerResponse, responses={400: {"model": ErrorResponse}})
async def query_lease(req: QueryRequest):
    """Ask a natural-language question about the indexed lease."""
    store = get_store()
    if store.index is None or not store.chunks:
        raise HTTPException(
            status_code=400,
            detail="No lease has been indexed yet. Upload a PDF first via POST /ingest.",
        )

    try:
        result = answer_question(req.question, top_k=req.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)