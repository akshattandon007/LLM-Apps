"""
document_loader.py — Load, chunk, and index municipal waste/recycling PDFs.

Public API:
    load_and_chunk(pdf_paths: list[str]) -> list[dict]
        Returns [{"id": int, "text": str, "source": str, "page": int}, ...]

    load_and_chunk_from_text(texts: dict[str, str]) -> list[dict]
        Same output but from raw text strings keyed by source name.
"""

import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


CHUNK_SIZE = 500       # target characters per chunk
CHUNK_OVERLAP = 80     # overlap between consecutive chunks


def _chunk_text(text: str, source: str, page: int, start_id: int = 0) -> list[dict]:
    """Split *text* into overlapping chunks, each tagged with metadata."""
    chunks = []
    idx = start_id
    pos = 0
    while pos < len(text):
        end = min(pos + CHUNK_SIZE, len(text))
        # try to break at a sentence boundary near the target size
        if end < len(text):
            # look back for sentence end within the overlap window
            search_start = max(pos, end - CHUNK_OVERLAP - 20)
            candidate = max(
                text.rfind(". ", search_start, end),
                text.rfind("?\n", search_start, end),
                text.rfind("!\n", search_start, end),
                text.rfind("\n\n", search_start, end),
            )
            if candidate > search_start:
                end = candidate + 1  # include the period/newline

        segment = text[pos:end].strip()
        if segment:
            chunks.append({
                "id": idx,
                "text": segment,
                "source": source,
                "page": page,
            })
            idx += 1

        # advance position — overlap so we don't cut mid-sentence
        next_start = end - CHUNK_OVERLAP if end < len(text) else len(text)
        pos = max(pos + 1, next_start)  # always move forward at least 1

    return chunks


def load_and_chunk(pdf_paths: list[str]) -> list[dict]:
    """Load one or more PDF files, extract text, and return chunks."""
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required. Run: pip install PyMuPDF")

    all_chunks: list[dict] = []
    chunk_id = 0

    for path in pdf_paths:
        p = Path(path)
        if not p.exists():
            continue
        doc = fitz.open(str(p))
        full_text_pages: list[str] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            full_text_pages.append(text)

        # Chunk each page separately
        for page_num, text in enumerate(full_text_pages):
            if not text.strip():
                continue
            page_chunks = _chunk_text(text, p.name, page_num + 1, chunk_id)
            all_chunks.extend(page_chunks)
            chunk_id += len(page_chunks)

        doc.close()

    return all_chunks


def load_and_chunk_from_text(texts: dict[str, str]) -> list[dict]:
    """Load chunks from raw text strings keyed by source name.
    
    Useful for tests or when text is already extracted.
    """
    all_chunks: list[dict] = []
    chunk_id = 0

    for source_name, text in texts.items():
        page_chunks = _chunk_text(text, source_name, 1, chunk_id)
        all_chunks.extend(page_chunks)
        chunk_id += len(page_chunks)

    return all_chunks