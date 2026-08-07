"""Legal-domain-aware chunking and tagging for lease agreements.

Splits extracted lease text on section boundaries, then tags each chunk with
a legal domain based on its header and content keywords.
"""

import re
from typing import Optional

from src.models import LEGAL_DOMAINS, Chunk
from src.document_loader import RawPage


# Mapping from keywords to legal domains. Longer/more-specific phrases first.
_DOMAIN_KEYWORDS: list[tuple[re.Pattern, str]] = [
    # Each entry: (compiled regex, domain)
    # Use \b at start only for prefix-based keywords (terminat, sublet, deposit, etc.)
    # Use full \b...\b for whole-word keywords
    (re.compile(r"\b(rent(?!al)|late\s+?fee|due\s+?date|grace\s+?period|rent\s+?increase)\b", re.I), "RENT"),
    (re.compile(r"\bterminat|early\s+?termination|holdover|abandon", re.I), "TERMINATION"),
    (re.compile(r"\b(access|enter|entry|inspect|show\s+?unit|landlord\s+?right)\b", re.I), "ACCESS"),
    (re.compile(r"\b(maintenance|repair|fix|damage|upkeep|pest\s+?control|habitability)\b", re.I), "MAINTENANCE"),
    (re.compile(r"\b(pet|pets|animal|animals|dog|dogs|cat|cats|service\s+?animal|esa|emotional\s+?support)\b", re.I), "PETS"),
    (re.compile(r"\bsublet|sublease|assign(ment)?\b", re.I), "SUBLETTING"),
    (re.compile(r"\b(deposit|security\s+?deposit|refund|deduction|damage\s+?deposit)\b", re.I), "DEPOSIT"),
    (re.compile(r"\b(utilit|electric|water|gas|internet|trash|sewer|bill)\b", re.I), "UTILITIES"),
]


def _classify_domain(header: str, text: str) -> str:
    """Classify a chunk's legal domain by examining header then full text.

    Priority: header-based match > text-based match > GENERAL.
    This prevents sections like "SECURITY DEPOSIT" from being classified as
    RENT just because the text mentions "one month's rent".
    """
    # 1. Check the header FIRST — higher weight
    for pattern, domain in _DOMAIN_KEYWORDS:
        if pattern.search(header):
            return domain

    # 2. Fall back to text
    for pattern, domain in _DOMAIN_KEYWORDS:
        if pattern.search(text):
            return domain

    return "GENERAL"


def _extract_clause_ref(header: str) -> str:
    """Extract the clause/section reference from a header line."""
    m = re.match(
        r"^\s*(?:section\s+)?(\d+(?:\.\d+)*|[ivxlcdm]+\.?)",
        header,
        re.I,
    )
    if m:
        return m.group(1).rstrip(".").upper()
    return ""


def chunk_pages(pages: list[RawPage]) -> list[Chunk]:
    """Split raw pages into legal-domain-tagged chunks.

    Each chunk corresponds to a section or sub-section. Pages without clear
    section headers are split on paragraph boundaries (> 3 sentences or 500
    chars).
    """
    chunks: list[Chunk] = []
    current_header = "Preamble"
    current_text: list[str] = []
    current_page = 1

    def _flush():
        nonlocal current_text, current_header
        if not current_text:
            return
        text = " ".join(current_text).strip()
        if not text:
            return
        domain = _classify_domain(current_header, text)
        clause_ref = _extract_clause_ref(current_header) or current_header
        chunks.append(Chunk(
            text=text,
            domain=domain,
            clause_ref=clause_ref,
            page_number=current_page,
        ))
        current_text = []

    for page in pages:
        current_page = page.page_number
        lines = page.text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check if this line looks like a section header
            header_match = re.match(
                r"^\s*(?:section\s+)?(\d+(?:\.\d+)*)\s*[.\-–:]\s*(.+)",
                line, re.I,
            )
            if header_match:
                _flush()
                current_header = line
                # Skip "Section N" standalone lines
                if len(line) < 80:
                    i += 1
                    continue
                else:
                    current_text.append(line)
            else:
                current_text.append(line)
            i += 1

    _flush()
    return chunks


def chunk_and_tag(pages: list[RawPage]) -> list[Chunk]:
    """High-level pipeline: extract pages, chunk, tag, return Chunks."""
    return chunk_pages(pages)