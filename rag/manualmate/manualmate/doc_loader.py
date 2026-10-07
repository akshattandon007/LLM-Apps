"""Document loader for ManualMate — reads PDFs and text files."""

import re
import os
from pathlib import Path
from typing import List, Tuple


def load_document(filepath: str) -> Tuple[str, str]:
    """Load text from a file. Returns (text, source_filename)."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    source = path.name
    suffix = path.suffix.lower()

    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        text = _load_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .pdf or .txt")

    if not text.strip():
        raise ValueError(f"No extractable text found in {filepath}")

    return text, source


def _load_pdf(path: Path) -> str:
    """Extract text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required for PDF support. Install: pip install pypdf")

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
    """Split text into overlapping sentence-boundary chunks.

    Args:
        text: Input text to chunk.
        chunk_size: Target characters per chunk.
        overlap: Character overlap between chunks.

    Returns:
        List of chunk strings.
    """
    if not text:
        return []

    # Split on sentence boundaries (preserving the delimiter)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    # Rejoin delimiter to its sentence
    # Actually the split above keeps the delimiter at the end of each item

    chunks = []
    current = []
    current_len = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        sent_len = len(sent)

        # If a single sentence is longer than chunk_size, split it by clauses
        if sent_len > chunk_size and not current:
            # Split long sentence by comma or semicolon
            parts = re.split(r"(?<=[,;])\s+", sent)
            sub_parts = []
            sub = []
            sub_len = 0
            for part in parts:
                part = part.strip()
                pl = len(part)
                if sub_len + pl + 1 > chunk_size and sub:
                    sub_parts.append(" ".join(sub))
                    sub = []
                    sub_len = 0
                sub.append(part)
                sub_len += pl + 1
            if sub:
                sub_parts.append(" ".join(sub))

            for sp in sub_parts:
                if sp.strip():
                    chunks.append(sp.strip())
            continue

        # If adding this sentence would exceed chunk_size, finalize current
        if current and current_len + sent_len + 1 > chunk_size:
            chunks.append(" ".join(current))
            # Keep last sentences for overlap
            overlap_text = ""
            overlap_sents = []
            ol = 0
            for s in reversed(current):
                sl = len(s)
                if ol + sl + 1 > overlap and overlap_sents:
                    break
                overlap_sents.insert(0, s)
                ol += sl + 1
            current = overlap_sents
            current_len = ol

        current.append(sent)
        current_len += sent_len + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def chunk_document(text: str, source: str, doc_id: str, chunk_size: int = 600, overlap: int = 80) -> List["Chunk"]:  # noqa: F821
    """Split a document into Chunk objects with metadata."""
    from manualmate.models import Chunk  # avoid circular import at module level

    texts = chunk_text(text, chunk_size, overlap)
    chunks = []
    char_pos = 0
    for i, t in enumerate(texts):
        # Find approximate char offset by searching in the original text
        start = text.find(t[:50], char_pos)
        if start < 0:
            start = char_pos
        end = start + len(t)
        chunks.append(Chunk(
            text=t,
            source=source,
            doc_id=doc_id,
            index=i,
            char_start=start,
            char_end=end,
        ))
        char_pos = end
    return chunks