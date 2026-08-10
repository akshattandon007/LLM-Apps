"""Section-aware chunking with medical metadata tags."""
from __future__ import annotations

import re

from src.models import Chunk, DocumentType

# Section headers commonly found in medical documents
_SECTION_HEADERS = [
    r"(?im)^(?:#+\s*)?(?:patient\s*)?history\s*(?:of\s*present\s*illness|of)?:?\s*$",
    r"(?im)^(?:#+\s*)?(?:lab\s*)?(?:results?|findings?|tests?):?\s*$",
    r"(?im)^(?:#+\s*)?(?:assessment|impression|diagnosis|plan):?\s*$",
    r"(?im)^(?:#+\s*)?(?:medications?|prescriptions?):?\s*$",
    r"(?im)^(?:#+\s*)?(?:immunizations?|vaccinations?|vaccines?):?\s*$",
    r"(?im)^(?:#+\s*)?(?:physical\s*exam|vitals?|physical):?\s*$",
    r"(?im)^(?:#+\s*)?(?:allergies?|allergic\s*reactions?):?\s*$",
    r"(?im)^(?:#+\s*)?(?:review\s*of\s*systems?|ros):?\s*$",
    r"(?im)^(?:#+\s*)?(?:summary|discharge\s*summary|hospital\s*course):?\s*$",
    r"(?im)^(?:#+\s*)?(?:family\s*history|social\s*history|past\s*medical\s*history):?\s*$",
    r"(?im)^(?:#+\s*)?(?:recommendations?|follow-up|follow\s*up):?\s*$",
]

_SECTION_LABELS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?im)^(?:#+\s*)?(?:lab\s*)?(?:results?|findings?|tests?|lipid\s*panel|metabolic\s*panel|complete\s*blood|blood\s*work):?\s*$"), "lab_results"),
    (re.compile(r"(?im)^(?:#+\s*)?(?:assessment|impression|diagnosis):?\s*$"), "assessment"),
    (re.compile(r"(?im)^(?:#+\s*)?plan:?\s*$"), "plan"),
    (re.compile(r"(?im)^(?:#+\s*)?(?:medications?|prescriptions?):?\s*$"), "medications"),
    (re.compile(r"(?im)^(?:#+\s*)?history"), "history"),
    (re.compile(r"(?im)^(?:#+\s*)?(?:immunizations?|vaccinations?|vaccines?):?\s*$"), "immunizations"),
    (re.compile(r"(?im)^(?:#+\s*)?(?:physical\s*exam|vitals?):?\s*$"), "physical_exam"),
    (re.compile(r"(?im)^(?:#+\s*)?(?:allergies?):?\s*$"), "allergies"),
    (re.compile(r"(?im)^(?:#+\s*)?(?:summary|discharge|hospital\s*course):?\s*$"), "summary"),
]


def _find_section_boundaries(text: str) -> list[tuple[int, str]]:
    """Find section header positions and labels."""
    boundaries: list[tuple[int, str]] = [(0, "header")]
    for pat, label in _SECTION_LABELS:
        for m in pat.finditer(text):
            boundaries.append((m.start(), label))
    # Deduplicate: keep first occurrence of each label, sorted by position
    seen: set[str] = set()
    unique: list[tuple[int, str]] = []
    for pos, label in sorted(boundaries, key=lambda x: x[0]):
        if label not in seen:
            seen.add(label)
            unique.append((pos, label))
    if not unique:
        unique = [(0, "header")]
    return unique


def chunk_document(
    text: str,
    doc_id: str,
    doc_type: DocumentType,
    doc_name: str = "",
    dates: list[str] | None = None,
    medications: list[str] | None = None,
    labs: list[str] | None = None,
    values: list[dict] | None = None,
    max_chars: int = 2000,
) -> list[Chunk]:
    """Split a document into section-aware chunks with metadata tags."""
    boundaries = _find_section_boundaries(text)
    chunks: list[Chunk] = []

    if not dates:
        dates = []
    if not medications:
        medications = []
    if not labs:
        labs = []
    if not values:
        values = []

    date_range = ", ".join(sorted(set(dates))) if dates else ""

    for i in range(len(boundaries)):
        start = boundaries[i][0]
        section_label = boundaries[i][1]
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        segment = text[start:end].strip()
        if not segment:
            continue

        # If segment is still too long, split by paragraphs
        if len(segment) > max_chars:
            paragraphs = segment.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) > max_chars and current:
                    chunk = Chunk(
                        text=current.strip(),
                        doc_id=doc_id,
                        doc_type=doc_type,
                        doc_name=doc_name,
                        date_range=date_range,
                        medications=medications,
                        labs=labs,
                        values=values,
                        section=section_label,
                    )
                    chunks.append(chunk)
                    current = para
                else:
                    current = current + "\n\n" + para if current else para
            if current.strip():
                chunk = Chunk(
                    text=current.strip(),
                    doc_id=doc_id,
                    doc_type=doc_type,
                    doc_name=doc_name,
                    date_range=date_range,
                    medications=medications,
                    labs=labs,
                    values=values,
                    section=section_label,
                )
                chunks.append(chunk)
        else:
            chunk = Chunk(
                text=segment,
                doc_id=doc_id,
                doc_type=doc_type,
                doc_name=doc_name,
                date_range=date_range,
                medications=medications,
                labs=labs,
                values=values,
                section=section_label,
            )
            chunks.append(chunk)

    return chunks or [
        Chunk(
            text=text[:max_chars],
            doc_id=doc_id,
            doc_type=doc_type,
            doc_name=doc_name,
            date_range=date_range,
            medications=medications,
            labs=labs,
            values=values,
            section="header",
        )
    ]