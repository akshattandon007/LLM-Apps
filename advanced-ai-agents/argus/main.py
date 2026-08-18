"""ARGUS — Deep Research Agent CLI entry point.

Usage:
    python main.py "your research question"
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.cross_reference import cross_reference
from src.extractor import extract_all
from src.models import SourceType
from src.planner import plan_query
from src.reporter import format_report
from src.searchers import search_all
from src.synthesizer import synthesize

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("argus")


def main():
    parser = argparse.ArgumentParser(
        description="ARGUS — Deep Research Agent. Answer any question with a cited research report."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Research question to investigate",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=5,
        help="Max search results per source (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write report to file instead of stdout",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("argus").setLevel(logging.DEBUG)

    query = args.query
    if not query:
        query = input("Research question: ").strip()
        if not query:
            print("No query provided. Exiting.")
            sys.exit(1)

    logger.info("Starting research on: %s", query)

    # Step 1: Plan — decompose into sub-questions
    logger.info("Phase 1/5: Planning research sub-questions...")
    sub_questions = plan_query(query)
    for sq in sub_questions:
        logger.info("  Q: %s", sq.question)

    # Step 2: Search — parallel search across all sources
    logger.info("Phase 2/5: Searching across web, arXiv, HN, blogs...")
    search_results = search_all(query, max_per_source=args.max_per_source)
    total_results = sum(len(v) for v in search_results.values())
    logger.info("  Found %d results total", total_results)
    for st, results in search_results.items():
        logger.info("  %s: %d results", st.value, len(results))

    # Step 3: Extract — crawl and extract full text
    logger.info("Phase 3/5: Extracting content from sources...")
    extracted = extract_all(search_results, max_per_type=3)
    logger.info("  Extracted %d full-text pages", len(extracted))

    # Step 4: Cross-reference — find contradictions, consensus, gaps
    logger.info("Phase 4/5: Cross-referencing findings...")
    cross_ref = cross_reference(extracted)
    logger.info("  Consensus: %d | Contradictions: %d | Gaps: %d",
                len(cross_ref.consensus_points),
                len(cross_ref.contradictions),
                len(cross_ref.gaps))

    # Step 5: Synthesize — write structured report
    logger.info("Phase 5/5: Writing report...")
    report = synthesize(query, sub_questions, search_results, extracted, cross_ref)

    # Format and output
    markdown = format_report(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        logger.info("Report written to %s", args.output)
    else:
        print("\n" + markdown)

    logger.info("Research complete. %d sources cited.", report.sources_count)


if __name__ == "__main__":
    main()