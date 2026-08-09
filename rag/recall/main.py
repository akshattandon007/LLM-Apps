"""Recall — FastAPI backend server.

Endpoints:
  POST /api/upload          — Upload a transcript file
  POST /api/ingest          — Ingest an uploaded file into the vector store
  GET  /api/upload-status   — See what's been ingested and what's waiting
  POST /api/query           — Ask a question about ingested meetings
  GET  /api/meetings         — List ingested meetings
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.chunker import chunk_utterances
from src.document_loader import load_transcript
from src.embedder import embed_chunks
from src.models import (
    AnswerResponse,
    IngestionResponse,
    QueryRequest,
    UploadResponse,
    UploadStatusResponse,
)
from src.rag_chain import build_rag_chain
from src.vector_store import VectorStore

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "index"
SAMPLE_DIR = DATA_DIR

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# ── App state ──────────────────────────────────────────────────────────────

app = FastAPI(title="Recall", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state — persists for the lifetime of the server process
vector_store: VectorStore = VectorStore(dim=384)
rag_components: dict = {}
ingested_meetings: list[dict] = []
pending_uploads: list[str] = []


def _init_rag():
    """Lazy-initialise the RAG chain once we have an API key."""
    global rag_components
    if rag_components:
        return
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # Will fail on first query, and that's fine — the endpoint returns a clear error
        return
    rag_components = build_rag_chain(vector_store, api_key=api_key)


# ── Endpoints ──────────────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a transcript file. Does NOT ingest it — call /api/ingest next."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".txt", ".srt", ".vtt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{suffix}'. Supported: .txt, .srt, .vtt",
        )

    # Save to uploads directory
    dest = UPLOAD_DIR / file.filename
    # Avoid overwrites
    counter = 1
    while dest.exists():
        stem = dest.stem.rsplit("_", 1)[0] if "_" in dest.stem else dest.stem
        dest = UPLOAD_DIR / f"{stem}_{counter}{dest.suffix}"
        counter += 1

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    pending_uploads.append(str(dest))

    return UploadResponse(
        status="uploaded",
        filename=dest.name,
        file_path=str(dest),
        message=f"Uploaded {dest.name}. Call POST /api/ingest to process it.",
    )


@app.post("/api/ingest", response_model=IngestionResponse)
def ingest(file_path: str = ""):
    """Ingest a transcript file into the vector store.

    Args:
        file_path: Path to the file. If empty, ingests the oldest pending upload.
    """
    global vector_store

    if not file_path:
        if not pending_uploads:
            raise HTTPException(status_code=400, detail="No pending uploads")
        file_path = pending_uploads.pop(0)
    else:
        if file_path in pending_uploads:
            pending_uploads.remove(file_path)

    file_path = Path(file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    # Parse
    try:
        utterances = load_transcript(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse: {e}")

    if not utterances:
        raise HTTPException(status_code=400, detail="No utterances found in file")

    meeting_title = file_path.stem.replace("_", " ").replace("-", " ").title()
    speakers = list({u.speaker for u in utterances if u.speaker != "UNKNOWN"})

    # Chunk and embed
    chunks = chunk_utterances(
        utterances,
        meeting_title=meeting_title,
        source_file=file_path.name,
    )

    texts = [c.text for c in chunks]
    embeddings = embed_chunks(texts)

    vector_store.add_chunks(chunks, embeddings)

    ingested_meetings.append({
        "title": meeting_title,
        "file": file_path.name,
        "chunks": len(chunks),
        "speakers": speakers,
    })

    _init_rag()

    return IngestionResponse(
        status="ingested",
        chunks_created=len(chunks),
        meeting_title=meeting_title,
        speakers=speakers,
        message=f"Ingested {file_path.name}: {len(chunks)} chunks from {len(speakers)} speakers.",
    )


@app.get("/api/upload-status", response_model=UploadStatusResponse)
def upload_status():
    """List ingested meetings and pending uploads."""
    return UploadStatusResponse(
        ingested=ingested_meetings,
        waiting=[str(p) for p in pending_uploads],
    )


@app.post("/api/query", response_model=AnswerResponse)
def query(request: QueryRequest):
    """Ask a question about ingested meetings."""
    _init_rag()

    if not rag_components:
        raise HTTPException(
            status_code=500,
            detail="RAG chain not initialised. Set ANTHROPIC_API_KEY in .env and restart.",
        )
    if vector_store.size == 0:
        raise HTTPException(
            status_code=400,
            detail="No meetings ingested yet. Upload and ingest a transcript first.",
        )

    try:
        result = rag_components["answer"](request.question, top_k=request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/api/meetings")
def list_meetings():
    """List all ingested meetings."""
    return {"meetings": ingested_meetings}


# ── Startup ingestion of sample data ──────────────────────────────────────

@app.on_event("startup")
def _ingest_sample_on_startup():
    """Auto-ingest any .txt sample files in the data/ directory on startup."""
    sample_files = list(DATA_DIR.glob("*.txt"))
    sample_files += list(DATA_DIR.glob("*.srt"))
    sample_files += list(DATA_DIR.glob("*.vtt"))
    for sf in sorted(sample_files):
        try:
            utterances = load_transcript(sf)
            if not utterances:
                continue
            meeting_title = sf.stem.replace("_", " ").replace("-", " ").title()
            speakers = list({u.speaker for u in utterances if u.speaker != "UNKNOWN"})
            chunks = chunk_utterances(
                utterances,
                meeting_title=meeting_title,
                source_file=sf.name,
            )
            texts = [c.text for c in chunks]
            embeddings = embed_chunks(texts)
            vector_store.add_chunks(chunks, embeddings)
            ingested_meetings.append({
                "title": meeting_title,
                "file": sf.name,
                "chunks": len(chunks),
                "speakers": speakers,
            })
        except Exception as e:
            print(f"Warning: could not ingest {sf}: {e}")

    _init_rag()
    if ingested_meetings:
        print(f"Recall ready: {len(ingested_meetings)} meetings ingested on startup.")


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)