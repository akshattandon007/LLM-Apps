"""Synthesis writer — produces structured report with inline citations."""

from __future__ import annotations

import logging
from collections import defaultdict

from src.models import (
    CrossReferenceResult,
    ExtractedContent,
    ReportSection,
    ResearchReport,
    SearchResult,
    SourceType,
    SubQuestion,
)

logger = logging.getLogger(__name__)

_synthesizer_client = None


def set_synthesizer_client(client):
    global _synthesizer_client
    _synthesizer_client = client


def _get_synthesizer_client():
    return _synthesizer_client


def _build_citation_index(
    extracted: list[ExtractedContent],
) -> dict[str, int]:
    """Build a mapping from URL to citation number."""
    index: dict[str, int] = {}
    for i, content in enumerate(extracted, start=1):
        index[content.url] = i
    return index


def synthesize(
    query: str,
    sub_questions: list[SubQuestion],
    search_results: dict[SourceType, list[SearchResult]],
    extracted: list[ExtractedContent],
    cross_ref: CrossReferenceResult,
) -> ResearchReport:
    """Synthesize all research data into a structured report.

    Uses extracted content and cross-reference analysis to build
    a coherent report with inline citations.
    """
    client = _get_synthesizer_client()
    if client is not None:
        return client.synthesize(query, sub_questions, search_results, extracted, cross_ref)

    return _synthesize_heuristic(
        query, sub_questions, search_results, extracted, cross_ref,
    )


def _synthesize_heuristic(
    query: str,
    sub_questions: list[SubQuestion],
    search_results: dict[SourceType, list[SearchResult]],
    extracted: list[ExtractedContent],
    cross_ref: CrossReferenceResult,
) -> ResearchReport:
    """Heuristic synthesis — assembles findings into sections."""
    citation_index = _build_citation_index(extracted)
    all_citations: list[str] = []
    for content in extracted:
        all_citations.append(f"[{citation_index[content.url]}] {content.title} — {content.url}")

    # Build a map: source_type -> content snippets
    source_text: dict[str, list[str]] = defaultdict(list)
    for content in extracted:
        sentences = content.content.replace("\n", " ").split(". ")
        # Take first 3 substantive sentences
        taken = [s + "." for s in sentences if 30 < len(s) < 400][:3]
        source_text[content.source.value].extend(taken)

    sections = []

    # --- Background section ---
    background_items = []
    for st in ["web", "arxiv"]:
        for snippet in source_text.get(st, []):
            background_items.append(snippet)
    if background_items:
        body = "\n\n".join(background_items[:5])
        citations = []
        for content in extracted[:3]:
            idx = citation_index.get(content.url)
            if idx:
                citations.append(f"[{idx}]")
        sections.append(ReportSection(
            heading="Background & Key Facts",
            body=body,
            citations=list(set(citations)),
        ))

    # --- Current State section ---
    state_items = []
    for st in ["arxiv", "blog", "web"]:
        for snippet in source_text.get(st, []):
            state_items.append(snippet)
    if state_items:
        body = "\n\n".join(state_items[:5])
        citations = []
        for content in extracted[2:6]:
            idx = citation_index.get(content.url)
            if idx:
                citations.append(f"[{idx}]")
        sections.append(ReportSection(
            heading="Current State of Research & Development",
            body=body,
            citations=list(set(citations)),
        ))

    # --- Controversies / Debates section ---
    controversy_items = []
    if cross_ref.contradictions:
        for c in cross_ref.contradictions:
            for s in c.get("supporting", []):
                controversy_items.append(f"**Claim**: {s}")
            for c_text in c.get("challenging", []):
                controversy_items.append(f"**Counterpoint**: {c_text}")
    if not controversy_items:
        controversy_items.append(
            "No significant contradictions were identified across the reviewed sources."
        )
    sections.append(ReportSection(
        heading="Controversies & Debates",
        body="\n\n".join(controversy_items[:6]),
        citations=[],
    ))

    # --- Consensus section ---
    consensus_body = ""
    if cross_ref.consensus_points:
        consensus_body = "\n\n".join(cross_ref.consensus_points[:5])
    else:
        consensus_body = "No strong consensus signals were detected across the reviewed sources."
    sections.append(ReportSection(
        heading="Consensus & Widely Accepted Findings",
        body=consensus_body,
        citations=[],
    ))

    # --- Gaps section ---
    gaps_body = ""
    if cross_ref.gaps:
        gaps_body = "\n\n".join(f"- {g}" for g in cross_ref.gaps[:5])
    else:
        gaps_body = "No significant research gaps were explicitly flagged in the reviewed sources."
    sections.append(ReportSection(
        heading="Research Gaps & Open Questions",
        body=gaps_body,
        citations=[],
    ))

    # --- Executive summary ---
    summary_parts = [
        f"Research was conducted across {len(extracted)} sources "
        f"({len(search_results.get(SourceType.WEB, []))} web, "
        f"{len(search_results.get(SourceType.ARXIV, []))} arXiv, "
        f"{len(search_results.get(SourceType.HN, []))} HN, "
        f"{len(search_results.get(SourceType.BLOG, []))} blog)."
    ]
    if cross_ref.consensus_points:
        summary_parts.append(
            f"{len(cross_ref.consensus_points)} areas of consensus were identified."
        )
    if cross_ref.contradictions:
        summary_parts.append(
            f"{len(cross_ref.contradictions)} contradictions were flagged for further investigation."
        )
    if cross_ref.gaps:
        summary_parts.append(
            f"{len(cross_ref.gaps)} research gaps were noted."
        )

    return ResearchReport(
        title=f"Research Report: {query[:80]}",
        query=query,
        sub_questions=sub_questions,
        executive_summary=" ".join(summary_parts),
        sections=sections,
        cross_reference=cross_ref,
        sources_count=len(extracted),
        citations=all_citations,
    )