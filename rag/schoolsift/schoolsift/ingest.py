"""Extract text from PDFs / txt / md and split it into searchable chunks."""
from __future__ import annotations

import re
from pathlib import Path

try:  # pymupdf >= 1.24 exposes both module names; prefer the new one.
    import pymupdf as fitz
except ImportError:  # pragma: no cover - older pymupdf installs
    import fitz  # type: ignore

CHUNK_MAX = 700      # max chars per indexed chunk
CHUNK_OVERLAP = 60   # sliding overlap between hard-split long chunks

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


def extract_pages(path: Path) -> list[dict]:
    """Return a list of {number, text} pages for a PDF or text file."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_pages(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    return [{"number": 1, "text": text}]


def _extract_pdf_pages(path: Path) -> list[dict]:
    doc = fitz.open(str(path))
    pages = []
    try:
        for number, page in enumerate(doc, start=1):
            pages.append({"number": number, "text": page.get_text("text")})
    finally:
        doc.close()
    return pages


def chunk_page(text: str, page_number: int) -> list[dict]:
    """Split one page's text into chunks carrying page metadata."""
    if not text or not text.strip():
        return []
    return [{"page": page_number, "text": seg} for seg in _chunk_text(text)]


def _chunk_text(text: str) -> list[str]:
    """Segment text into CHUNK_MAX-char chunks with paragraph awareness.

    Line breaks inside a paragraph are preserved (only horizontal whitespace
    is normalized) — pymupdf often separates a document's title line from the
    body with just a newline, and keeping that boundary means the title can
    never merge into the first body sentence during answering.
    """
    segments: list[str] = []
    buf = ""
    for para in _PARAGRAPH_SPLIT_RE.split(text):
        lines = [
            re.sub(r"[ \t]+", " ", line).strip()
            for line in para.splitlines()
            if line.strip()
        ]
        para = "\n".join(lines)
        if not para:
            continue
        if len(buf) + len(para) + 1 <= CHUNK_MAX:
            buf = f"{buf}\n{para}" if buf else para
            continue
        if buf:
            segments.append(buf)
            buf = ""
        if len(para) <= CHUNK_MAX:
            buf = para
        else:
            # One very long paragraph: hard-split with a sliding overlap so
            # phrases straddling the cut are still findable. The overlap
            # backstep must NOT repeat the final tail segment — once we've
            # emitted up to the end of the paragraph we are done.
            start = 0
            while start < len(para):
                end = min(start + CHUNK_MAX, len(para))
                seg = para[start:end]
                if len(seg) >= 40:
                    segments.append(seg)
                if end >= len(para):
                    break
                start = end - CHUNK_OVERLAP
    if buf:
        segments.append(buf)
    return segments


def ingest_folder(folder: Path) -> list[dict]:
    """Index every supported file under folder (recursively).

    Returns a list of doc records:
        {id, path, title, pages, chunks: [{page, text}, ...]}
    Empty-text files are skipped.
    """
    docs: list[dict] = []
    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    for path in files:
        pages = extract_pages(path)
        if not any(p["text"].strip() for p in pages):
            continue
        chunks: list[dict] = []
        for page in pages:
            chunks.extend(chunk_page(page["text"], page["number"]))
        docs.append({
            "id": len(docs),
            "path": str(path),
            "title": path.stem,
            "pages": len(pages),
            "chunks": chunks,
        })
    return docs