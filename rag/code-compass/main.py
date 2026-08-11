"""Code Compass — FastAPI server for codebase RAG."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.chunker import chunk_file
from src.code_loader import walk_directory
from src.embedder import Embedder
from src.models import IngestRequest, IngestResponse, QueryRequest, QueryResponse, StatusResponse
from src.rag_chain import RAGChain
from src.vector_store import VectorStore

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
INDEX_DIR = DATA_DIR / "index"

app = FastAPI(title="Code Compass", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state — initialized on demand
_embedder: Embedder | None = None
_vector_store: VectorStore | None = None
_rag_chain: RAGChain | None = None


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def _get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def _get_rag_chain() -> RAGChain:
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain(
            embedder=_get_embedder(),
            vector_store=_get_vector_store(),
        )
    return _rag_chain


@app.on_event("startup")
async def startup():
    """Load existing index on startup if available."""
    store = _get_vector_store()
    if INDEX_DIR.exists() and (INDEX_DIR / "index.faiss").exists():
        store.load(str(INDEX_DIR))


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Return server status and index info."""
    store = _get_vector_store()
    return StatusResponse(
        status="ok",
        indexed_files=len(set(c.file_path for c in store.chunks)),
        indexed_chunks=store.size,
        has_index=store.size > 0,
    )


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_directory(req: IngestRequest):
    """Ingest a codebase directory into the vector store."""
    abs_path = os.path.abspath(os.path.expanduser(req.directory_path))

    if not os.path.isdir(abs_path):
        raise HTTPException(status_code=400, detail=f"Directory not found: {abs_path}")

    files = walk_directory(abs_path, extensions=req.extensions)
    if not files:
        raise HTTPException(
            status_code=400,
            detail=f"No supported source files found in {abs_path}. "
            f"Supported: {['.py', '.js', '.ts', '.jsx', '.tsx']}",
        )

    embedder = _get_embedder()
    store = _get_vector_store()

    all_chunks = []
    for file_info in files:
        chunks = chunk_file(
            content=file_info["content"],
            file_path=file_info["relative_path"],
            language=file_info["language"],
            chunk_size=req.chunk_size,
            chunk_overlap=req.chunk_overlap,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        raise HTTPException(
            status_code=400,
            detail="No code chunks could be extracted from the source files.",
        )

    texts, embeddings = embedder.embed_chunks(all_chunks)
    store.add(all_chunks, texts, embeddings)
    store.save(str(INDEX_DIR))

    return IngestResponse(
        files_ingested=len(files),
        chunks_created=len(all_chunks),
        index_size=store.size,
        message=f"Ingested {len(files)} files, created {len(all_chunks)} chunks.",
    )


@app.post("/api/query", response_model=QueryResponse)
async def query_codebase(req: QueryRequest):
    """Query the ingested codebase."""
    store = _get_vector_store()
    if store.size == 0:
        raise HTTPException(
            status_code=400,
            detail="No codebase has been ingested yet. POST /api/ingest first.",
        )

    chain = _get_rag_chain()
    return chain.query(req.query, top_k=req.top_k)


@app.post("/api/clear")
async def clear_index():
    """Clear the vector store index."""
    store = _get_vector_store()
    store.clear()

    # Remove persisted files
    if INDEX_DIR.exists():
        import shutil

        shutil.rmtree(str(INDEX_DIR))
    INDEX_DIR.mkdir(exist_ok=True)

    return {"status": "ok", "message": "Index cleared."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
