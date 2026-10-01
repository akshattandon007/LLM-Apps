"""Document loader for GardenGuide — loads and parses gardening documents."""

import os
import re
from pathlib import Path
from typing import List


def load_text(filepath: str) -> str:
    """Load a plain .txt file and return its content."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def try_load_pdf(filepath: str) -> str | None:
    """Try to load a PDF using available libraries. Returns None if none available."""
    try:
        import pymupdf  # PyMuPDF

        doc = pymupdf.open(filepath)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip() or None
    except ImportError:
        pass

    try:
        import pdfplumber

        with pdfplumber.open(filepath) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip() or None
    except ImportError:
        pass

    # Try pdftotext CLI
    import subprocess, tempfile

    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_name = tmp.name
        subprocess.run(
            ["pdftotext", filepath, tmp_name],
            capture_output=True, timeout=30,
        )
        with open(tmp_name, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        os.unlink(tmp_name)
        return text.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    return None


SUPPORTED_EXTENSIONS = {".txt": load_text, ".md": load_text}


def load_document(filepath: str) -> str:
    """Load a document (txt, md, or pdf) and return its text content.

    Raises ValueError if the format is unsupported or the file is empty.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {filepath}")
    if not path.is_file():
        raise ValueError(f"Not a file: {filepath}")

    ext = path.suffix.lower()
    loader = SUPPORTED_EXTENSIONS.get(ext)

    if loader:
        text = loader(filepath)
    elif ext == ".pdf":
        text = try_load_pdf(filepath)
        if text is None:
            # Register for future calls
            SUPPORTED_EXTENSIONS[ext] = lambda fp: try_load_pdf(fp) or ""
            raise ValueError(
                "PDF support requires PyMuPDF or pdfplumber.\n"
                "  pip install pymupdf\n"
                "  # or: pip install pdfplumber"
            )
        SUPPORTED_EXTENSIONS[ext] = lambda fp: try_load_pdf(fp) or ""
    else:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    text = text.strip()
    if not text:
        raise ValueError(f"Document is empty: {filepath}")

    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks at sentence boundaries.

    Args:
        text: The text to chunk.
        chunk_size: Target size in characters per chunk.
        overlap: Overlap between chunks in characters.

    Returns:
        List of text chunks.
    """
    # Split on sentence endings
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        sent_len = len(sentence)
        if current_len + sent_len > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)

            # Keep overlap: re-add last sentences that fit within overlap
            overlap_sentences = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s)
                else:
                    break

            current_chunk = overlap_sentences
            current_len = overlap_len

        current_chunk.append(sentence)
        current_len += sent_len

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text]