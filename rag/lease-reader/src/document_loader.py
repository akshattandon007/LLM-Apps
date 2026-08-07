"""PDF ingestion with PyMuPDF (fitz) and lease section detection.

Extracts text from a lease PDF while preserving section structure. It detects
section headers (e.g. "Section 4.2 — Rent Increases", "7. Pet Policy") so the
chunker can split on legal-clause boundaries rather than arbitrary character
counts.
"""

import re
from dataclasses import dataclass

import fitz  # PyMuPDF


# Regex used to spot lease-style section headers. Kept loose so we
# catch "Section 4.2", "4.2", "VII.", "7. PETS", etc.
_SECTION_HEADER_RE = re.compile(
    r"^\s*(?i:section\s+)?"
    r"(?:\d+(?:\.\d+)*|(?i:[ivxlcdm])+\.?)"
    r"[\s.\-–:]+"
    r"([A-Z][A-Za-z &'\-/]{3,})"
)


@dataclass
class RawPage:
    """One page's extracted text plus any detected section headers."""

    page_number: int
    text: str
    headers: list[str]


def extract_raw_pages(pdf_path: str) -> list[RawPage]:
    """Extract text from a PDF, page by page, detecting section headers."""
    pages: list[RawPage] = []
    doc = fitz.open(pdf_path)
    try:
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            headers = []
            if text:
                for line in text.splitlines():
                    stripped = line.strip()
                    if _SECTION_HEADER_RE.match(stripped):
                        headers.append(stripped)
            pages.append(RawPage(
                page_number=page_index,
                text=text,
                headers=headers,
            ))
    finally:
        doc.close()
    return pages


def load_lease(pdf_path: str) -> list[RawPage]:
    """Convenience wrapper: extract raw pages from a lease PDF."""
    return extract_raw_pages(pdf_path)