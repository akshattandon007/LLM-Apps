"""Chunk SEC filings by section headers."""

import re
from typing import Iterator

from .models import Chunk, FilingMetadata

# Pattern for Item sections in SEC filings (10-K and 10-Q)
# Matches "Item 1.", "Item 1A.", "Item 1B.", "Item 7.", "Item 7A.", etc.
# Also supports "Item 1 — Business" style with em dash
SECTION_PATTERN = re.compile(
    r"(?mi)^Item\s+(\d+[A-Za-z]?)\.?\s*(?:—|–|-|\.)?\s*(.*?)$"
)

# Sections that are purely administrative — skip these
SKIP_SECTIONS = {
    "Reserved",
    "None",
    "Not applicable",
    "Not Applicable",
}

# Minimum chunk character length to keep
MIN_CHUNK_LENGTH = 30


def chunk_filing(text: str, metadata: FilingMetadata) -> list[Chunk]:
    """Split a filing text into section-level chunks.

    Uses Item headers as section boundaries. Each chunk gets its own
    FilingMetadata for provenance.
    """
    matches = list(SECTION_PATTERN.finditer(text))
    chunks: list[Chunk] = []

    if not matches:
        # No section headers found — return entire text as one chunk
        if len(text.strip()) >= MIN_CHUNK_LENGTH:
            chunks.append(
                Chunk(
                    section_header="Full Filing",
                    section_text=text.strip(),
                    metadata=metadata,
                )
            )
        return chunks

    for i, match in enumerate(matches):
        section_number = match.group(1)  # e.g. "1", "1A", "7"
        section_title = match.group(2).strip()  # e.g. "Business", "Risk Factors"
        section_start = match.end()

        # Determine section end (next match or end of text)
        if i + 1 < len(matches):
            section_end = matches[i + 1].start()
        else:
            section_end = len(text)

        section_text = text[section_start:section_end].strip()

        # Build the full header for display
        header = f"Item {section_number}"
        if section_title:
            header += f": {section_title}"

        # Skip purely administrative sections with no substantive content
        title_lower = section_title.lower()
        if title_lower in {s.lower() for s in SKIP_SECTIONS}:
            continue

        # Skip placeholder or empty sections
        if len(section_text) < MIN_CHUNK_LENGTH:
            continue

        chunks.append(
            Chunk(
                section_header=header,
                section_text=section_text,
                metadata=metadata,
            )
        )

    return chunks


def chunk_filings(
    texts: list[tuple[str, FilingMetadata]],
) -> list[Chunk]:
    """Chunk multiple filings at once.

    Args:
        texts: List of (filing_text, metadata) tuples.

    Returns:
        Flat list of all chunks across all filings.
    """
    all_chunks: list[Chunk] = []
    for text, metadata in texts:
        all_chunks.extend(chunk_filing(text, metadata))
    return all_chunks