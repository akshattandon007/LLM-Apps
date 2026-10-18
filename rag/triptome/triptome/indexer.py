"""Document ingestion and chunking for TripTome.

Supports PDF, .txt, and .md files. Chunks by semantic boundaries
(headers, paragraphs) with configurable overlap.
"""

import os
import re
from pathlib import Path
from typing import Iterator, Optional

from triptome.models import Document


def _split_text(text: str, source: str, chunk_size: int = 500,
                 overlap: int = 50) -> list[Document]:
    """Split text into overlapping chunks at paragraph boundaries."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks: list[Document] = []
    current_chunk: list[str] = []
    current_size = 0
    chunk_id = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_words = len(para.split())
        # If a single paragraph is larger than chunk_size, split by sentences
        if para_words > chunk_size * 1.5:
            sub_chunks = _split_paragraph(para, source, chunk_size, chunk_id)
            chunks.extend(sub_chunks)
            chunk_id += len(sub_chunks)
            current_chunk = []
            current_size = 0
            continue

        if current_size + para_words > chunk_size and current_chunk:
            text_block = '\n\n'.join(current_chunk)
            chunks.append(Document(text=text_block, source=source,
                                   chunk_id=chunk_id))
            chunk_id += 1
            # Keep overlap paragraphs from the end
            overlap_words = 0
            overlap_paras: list[str] = []
            for prev_para in reversed(current_chunk):
                pw = len(prev_para.split())
                if overlap_words + pw > overlap:
                    break
                overlap_words += pw
                overlap_paras.insert(0, prev_para)
            current_chunk = overlap_paras

        current_chunk.append(para)
        current_size = sum(len(c.split()) for c in current_chunk)

    if current_chunk:
        text_block = '\n\n'.join(current_chunk)
        chunks.append(Document(text=text_block, source=source,
                               chunk_id=chunk_id))

    return chunks


def _split_paragraph(paragraph: str, source: str,
                     chunk_size: int, start_id: int) -> list[Document]:
    """Split an oversized paragraph by sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
    chunks: list[Document] = []
    current: list[str] = []
    current_size = 0
    chunk_id = start_id

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        sw = len(sent.split())
        if current_size + sw > chunk_size and current:
            chunks.append(Document(
                text=' '.join(current), source=source, chunk_id=chunk_id))
            chunk_id += 1
            current = []
            current_size = 0
        current.append(sent)
        current_size += sw

    if current:
        chunks.append(Document(
            text=' '.join(current), source=source, chunk_id=chunk_id))

    return chunks


def _read_pdf(path: Path) -> Iterator[tuple[str, int]]:
    """Extract text from a PDF file page by page."""
    try:
        import pypdf
    except ImportError:
        raise ImportError(
            "pypdf is required to read PDF files. Install with: "
            "pip install pypdf")

    reader = pypdf.PdfReader(str(path))
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text and text.strip():
            yield text.strip(), i


def _read_text_file(path: Path) -> str:
    """Read a plain text or markdown file."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def ingest_file(path: Path, chunk_size: int = 500,
                overlap: int = 50) -> list[Document]:
    """Ingest a single file and return document chunks."""
    suffix = path.suffix.lower()
    documents: list[Document] = []

    if suffix in ('.txt', '.md'):
        text = _read_text_file(path)
        documents = _split_text(text, str(path.name), chunk_size, overlap)
    elif suffix == '.pdf':
        for page_text, page_num in _read_pdf(path):
            page_docs = _split_text(
                page_text, str(path.name), chunk_size, overlap)
            for doc in page_docs:
                doc.page = page_num
            documents.extend(page_docs)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    # Assign sequential chunk IDs after all splitting
    for i, doc in enumerate(documents):
        doc.chunk_id = i

    return documents


def ingest_directory(path: Path, chunk_size: int = 500,
                     overlap: int = 50) -> list[Document]:
    """Ingest all supported files in a directory."""
    all_docs: list[Document] = []
    supported = {'.txt', '.md', '.pdf'}

    if path.is_file():
        return ingest_file(path, chunk_size, overlap)

    for file_path in sorted(path.rglob('*')):
        if file_path.suffix.lower() in supported and file_path.is_file():
            try:
                docs = ingest_file(file_path, chunk_size, overlap)
                all_docs.extend(docs)
            except Exception as e:
                print(f"  ⚠️  Skipping {file_path.name}: {e}")

    return all_docs