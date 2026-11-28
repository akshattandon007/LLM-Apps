"""Pydantic and dataclass models for MintDocs."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class FilingMetadata:
    """Metadata for a single SEC filing."""

    company_name: str
    ticker: str
    cik: str
    filing_type: str  # "10-K" or "10-Q"
    filing_date: date
    accession_number: str
    primary_doc: str


@dataclass
class Chunk:
    """A single section-level chunk from a filing."""

    section_header: str
    section_text: str
    metadata: FilingMetadata

    def to_dict(self) -> dict:
        return {
            "section_header": self.section_header,
            "section_text": self.section_text,
            "company_name": self.metadata.company_name,
            "ticker": self.metadata.ticker,
            "cik": self.metadata.cik,
            "filing_type": self.metadata.filing_type,
            "filing_date": self.metadata.filing_date.isoformat(),
            "accession_number": self.metadata.accession_number,
            "primary_doc": self.metadata.primary_doc,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        return cls(
            section_header=d["section_header"],
            section_text=d["section_text"],
            metadata=FilingMetadata(
                company_name=d["company_name"],
                ticker=d["ticker"],
                cik=d["cik"],
                filing_type=d["filing_type"],
                filing_date=date.fromisoformat(d["filing_date"]),
                accession_number=d["accession_number"],
                primary_doc=d["primary_doc"],
            ),
        )


@dataclass
class QueryResult:
    """Result of a single query against the index."""

    answer: str
    sources: list[Chunk] = field(default_factory=list)

    def format(self) -> str:
        lines = [f"Answer: {self.answer}", "", "Sources:"]
        for i, chunk in enumerate(self.sources, 1):
            meta = chunk.metadata
            lines.append(
                f"\n  {i}. {meta.company_name} {meta.filing_type} "
                f"({meta.filing_date}), {chunk.section_header}"
            )
            # Show a preview of the source text
            preview = chunk.section_text[:200].replace("\n", " ")
            if len(chunk.section_text) > 200:
                preview += "..."
            lines.append(f"     \"{preview}\"")
        return "\n".join(lines)