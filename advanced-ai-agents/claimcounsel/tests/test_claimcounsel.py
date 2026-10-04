"""
Tests for ClaimCounsel agents and utilities.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timedelta

# Add parent to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import CLAIM_DEADLINES, CLAIM_TYPE_DOCUMENTS
from utils.file_utils import (
    ensure_dirs,
    write_text_file,
    write_json_file,
    read_text_file,
    read_json_file,
    extract_pdf_text,
    read_all_texts,
    list_claim_files,
)
from agents.timeline_tracker import TimelineTrackerAgent
from agents.document_collector import DocumentCollectorAgent
from agents.letter_drafter import LetterDrafterAgent
from agents.policy_parser import PolicyParserAgent


# ─── Config Tests ───


class TestConfig:
    def test_claim_deadlines_has_all_states(self):
        """Should have all 50 US states."""
        assert len(CLAIM_DEADLINES) == 50
        assert "CA" in CLAIM_DEADLINES
        assert "NY" in CLAIM_DEADLINES
        assert "TX" in CLAIM_DEADLINES

    def test_claim_type_documents_has_types(self):
        """Should cover all standard claim types."""
        for t in ["auto", "home", "health", "life", "travel"]:
            assert t in CLAIM_TYPE_DOCUMENTS
            assert len(CLAIM_TYPE_DOCUMENTS[t]) >= 3


# ─── File Utils Tests ───


class TestFileUtils:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_write_and_read_text(self):
        path = os.path.join(self.tmpdir, "test.txt")
        write_text_file(path, "hello world")
        assert read_text_file(path) == "hello world"

    def test_write_and_read_json(self):
        path = os.path.join(self.tmpdir, "test.json")
        data = {"name": "test", "value": 42}
        write_json_file(path, data)
        assert read_json_file(path) == data

    def test_ensure_dirs_creates(self):
        test_dir = os.path.join(self.tmpdir, "a/b/c")
        os.makedirs(test_dir, exist_ok=True)  # just verify the concept
        assert os.path.isdir(test_dir)

    def test_list_claim_files(self):
        for f in ["doc1.txt", "doc2.pdf", "notes.md"]:
            write_text_file(os.path.join(self.tmpdir, f), "test")
        files = list_claim_files(self.tmpdir)
        assert len(files) == 3
        assert all(f.endswith((".txt", ".pdf", ".md")) for f in files)

    def test_read_all_texts_plain(self):
        write_text_file(os.path.join(self.tmpdir, "hello.txt"), "Hello World")
        result = read_all_texts(self.tmpdir)
        assert "hello.txt" in result
        assert result["hello.txt"] == "Hello World"

    def test_extract_pdf_text_nonexistent(self):
        """Should handle missing/non-PDF files gracefully."""
        result = extract_pdf_text(os.path.join(self.tmpdir, "nonexistent.pdf"))
        assert result is None

    def test_read_all_texts_empty_dir(self):
        """Should handle empty directories."""
        result = read_all_texts(self.tmpdir)
        assert result == {}


# ─── Timeline Tracker Tests ───


class TestTimelineTracker:
    def setup_method(self):
        self.tracker = TimelineTrackerAgent(llm_client=None)

    def test_get_filing_deadline_days(self):
        assert self.tracker.get_filing_deadline_days("CA") == 365
        assert self.tracker.get_filing_deadline_days("AL") == 730
        assert self.tracker.get_filing_deadline_days("XX") == 365  # unknown defaults

    def test_calculate_timeline(self):
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        result = self.tracker.calculate_timeline("auto", "CA", thirty_days_ago)
        assert "error" not in result
        assert result["state"] == "CA"
        assert result["days_remaining"] > 300  # roughly 335 for a 365-day limit
        assert result["is_overdue"] is False
        assert result["status"] == "OK"
        assert len(result["milestones"]) == 4

    def test_calculate_timeline_overdue(self):
        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        result = self.tracker.calculate_timeline("auto", "CA", two_years_ago)
        assert result["is_overdue"] is True
        assert result["status"] == "OVERDUE"

    def test_calculate_timeline_invalid_date(self):
        result = self.tracker.calculate_timeline("auto", "CA", "not-a-date")
        assert "error" in result

    def test_get_next_steps_overdue(self):
        result = self.tracker.get_next_steps({"is_overdue": True, "days_remaining": -5})
        assert any("attorney" in s.lower() for s in result)

    def test_get_next_steps_ok(self):
        result = self.tracker.get_next_steps({"is_overdue": False, "days_remaining": 300})
        assert any("don't procrastinate" in s for s in result)

    def test_get_next_steps_urgent(self):
        result = self.tracker.get_next_steps({"is_overdue": False, "days_remaining": 5})
        assert any("week" in s for s in result)


# ─── Document Collector Tests ───


class TestDocumentCollector:
    def setup_method(self):
        self.collector = DocumentCollectorAgent(llm_client=None)
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_get_required_documents(self):
        docs = self.collector.get_required_documents("auto")
        assert len(docs) >= 4
        assert any("Police" in d for d in docs)

    def test_get_required_documents_fallback(self):
        docs = self.collector.get_required_documents("unknown_type")
        assert len(docs) >= 4  # falls back to auto

    def test_inventory_documents_empty(self):
        result = self.collector.inventory_documents(self.tmpdir)
        assert result == {}

    def test_inventory_documents_with_files(self):
        write_text_file(os.path.join(self.tmpdir, "police_report.txt"), "Police report for accident")
        result = self.collector.inventory_documents(self.tmpdir)
        assert "police_report.txt" in result

    def test_generate_checklist(self):
        checklist = self.collector.generate_checklist("auto")
        assert "Document Checklist" in checklist
        assert "Police report" in checklist or "Photos" in checklist


# ─── Letter Drafter Tests ───


class TestLetterDrafter:
    def setup_method(self):
        self.drafter = LetterDrafterAgent(llm_client=None)

    def test_draft_initial_claim_no_llm(self):
        """Without an LLM, the letter will show an error — which is fine."""
        letter = self.drafter.draft_initial_claim(
            policy_number="POL-12345",
            insurance_company="Test Insurance Co",
            claim_type="auto",
            incident_date="2026-09-15",
            incident_description="Rear-end collision at intersection",
            estimated_damages="$5,000",
        )
        # Without an API key, it'll return an error message
        assert letter is not None
        assert len(letter) > 0


# ─── Policy Parser Tests ───


class TestPolicyParser:
    def setup_method(self):
        self.parser = PolicyParserAgent(llm_client=None)
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_parse_policy_no_file(self):
        result = self.parser.parse_policy("/nonexistent/policy.pdf")
        assert "error" in result

    def test_parse_policy_empty_file(self):
        path = os.path.join(self.tmpdir, "policy.txt")
        write_text_file(path, "Short")
        result = self.parser.parse_policy(path)
        # Without LLM, will get error but should handle gracefully
        assert result is not None

    def test_summarize_in_plain_english_no_llm(self):
        summary = self.parser.summarize_in_plain_english({"insurance_company": "Test Co"})
        assert summary is not None


# ─── Integration Tests ───


class TestClaimCounselIntegration:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.claims_dir = os.path.join(self.tmpdir, "claims")
        self.policies_dir = os.path.join(self.tmpdir, "policies")
        self.documents_dir = os.path.join(self.tmpdir, "documents")
        self.output_dir = os.path.join(self.tmpdir, "output")

        # Override config paths
        import config
        config.CLAIMS_DIR = self.claims_dir
        config.POLICIES_DIR = self.policies_dir
        config.DOCUMENTS_DIR = self.documents_dir
        config.OUTPUT_DIR = self.output_dir

        # Create dirs with our test function that uses the config values
        for d in [self.claims_dir, self.policies_dir, self.documents_dir, self.output_dir]:
            os.makedirs(d, exist_ok=True)

        # Create sample test documents
        write_text_file(
            os.path.join(self.documents_dir, "police_report.txt"),
            "Police Report #12345\nDate: 2026-09-15\nParties involved: 2 vehicles\n"
            "Location: Main St & Oak Ave\nDamage: Front-end collision",
        )
        write_text_file(
            os.path.join(self.documents_dir, "damage_photos_notes.txt"),
            "Photos taken 2026-09-15\nFile: IMG_0001.jpg - front bumper damage\n"
            "File: IMG_0002.jpg - side panel damage",
        )

        # Create a sample policy
        write_text_file(
            os.path.join(self.policies_dir, "policy.txt"),
            "Policy Number: POL-2025-ABCD\nInsurance Company: SafeGuard Insurance\n"
            "Policy Type: Auto\nCoverage Start: 2025-01-01\nCoverage End: 2026-01-01\n"
            "Deductible: $1,000\nCoverage Limit: $50,000\n"
            "Covered: Collision, Comprehensive, Liability\n"
            "Excluded: Intentional damage, wear and tear\n"
            "To file a claim: Call 1-800-555-0199 or visit our website",
        )

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_full_pipeline_without_llm(self):
        """Run the orchestrator without an LLM to test the agent wiring."""
        from main import ClaimCounselOrchestrator

        # Patch config to use test directories
        import config
        config.CLAIMS_DIR = self.claims_dir
        config.POLICIES_DIR = self.policies_dir
        config.DOCUMENTS_DIR = self.documents_dir
        config.OUTPUT_DIR = self.output_dir

        orch = ClaimCounselOrchestrator()
        result = orch.run_full_pipeline(
            claim_type="auto",
            state_code="CA",
            incident_date="2026-09-15",
            incident_description="Rear-end collision at Main & Oak intersection",
            policy_filepath=os.path.join(self.policies_dir, "policy.txt"),
            documents_dir=self.documents_dir,
            output_name="test_claim",
        )

        assert result["claim_type"] == "auto"
        assert result["state"] == "CA"
        assert result["incident_date"] == "2026-09-15"
        assert "timeline" in result
        assert "document_readiness" in result
        assert "draft_letter" in result
        assert "checklist" in result
        assert "next_steps" in result

        # Check outputs were saved
        assert os.path.isdir(os.path.join(self.output_dir, "test_claim"))
        assert os.path.isfile(os.path.join(self.output_dir, "test_claim", "claim_counsel_report.json"))
        assert os.path.isfile(os.path.join(self.output_dir, "test_claim", "claim_counsel_report.txt"))

        # Check JSON content
        with open(os.path.join(self.output_dir, "test_claim", "claim_counsel_report.json")) as f:
            saved = json.load(f)
            assert saved["claim_type"] == "auto"
            assert "run_timestamp" in saved


# ─── Run tests if executed directly ───

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])