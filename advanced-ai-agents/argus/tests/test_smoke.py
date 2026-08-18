"""Smoke tests for ARGUS — Deep Research Agent.

Uses mock clients injected via conftest.setup_mocks() — no real network calls.
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on sys.path so imports from src/ work
_proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from src.cross_reference import cross_reference
from src.extractor import extract_all
from src.models import (
    CrossReferenceResult,
    ExtractedContent,
    ReportSection,
    ResearchReport,
    SourceType,
    SubQuestion,
)
from src.planner import plan_query
from src.reporter import format_report
from src.searchers import search_all, search_web, search_arxiv, search_hn, search_blogs
from src.synthesizer import synthesize
from tests.conftest import (
    MOCK_ALL_RESULTS,
    MOCK_ARXIV_RESULTS,
    MOCK_BLOG_RESULTS,
    MOCK_EXTRACTED,
    MOCK_HN_RESULTS,
    MOCK_WEB_RESULTS,
    MockCrossReference,
    MockExtractor,
    MockPlanner,
    MockSearcher,
    MockSynthesizer,
    setup_mocks,
    teardown_mocks,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_passed = 0
_failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name} — {detail}")


def section(title: str):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_mock_planner():
    """Planner returns sub-questions when mock is injected."""
    setup_mocks()
    subs = plan_query("test query")
    teardown_mocks()
    check("returns list", isinstance(subs, list))
    check("returns SubQuestion items", all(isinstance(s, SubQuestion) for s in subs))
    check("has expected count", len(subs) == 2)


def test_planner_heuristic():
    """Planner returns heuristic sub-questions when no client is set."""
    subs = plan_query("machine learning")
    check("returns heuristic list", isinstance(subs, list))
    check("has 4 heuristic questions", len(subs) == 4)
    check("all have text", all(len(s.question) > 10 for s in subs))
    check("all have intent", all(len(s.intent) > 0 for s in subs))


def test_mock_web_search():
    """Web searcher returns mock results."""
    setup_mocks()
    results = search_web("test")
    teardown_mocks()
    check("returns list", isinstance(results, list))
    check("returns mock data", results == MOCK_WEB_RESULTS)


def test_mock_arxiv_search():
    """arXiv searcher returns mock results."""
    setup_mocks()
    results = search_arxiv("test")
    teardown_mocks()
    check("returns list", isinstance(results, list))
    check("returns mock data", results == MOCK_ARXIV_RESULTS)


def test_mock_hn_search():
    """HN searcher returns mock results."""
    setup_mocks()
    results = search_hn("test")
    teardown_mocks()
    check("returns list", isinstance(results, list))
    check("returns mock data", results == MOCK_HN_RESULTS)


def test_mock_blog_search():
    """Blog searcher returns mock results."""
    setup_mocks()
    results = search_blogs("test")
    teardown_mocks()
    check("returns list", isinstance(results, list))
    check("returns mock data", results == MOCK_BLOG_RESULTS)


def test_search_all():
    """search_all returns results from all sources."""
    setup_mocks()
    results = search_all("test")
    teardown_mocks()
    check("returns dict", isinstance(results, dict))
    for st in SourceType:
        check(f"has key {st.value}", st in results)
    check("web results match", results[SourceType.WEB] == MOCK_WEB_RESULTS)
    check("arxiv results match", results[SourceType.ARXIV] == MOCK_ARXIV_RESULTS)


def test_mock_extractor():
    """Extractor returns mock content."""
    setup_mocks()
    extracted = extract_all(MOCK_ALL_RESULTS)
    teardown_mocks()
    check("returns list", isinstance(extracted, list))
    if extracted:
        check("has ExtractedContent items",
              all(isinstance(e, ExtractedContent) for e in extracted))
        check("has content text",
              all(len(e.content) > 0 for e in extracted))


def test_cross_reference():
    """Cross-reference returns structured analysis."""
    setup_mocks()
    xref = cross_reference(MOCK_EXTRACTED)
    teardown_mocks()
    check("returns CrossReferenceResult", isinstance(xref, CrossReferenceResult))
    check("has consensus points", isinstance(xref.consensus_points, list))
    check("has contradictions", isinstance(xref.contradictions, list))
    check("has gaps", isinstance(xref.gaps, list))
    check("has source count", xref.cross_referenced_sources > 0)


def test_cross_reference_empty():
    """Cross-reference handles empty input gracefully."""
    xref = cross_reference([])
    check("returns CrossReferenceResult", isinstance(xref, CrossReferenceResult))
    check("no consensus", len(xref.consensus_points) == 0)
    check("no contradictions", len(xref.contradictions) == 0)
    check("no gaps", len(xref.gaps) == 0)
    check("count is 0", xref.cross_referenced_sources == 0)


def test_synthesize():
    """Synthesis produces a ResearchReport."""
    setup_mocks()
    subs = plan_query("test")
    results = search_all("test")
    extracted = extract_all(results)
    xref = cross_reference(extracted)
    report = synthesize("test", subs, results, extracted, xref)
    teardown_mocks()
    check("returns ResearchReport", isinstance(report, ResearchReport))
    check("has title", len(report.title) > 0)
    check("has executive summary", len(report.executive_summary) > 0)
    check("has sections", len(report.sections) > 0)
    check("has citations", len(report.citations) > 0)
    check("has sub-questions", len(report.sub_questions) > 0)


def test_synthesize_mock():
    """Synthesis with fully mocked pipeline works end-to-end."""
    mock_report = ResearchReport(
        title="Mock End-to-End Report",
        query="test",
        sub_questions=[SubQuestion(question="What?", intent="Test", priority=1)],
        executive_summary="This is a test.",
        sections=[],
        sources_count=0,
        citations=[],
    )
    setup_mocks(synthesizer=MockSynthesizer(report=mock_report))
    subs = plan_query("test")
    results = search_all("test")
    extracted = extract_all(results)
    xref = cross_reference(extracted)
    report = synthesize("test", subs, results, extracted, xref)
    teardown_mocks()
    check("title matches", report.title == "Mock End-to-End Report")
    check("exec summary matches", report.executive_summary == "This is a test.")


def test_reporter():
    """Reporter produces valid markdown."""
    report = ResearchReport(
        title="Test Report",
        query="test query",
        sub_questions=[SubQuestion(question="What is X?", intent="Background", priority=1)],
        executive_summary="Summary text.",
        sections=[],
        sources_count=2,
        citations=["[1] Test source"],
    )
    md = format_report(report)
    check("returns string", isinstance(md, str))
    check("includes title", "# Test Report" in md)
    check("includes query", "test query" in md)
    check("includes citations", "[1] Test source" in md)
    check("includes sub-questions", "What is X?" in md)
    check("has ARGUS footer", "ARGUS" in md)


def test_reporter_full():
    """Reporter handles a full report with all sections."""
    report = ResearchReport(
        title="Full Report",
        query="full query",
        sub_questions=[
            SubQuestion(question="Q1?", intent="I1", priority=1),
            SubQuestion(question="Q2?", intent="I2", priority=2),
        ],
        executive_summary="Full summary.",
        sections=[
            ReportSection(heading="Background", body="Body text.", citations=["[1]"]),
            ReportSection(heading="Results", body="More text.", citations=["[2]"]),
        ],
        cross_reference=CrossReferenceResult(
            consensus_points=["C1"],
            contradictions=[{"claim": "X vs Y", "supporting": ["X"], "challenging": ["Y"]}],
            gaps=["G1"],
            cross_referenced_sources=3,
        ),
        sources_count=3,
        citations=["[1] A", "[2] B"],
    )
    md = format_report(report)
    check("has Background section", "Background" in md)
    check("has Results section", "Results" in md)
    check("has Cross-Reference Analysis", "Cross-Reference Analysis" in md)
    check("has consensus count", "1" in md and "consensus" in md.lower())


def test_full_pipeline_mocked():
    """End-to-end pipeline with all mocks works."""
    setup_mocks()
    subs = plan_query("machine learning advances")
    results = search_all("machine learning advances")
    extracted = extract_all(results)
    xref = cross_reference(extracted)
    report = synthesize("machine learning advances", subs, results, extracted, xref)
    md = format_report(report)
    teardown_mocks()

    check("all phases produce output", bool(subs and results and extracted and xref and report))
    check("report has content", len(report.sections) > 0 or len(report.citations) > 0)
    check("markdown is non-empty", len(md) > 100)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    section("ARGUS Smoke Tests — Mock Pipeline")

    tests = [
        ("Planner — mock client", test_mock_planner),
        ("Planner — heuristic fallback", test_planner_heuristic),
        ("Searcher — web (mock)", test_mock_web_search),
        ("Searcher — arxiv (mock)", test_mock_arxiv_search),
        ("Searcher — hn (mock)", test_mock_hn_search),
        ("Searcher — blog (mock)", test_mock_blog_search),
        ("Searcher — search_all (mock)", test_search_all),
        ("Extractor — mock client", test_mock_extractor),
        ("Cross-reference — mock data", test_cross_reference),
        ("Cross-reference — empty input", test_cross_reference_empty),
        ("Synthesizer — heuristic", test_synthesize),
        ("Synthesizer — mock client", test_synthesize_mock),
        ("Reporter — minimal", test_reporter),
        ("Reporter — full report", test_reporter_full),
        ("Full pipeline — end to end mocked", test_full_pipeline_mocked),
    ]

    for name, fn in tests:
        section(name)
        try:
            fn()
        except Exception as e:
            _failed += 1
            print(f"  ERROR {name} — {e}")

    print(f"\n{'='*60}")
    print(f" Results: {_passed} passed, {_failed} failed")
    print(f"{'='*60}")
    sys.exit(1 if _failed > 0 else 0)