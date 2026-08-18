"""Cross-reference engine — finds contradictions, consensus, and gaps."""

from __future__ import annotations

import logging
from collections import defaultdict

from src.models import (
    CrossReferenceResult,
    ExtractedContent,
    Finding,
    SourceType,
)

logger = logging.getLogger(__name__)

_crossref_client = None


def set_crossref_client(client):
    global _crossref_client
    _crossref_client = client


def _get_crossref_client():
    return _crossref_client


def _extract_findings(content: ExtractedContent) -> list[Finding]:
    """Extract discrete findings from extracted content.

    Simple sentence-splitting heuristic for the thin slice.
    """
    sentences = content.content.replace("\n", " ").split(". ")
    findings = []
    word_count = len(content.content.split())

    # Take up to 5 substantial sentences as findings
    count = 0
    for sent in sentences:
        sent = sent.strip()
        if 20 < len(sent) < 500:
            findings.append(
                Finding(
                    statement=sent + ".",
                    url=content.url,
                    source_type=content.source,
                    confidence=0.6 if word_count > 100 else 0.4,
                )
            )
            count += 1
            if count >= 5:
                break
    return findings


def cross_reference(extracted: list[ExtractedContent]) -> CrossReferenceResult:
    """Analyze extracted content for consensus, contradictions, and gaps.

    Args:
        extracted: List of extracted full-text contents from crawled sources.

    Returns:
        CrossReferenceResult with consensus points, contradictions, and gaps.
    """
    client = _get_crossref_client()
    if client is not None:
        return client.cross_reference(extracted)

    if not extracted:
        return CrossReferenceResult()

    # Extract findings from each source
    all_findings: list[Finding] = []
    for content in extracted:
        all_findings.extend(_extract_findings(content))

    # --- Consensus: findings with similar keywords across multiple sources ---
    keyword_sources: dict[str, set[str]] = defaultdict(set)
    keyword_findings: dict[str, list[str]] = defaultdict(list)

    key_terms = [
        "state of the art", "breakthrough", "significant", "important",
        "widely accepted", "consensus", "standard approach", "leading",
        "main challenge", "key limitation", "fundamental", "critical",
    ]

    for finding in all_findings:
        lower = finding.statement.lower()
        for term in key_terms:
            if term in lower:
                keyword_sources[term].add(finding.url)
                keyword_findings[term].append(finding.statement)
                break

    consensus_points = []
    for term, sources in keyword_sources.items():
        if len(sources) >= 2 and keyword_findings[term]:
            # Pick the shortest finding as the consensus statement
            best = min(keyword_findings[term], key=len)
            consensus_points.append(
                f"[{term.capitalize()}]: {best[:200]} " +
                f"(supported by {len(sources)} sources)"
            )

    # --- Contradictions: look for conflicting language ---
    contradictions = []
    positive_terms = ["effective", "successful", "beneficial", "solves", "works well"]
    negative_terms = ["ineffective", "fails", "problematic", "limitation", "drawback"]

    for term_a, term_b in [
        ("effective", "limitation"),
        ("successful", "fails"),
        ("beneficial", "drawback"),
        ("solves", "problematic"),
    ]:
        pos_findings = [
            f for f in all_findings if term_a in f.statement.lower()
        ]
        neg_findings = [
            f for f in all_findings if term_b in f.statement.lower()
        ]
        if pos_findings and neg_findings:
            contradictions.append({
                "claim": f"'{term_a}' vs '{term_b}'",
                "supporting": [f.statement[:150] for f in pos_findings[:2]],
                "challenging": [f.statement[:150] for f in neg_findings[:2]],
            })

    # --- Gaps: questions that seem unanswered ---
    gap_indicators = [
        "unclear", "not yet", "unknown", "future work", "remains to be",
        "open question", "needs further", "limited research", "not well understood",
    ]
    gaps = set()
    for finding in all_findings:
        lower = finding.statement.lower()
        for indicator in gap_indicators:
            if indicator in lower:
                gaps.add(finding.statement[:200])
                break

    return CrossReferenceResult(
        consensus_points=consensus_points,
        contradictions=contradictions,
        gaps=list(gaps),
        cross_referenced_sources=len(extracted),
    )