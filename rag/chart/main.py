"""Chart RAG — FastAPI server entry point."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.chunker import chunk_document
from src.document_loader import load_document
from src.embedder import embed_texts
from src.models import (
    DocumentType,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from src.rag_chain import answer_question
from src.vector_store import VectorStore

load_dotenv()

app = FastAPI(title="Chart — Medical Records RAG", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
vector_store = VectorStore(index_path="/tmp/chart-faiss.index")
api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")


def _ingest_file(file_path: str) -> IngestResponse:
    """Ingest a single file into the vector store."""
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    ext = path_obj.suffix.lower()
    if ext not in (".pdf", ".txt", ".jpg", ".jpeg", ".png"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    doc = load_document(file_path)
    doc_id = str(uuid.uuid4())

    chunks = chunk_document(
        text=doc["text"],
        doc_id=doc_id,
        doc_type=doc["doc_type"],
        doc_name=doc["doc_name"],
        dates=doc["dates"],
        medications=doc["medications"],
        labs=doc["labs"],
        values=doc["values"],
    )

    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)
    vector_store.add(embeddings, chunks)
    vector_store.save()

    return IngestResponse(
        doc_id=doc_id,
        doc_name=doc["doc_name"],
        doc_type=doc["doc_type"],
        chunk_count=len(chunks),
        message=f"Ingested {doc['doc_name']} ({doc['doc_type'].value}) — {len(chunks)} chunks.",
    )


@app.on_event("startup")
async def startup():
    vector_store.load()


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        documents_loaded=vector_store.count,
        chunks_indexed=vector_store.count,
        model_loaded=True,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    return _ingest_file(req.file_path)


@app.post("/ingest-directory", response_model=list[IngestResponse])
async def ingest_directory(directory: str):
    path = Path(directory)
    if not path.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory}")
    results: list[IngestResponse] = []
    for f in sorted(path.iterdir()):
        if f.suffix.lower() in (".pdf", ".txt", ".jpg", ".jpeg", ".png"):
            try:
                result = _ingest_file(str(f))
                results.append(result)
            except Exception as e:
                results.append(
                    IngestResponse(
                        doc_id="error",
                        doc_name=f.name,
                        doc_type=DocumentType.OTHER,
                        chunk_count=0,
                        message=f"Error: {e}",
                    )
                )
    return results


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    global api_key
    return answer_question(
        question=req.question,
        vector_store=vector_store,
        top_k=req.top_k,
        api_key=api_key,
    )


@app.post("/reset")
async def reset():
    vector_store.clear()
    vector_store.save()
    return {"message": "Vector store cleared."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)