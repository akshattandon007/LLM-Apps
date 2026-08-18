"""Fixtures and mock clients for ARGUS tests."""

from __future__ import annotations

from typing import Optional

from src.cross_reference import set_crossref_client
from src.extractor import set_extractor_client
from src.models import (
    CrossReferenceResult,
    ExtractedContent,
    Finding,
    ReportSection,
    ResearchReport,
    SearchResult,
    SourceType,
    SubQuestion,
)
from src.planner import set_client as set_planner_client
from src.searchers import (
    set_arxiv_client,
    set_blog_client,
    set_hn_client,
    set_web_client,
)
from src.synthesizer import set_synthesizer_client


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

MOCK_WEB_RESULTS = [
    SearchResult(
        title="What is Machine Learning? A Comprehensive Guide",
        url="https://example.com/ml-guide",
        snippet="Machine learning is a subset of artificial intelligence...",
        source=SourceType.WEB,
        source_name="example.com",
    ),
    SearchResult(
        title="Deep Learning Breakthroughs in 2025",
        url="https://example.com/dl-2025",
        snippet="Recent breakthroughs in deep learning include transformer architectures...",
        source=SourceType.WEB,
        source_name="example.com",
    ),
]

MOCK_ARXIV_RESULTS = [
    SearchResult(
        title="Attention Is All You Need",
        url="https://arxiv.org/abs/1706.03762",
        snippet="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        source=SourceType.ARXIV,
        source_name="arXiv",
        published="2017-06-12",
    ),
    SearchResult(
        title="Large Language Models: A Survey",
        url="https://arxiv.org/abs/2401.00001",
        snippet="This survey covers recent advances in large language models...",
        source=SourceType.ARXIV,
        source_name="arXiv",
        published="2024-01-01",
    ),
]

MOCK_HN_RESULTS = [
    SearchResult(
        title="Show HN: A new machine learning framework",
        url="https://news.ycombinator.com/item?id=12345",
        snippet="I built a new ML framework that makes training 10x faster...",
        source=SourceType.HN,
        source_name="Hacker News",
        published="2025-01-15",
    ),
]

MOCK_BLOG_RESULTS = [
    SearchResult(
        title="The State of AI in 2025",
        url="https://blog.example.com/ai-2025",
        snippet="A deep dive into the state of AI across industries...",
        source=SourceType.BLOG,
        source_name="blog.example.com",
    ),
]

MOCK_ALL_RESULTS = {
    SourceType.WEB: MOCK_WEB_RESULTS,
    SourceType.ARXIV: MOCK_ARXIV_RESULTS,
    SourceType.HN: MOCK_HN_RESULTS,
    SourceType.BLOG: MOCK_BLOG_RESULTS,
}

MOCK_EXTRACTED = [
    ExtractedContent(
        url="https://example.com/ml-guide",
        title="What is Machine Learning? A Comprehensive Guide",
        content=(
            "Machine learning is a subset of artificial intelligence that enables systems to learn "
            "from data. It has become a widely accepted approach in modern computing. "
            "The main challenge in machine learning is data quality and quantity. "
            "Future work remains to be done on interpretability of deep models. "
            "This approach is widely accepted by the research community."
        ),
        source=SourceType.WEB,
        word_count=50,
    ),
    ExtractedContent(
        url="https://arxiv.org/abs/1706.03762",
        title="Attention Is All You Need",
        content=(
            "The dominant sequence transduction models are based on complex recurrent or "
            "convolutional neural networks that include an encoder and a decoder. "
            "The Transformer architecture is a significant breakthrough in sequence modeling. "
            "However, the effectiveness of these models depends on large amounts of training data. "
            "A key limitation is the computational cost of self-attention. "
            "It remains unclear whether attention alone is sufficient for all sequence tasks."
        ),
        source=SourceType.ARXIV,
        word_count=60,
    ),
]


# ---------------------------------------------------------------------------
# Mock client classes (callable objects for injection)
# ---------------------------------------------------------------------------

class MockPlanner:
    """Mock planner that returns predefined sub-questions."""

    def __init__(self, sub_questions: Optional[list[SubQuestion]] = None):
        self.sub_questions = sub_questions or [
            SubQuestion(question="What is ML?", intent="Background", priority=1),
            SubQuestion(question="Latest ML advances?", intent="Survey", priority=2),
        ]

    def plan_query(self, query: str) -> list[SubQuestion]:
        return self.sub_questions


class MockSearcher:
    """Mock searcher that returns predefined results."""

    def __init__(self, results: Optional[list[SearchResult]] = None):
        self.results = results or []

    def search(self, query: str, source: SourceType) -> list[SearchResult]:
        return self.results


class MockExtractor:
    """Mock extractor that returns predefined extracted content."""

    def __init__(self, extracted: Optional[list[ExtractedContent]] = None):
        self.extracted = extracted or MOCK_EXTRACTED

    def extract(self, url: str, source_type: SourceType) -> Optional[ExtractedContent]:
        for e in self.extracted:
            if e.url == url:
                return e
        return None


class MockCrossReference:
    """Mock cross-referencer that returns a predefined result."""

    def __init__(self, result: Optional[CrossReferenceResult] = None):
        self.result = result or CrossReferenceResult(
            consensus_points=[
                "Machine learning is widely accepted in computing.",
                "Transformer architectures represent a significant breakthrough.",
            ],
            contradictions=[
                {
                    "claim": "'effective' vs 'limitation'",
                    "supporting": ["Transformer architectures are effective."],
                    "challenging": ["Self-attention has computational limitations."],
                }
            ],
            gaps=["Interpretability of deep models remains not well understood."],
            cross_referenced_sources=2,
        )

    def cross_reference(self, extracted: list[ExtractedContent]) -> CrossReferenceResult:
        return self.result


class MockSynthesizer:
    """Mock synthesizer that returns a predefined report."""

    def __init__(self, report: Optional[ResearchReport] = None):
        self.report = report or ResearchReport(
            title="Mock Report",
            query="test query",
            sub_questions=[
                SubQuestion(question="What is ML?", intent="Background", priority=1),
            ],
            executive_summary="Mock summary.",
            sections=[
                ReportSection(heading="Background", body="Mock body.", citations=["[1]"]),
            ],
            sources_count=2,
            citations=["[1] Mock citation"],
        )

    def synthesize(self, query, sub_questions, search_results, extracted, cross_ref):
        return self.report


# ---------------------------------------------------------------------------
# Fixture setup / teardown helpers
# ---------------------------------------------------------------------------

_mock_clients = {}


def setup_mocks(
    planner: Optional[MockPlanner] = None,
    web: Optional[MockSearcher] = None,
    arxiv: Optional[MockSearcher] = None,
    hn: Optional[MockSearcher] = None,
    blog: Optional[MockSearcher] = None,
    extractor: Optional[MockExtractor] = None,
    crossref: Optional[MockCrossReference] = None,
    synthesizer: Optional[MockSynthesizer] = None,
):
    """Inject mock clients into all ARGUS modules."""
    set_planner_client(planner or MockPlanner())
    set_web_client(web or MockSearcher(MOCK_WEB_RESULTS))
    set_arxiv_client(arxiv or MockSearcher(MOCK_ARXIV_RESULTS))
    set_hn_client(hn or MockSearcher(MOCK_HN_RESULTS))
    set_blog_client(blog or MockSearcher(MOCK_BLOG_RESULTS))
    set_extractor_client(extractor or MockExtractor())
    set_crossref_client(crossref or MockCrossReference())
    set_synthesizer_client(synthesizer or MockSynthesizer())


def teardown_mocks():
    """Reset all mock clients to None."""
    set_planner_client(None)
    set_web_client(None)
    set_arxiv_client(None)
    set_hn_client(None)
    set_blog_client(None)
    set_extractor_client(None)
    set_crossref_client(None)
    set_synthesizer_client(None)