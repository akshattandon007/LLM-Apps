#!/usr/bin/env python3
"""
Tests for Clarity — Legal Document Clarity Analyzer.
"""
import sys
import os
import json
import tempfile

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.clause_extractor import ClauseExtractor, _rule_based_extract
from agents.plain_translator import PlainTranslator, _rule_based_translate
from agents.risk_advisor import RiskAdvisor, _rule_based_risk
from agents.orchestrator import Orchestrator


SAMPLE_CONTRACT = """
SERVICE AGREEMENT

1. PAYMENT TERMS: The Client shall pay a monthly fee of $49.99. Late payments shall incur a fee of $25.00.

2. AUTO-RENEWAL: This Agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least 30 days prior to the end of the current term.

3. ARBITRATION: Any dispute arising out of this Agreement shall be resolved by binding arbitration in accordance with the rules of the American Arbitration Association. The Client waives any right to a jury trial.

4. LIMITATION OF LIABILITY: IN NO EVENT SHALL THE COMPANY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES.

5. CONFIDENTIALITY: Each party agrees to maintain the confidentiality of all proprietary information disclosed during the term of this Agreement.

6. GOVERNING LAW: This Agreement shall be governed by the laws of the State of Delaware.
"""

SAMPLE_EMPTY = ""


def test_clause_extractor_rule_based():
    """Test rule-based clause extraction."""
    extractor = ClauseExtractor(api_key="", model="")
    clauses = extractor.extract(SAMPLE_CONTRACT)
    assert isinstance(clauses, list), "Should return a list"
    assert len(clauses) > 0, "Should extract at least one clause"
    assert all("text" in c and "type" in c for c in clauses), \
        "Each clause should have 'text' and 'type'"
    print(f"  ✅ Extracted {len(clauses)} clause(s) from sample contract")


def test_clause_extractor_empty():
    """Test extraction with empty text."""
    extractor = ClauseExtractor(api_key="", model="")
    clauses = extractor.extract(SAMPLE_EMPTY)
    assert clauses == [], "Empty text should return empty list"
    print("  ✅ Empty text returns empty list")


def test_plain_translator_rule_based():
    """Test rule-based plain language translation."""
    translator = PlainTranslator(api_key="", model="")
    clause = {"text": "The Lessee hereby agrees to indemnify and hold harmless the Lessor.", "type": "liability_and_indemnification"}
    result = _rule_based_translate(clause)
    assert "plain_text" in result, "Should have plain_text key"
    assert "confidence" in result, "Should have confidence key"
    assert "protect from loss" in result["plain_text"].lower(), \
        "Should replace 'indemnify' with plain language"
    print(f"  ✅ Translated clause: {result['plain_text'][:60]}...")


def test_risk_advisor_rule_based():
    """Test rule-based risk assessment."""
    clause_text = "This Agreement shall automatically renew for successive terms. The Client waives any right to a jury trial and agrees to binding arbitration."
    flags, score, explanation = _rule_based_risk(clause_text)
    assert isinstance(flags, list), "Flags should be a list"
    assert len(flags) > 0, "Should flag at least one risk"
    assert "auto_renewal" in flags or "binding_arbitration" in flags, \
        "Should detect auto-renewal or arbitration"
    assert 0 <= score <= 1, "Score should be between 0 and 1"
    print(f"  ✅ Found flags: {flags}, score: {score:.2f}")


def test_orchestrator_compilation():
    """Test that orchestrator compiles a full report."""
    orchestrator = Orchestrator()

    clauses = [
        {"text": "Client shall pay $49.99 monthly.", "type": "payment_and_fees"},
        {"text": "This Agreement auto-renews.", "type": "renewal_and_auto_renewal"},
    ]
    translations = [
        {"plain_text": "You must pay $49.99 every month.", "confidence": 0.95},
        {"plain_text": "This contract renews automatically.", "confidence": 0.90},
    ]
    risks = [
        {"score": 0.2, "flags": [], "explanation": "Standard payment clause."},
        {"score": 0.8, "flags": ["auto_renewal"], "explanation": "Auto-renewal without notice."},
    ]

    report = orchestrator.compile_report(clauses, translations, risks)
    assert "report_title" in report, "Should have report_title"
    assert "summary" in report, "Should have summary"
    assert "clauses" in report, "Should have clauses"
    assert "recommendation" in report, "Should have recommendation"
    assert len(report["clauses"]) == 2, "Should have 2 clause records"
    print(f"  ✅ Report compiled with {len(report['clauses'])} clauses")
    print(f"  ✅ Recommendation: {report['recommendation']}")


def test_orchestrator_markdown():
    """Test markdown output generation."""
    orchestrator = Orchestrator()
    report = {
        "report_title": "Clarity — Document Analysis Report",
        "generated_at": "2025-01-01T00:00:00Z",
        "summary": "📋 Document contains 1 clause(s) analyzed.\n⚠️  1 high-risk clause(s).",
        "clauses": [{
            "clause_number": 1,
            "clause_type": "auto_renewal",
            "original_text": "Auto-renew clause",
            "plain_language": "This renews automatically.",
            "confidence": 0.9,
            "risk_score": 0.8,
            "risk_flags": ["auto_renewal"],
            "risk_explanation": "Traps user in renewal.",
        }],
        "risk_summary": {"auto_renewal": 1},
        "questions_to_ask": ["When can I cancel?"],
        "recommendation": "⚠️ CAUTION",
    }
    md = orchestrator.to_markdown(report)
    assert "Clarity" in md, "Should include title"
    assert "auto_renewal" in md or "Auto-renewal" in md, "Should include risk flag"
    print(f"  ✅ Markdown report generated ({len(md)} chars)")


def test_rule_based_extract():
    """Test the raw rule-based extraction function."""
    text = "The Client shall pay a fee of $100.\n\nThis Agreement auto-renews."
    clauses = _rule_based_extract(text)
    assert len(clauses) >= 2, "Should extract at least 2 clauses"
    print(f"  ✅ Rule-based extraction found {len(clauses)} clause(s)")


def test_orchestrator_empty():
    """Test orchestrator with empty data."""
    orchestrator = Orchestrator()
    report = orchestrator.compile_report([], [], [])
    assert report["summary"] != "", "Should still generate summary"
    assert report["recommendation"] != "", "Should still generate recommendation"
    print("  ✅ Empty report generated successfully")


def test_risk_advisor_empty():
    """Test risk advisor with no flags."""
    text = "The parties agree to cooperate in good faith."
    flags, score, explanation = _rule_based_risk(text)
    assert isinstance(flags, list), "Flags should be a list"
    assert len(flags) == 0, "Friendly clause should have no flags"
    assert score == 0.0, "Score should be 0"
    print(f"  ✅ No flags for cooperative clause")


def test_plain_translator_multiple_clauses():
    """Test translation with multiple clauses."""
    translator = PlainTranslator(api_key="", model="")
    clauses = [
        {"text": "Party A shall indemnify Party B.", "type": "liability_and_indemnification"},
        {"text": "This agreement is governed by the laws of New York.", "type": "governing_law_and_jurisdiction"},
    ]
    results = translator.translate(clauses)
    assert len(results) == 2, "Should translate 2 clauses"
    assert all("plain_text" in r for r in results), "All should have plain_text"
    print(f"  ✅ Translated {len(results)} clauses")


if __name__ == "__main__":
    tests = [
        test_clause_extractor_rule_based,
        test_clause_extractor_empty,
        test_plain_translator_rule_based,
        test_risk_advisor_rule_based,
        test_orchestrator_compilation,
        test_orchestrator_markdown,
        test_rule_based_extract,
        test_orchestrator_empty,
        test_risk_advisor_empty,
        test_plain_translator_multiple_clauses,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
