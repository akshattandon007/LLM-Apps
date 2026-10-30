#!/usr/bin/env python3
"""
Clarity — Multi-Agent Legal Document Analyzer

Three agents collaborate to demystify legal documents:
  ClauseExtractor  → identifies obligations, deadlines, fees, penalties
  PlainTranslator  → rewrites each clause at a 6th-grade reading level
  RiskAdvisor      → flags high-risk/unfair terms, auto-renewal traps

Usage:
  python3 main.py --file contract.txt
  python3 main.py --text "The Lessee agrees to..."
  python3 main.py --interactive          # paste text at prompt
"""

import sys
import json
import argparse
import os
from pathlib import Path

from agents.clause_extractor import ClauseExtractor
from agents.plain_translator import PlainTranslator
from agents.risk_advisor import RiskAdvisor
from agents.orchestrator import Orchestrator


def read_input(args: argparse.Namespace) -> str:
    """Read document text from file, --text flag, or stdin."""
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding="utf-8")

    if args.text:
        return args.text

    if args.interactive:
        print("📄 Paste your document text below. Press Ctrl+D (Unix) or Ctrl+Z+Enter (Windows) when done:")
        return sys.stdin.read()

    print("❌ No input provided. Use --file, --text, or --interactive.", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Clarity — Understand any legal document in plain language."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", "-f", help="Path to a text file containing the document")
    input_group.add_argument("--text", "-t", help="Document text as a string")
    input_group.add_argument("--interactive", "-i", action="store_true",
                             help="Paste document text interactively")
    parser.add_argument("--api-key", help="OpenAI/LLM API key (default: LLM_API_KEY env var)",
                        default=os.environ.get("LLM_API_KEY", ""))
    parser.add_argument("--model", default="gpt-4o-mini",
                        help="LLM model to use (default: gpt-4o-mini)")
    parser.add_argument("--output", "-o", help="Save report to file (JSON or Markdown)")
    parser.add_argument("--json", action="store_true", help="Output as JSON only")

    args = parser.parse_args()

    document = read_input(args)

    if not document.strip():
        print("❌ Empty document. Nothing to analyze.", file=sys.stderr)
        sys.exit(1)

    print("🔍 Clarity — Analyzing your document...\n")
    print("  Step 1/3: Extracting clauses...")
    extractor = ClauseExtractor(api_key=args.api_key, model=args.model)
    clauses = extractor.extract(document)
    print(f"  → Found {len(clauses)} clause(s)\n")

    print("  Step 2/3: Translating to plain language...")
    translator = PlainTranslator(api_key=args.api_key, model=args.model)
    translations = translator.translate(clauses)
    print(f"  → Translated {len(translations)} clause(s)\n")

    print("  Step 3/3: Assessing risk...")
    advisor = RiskAdvisor(api_key=args.api_key, model=args.model)
    risks = advisor.assess(clauses, translations, document)
    print(f"  → Risk assessment complete\n")

    orchestrator = Orchestrator(args.api_key, args.model)
    report = orchestrator.compile_report(clauses, translations, risks)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(
            json.dumps(report, indent=2) if args.json else report,
            encoding="utf-8"
        )
        print(f"\n📁 Report saved to {out_path.resolve()}")

    # Return structured summary for Flow.md trace
    return report


if __name__ == "__main__":
    main()
