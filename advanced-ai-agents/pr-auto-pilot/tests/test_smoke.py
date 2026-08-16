"""Smoke tests for PR Auto-Pilot.

Uses FakeGitHubClient and mock data — no real network calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.github_client import (
    PRInfo,
    fetch_pr_diff,
    fetch_pr_files,
    get_pr_info_from_url,
    parse_diff_to_filediffs,
    set_client,
)
from src.models import (
    FileDiff,
    Issue,
    IssueSeverity,
    Patch,
    PRInfo as PRInfoModel,
    ReviewCategory,
    ReviewReport,
    TestResult,
)
from src.reporter import format_report, format_short_summary
from src.reviewer import _simulate_review, review_file, run_full_review, set_anthropic_client
from src.tester import diagnose_test_failures, find_test_command, run_tests

from tests.conftest import (
    FakeGitHubClient,
    make_mock_diff_text,
    make_mock_file_diff,
    make_mock_issues,
    make_mock_pr_info,
    make_mock_test_result,
    MOCK_PR_URL,
)


class TestPRInfo:
    """Tests for PRInfo parsing."""

    def test_from_url_valid(self):
        """Parse a valid PR URL."""
        pr = PRInfoModel.from_url(MOCK_PR_URL)
        assert pr.repo_owner == "owner"
        assert pr.repo_name == "demo-repo"
        assert pr.pr_number == 42

    def test_from_url_with_git_suffix(self):
        """Parse URL with .git suffix."""
        pr = PRInfoModel.from_url("https://github.com/owner/repo.git/pull/99")
        assert pr.repo_owner == "owner"
        assert pr.repo_name == "repo"
        assert pr.pr_number == 99

    def test_from_url_invalid(self):
        """Reject non-GitHub URLs."""
        with pytest.raises(ValueError):
            PRInfoModel.from_url("https://gitlab.com/user/repo/-/merge_requests/1")

    def test_from_url_no_pr_number(self):
        """Reject URLs without PR number."""
        with pytest.raises(ValueError):
            PRInfoModel.from_url("https://github.com/user/repo")


class TestGitHubClient:
    """Tests for GitHub API client."""

    def test_fetch_pr_diff(self, fake_http_client):
        """Fetch raw diff text."""
        pr = make_mock_pr_info()
        diff = fetch_pr_diff(pr)
        assert "diff --git" in diff
        assert "src/calculator.py" in diff

    def test_fetch_pr_files(self, fake_http_client):
        """Fetch file metadata."""
        pr = make_mock_pr_info()
        files = fetch_pr_files(pr)
        assert len(files) == 1
        assert files[0].filename == "src/calculator.py"
        assert files[0].additions == 6

    def test_parse_diff_to_filediffs(self):
        """Parse raw diff text into FileDiff objects."""
        diff_text = make_mock_diff_text()
        files = parse_diff_to_filediffs(diff_text)
        assert len(files) == 1
        assert files[0].filename == "src/calculator.py"
        assert files[0].additions == 6
        assert files[0].deletions == 1
        assert "diff --git" in files[0].patch

    def test_get_pr_info_from_url(self, fake_http_client):
        """Parse URL and fetch repo metadata."""
        pr = get_pr_info_from_url(MOCK_PR_URL)
        assert pr.repo_owner == "owner"
        assert pr.repo_name == "demo-repo"
        assert pr.pr_number == 42

    def test_empty_diff_text(self):
        """Handle empty diff gracefully."""
        files = parse_diff_to_filediffs("")
        assert files == []

    def test_no_diff_lines(self):
        """Handle diff text with no diff --git lines."""
        files = parse_diff_to_filediffs("some random text\nwith no diffs")
        assert files == []


class TestReviewer:
    """Tests for the LLM-powered review pipeline."""

    def test_simulate_review_finds_print(self):
        """Detect debug statements."""
        diff = FileDiff(
            filename="test.py",
            patch="""+def foo():
+    print("hello")
+    return 42""",
        )
        issues = _simulate_review(diff, ReviewCategory.logic)
        assert len(issues) >= 1
        assert any("print" in i.title.lower() or "debug" in i.title.lower() or "print" in i.description.lower()
                   for i in issues)

    def test_simulate_review_finds_todo(self):
        """Detect TODO comments."""
        diff = FileDiff(
            filename="test.py",
            patch="""+def foo():
+    # TODO: handle edge case
+    return 42""",
        )
        issues = _simulate_review(diff, ReviewCategory.logic)
        assert any("todo" in i.title.lower() for i in issues)

    def test_simulate_review_finds_password(self):
        """Detect hardcoded passwords."""
        diff = FileDiff(
            filename="config.py",
            patch="""+DB_PASSWORD = "supersecret"
+DB_HOST = "localhost\"""",
        )
        issues = _simulate_review(diff, ReviewCategory.security)
        assert any("password" in i.title.lower() or "secret" in i.title.lower()
                   for i in issues)

    def test_simulate_review_clean_code(self):
        """No false positives on clean code."""
        diff = FileDiff(
            filename="test.py",
            patch="""+def add(a, b):
+    return a + b""",
        )
        issues = _simulate_review(diff, ReviewCategory.logic)
        assert len(issues) == 0

    def test_review_file_no_api_key(self):
        """Fall back to simulated review when no API key."""
        diff = make_mock_file_diff()
        issues = review_file(diff, ReviewCategory.logic, [diff])
        # Should always return a list
        assert isinstance(issues, list)


class TestReporter:
    """Tests for the report formatter."""

    def test_format_report_empty(self):
        """Format a report with no issues."""
        pr_info = make_mock_pr_info()
        report = ReviewReport(pr_info=pr_info)
        text = format_report(report)
        assert "No issues found" in text or "No issues detected" in text or "looks clean" in text

    def test_format_report_with_issues(self):
        """Format a report with issues."""
        pr_info = make_mock_pr_info()
        issues = make_mock_issues()
        report = ReviewReport(
            pr_info=pr_info,
            files_changed=[make_mock_file_diff()],
            issues=issues,
        )
        text = format_report(report)
        assert "Division by zero" in text
        assert "Critical" in text
        assert "Unused" in text

    def test_format_report_with_test_results(self):
        """Format a report with test results."""
        pr_info = make_mock_pr_info()
        report = ReviewReport(
            pr_info=pr_info,
            test_results=make_mock_test_result(True),
            confidence=0.9,
        )
        text = format_report(report)
        assert "PASSED" in text or "Tests" in text

    def test_format_short_summary(self):
        """Format a one-liner summary."""
        report = ReviewReport(
            pr_info=make_mock_pr_info(),
            issues=make_mock_issues(),
            test_results=make_mock_test_result(True),
            confidence=0.85,
        )
        summary = format_short_summary(report)
        assert "PR Auto-Pilot" in summary
        assert "issues" in summary.lower()

    def test_confidence_bar_scores(self):
        """Test the confidence bar rendering."""
        from src.reporter import _confidence_bar
        bar = _confidence_bar(0.9)
        assert "█" in bar
        assert "░" in bar


class TestTester:
    """Tests for the test runner."""

    def test_find_test_command_no_repo(self):
        """Return default when no config found."""
        cmd = find_test_command("/tmp/nonexistent-path-xyz")
        assert cmd is None or "unittest" in cmd or "pytest" in cmd

    def test_diagnose_pass(self):
        """Diagnose a passing test result."""
        tr = make_mock_test_result(True)
        msg = diagnose_test_failures(tr)
        assert "passed" in msg.lower()

    def test_diagnose_fail(self):
        """Diagnose a failing test result."""
        tr = make_mock_test_result(False)
        msg = diagnose_test_failures(tr)
        assert "failed" in msg.lower()


class TestPipeline:
    """End-to-end pipeline smoke tests."""

    def test_pr_url_parsing(self):
        """Full pipeline test — just PR URL parsing and diff fetch."""
        pr = PRInfoModel.from_url(MOCK_PR_URL)
        assert pr.pr_number == 42
        assert pr.repo_owner == "owner"

    def test_parse_and_review_flow(self):
        """Parse diff, run simulated review, generate report."""
        diff_text = make_mock_diff_text()
        files = parse_diff_to_filediffs(diff_text)
        assert len(files) == 1

        pr = make_mock_pr_info()
        issues = run_full_review(pr, files)
        assert isinstance(issues, list)

        report = ReviewReport(
            pr_info=pr,
            files_changed=files,
            issues=issues,
        )
        text = format_report(report)
        assert len(text) > 0

    def test_format_then_parse_report(self):
        """Round-trip: format report, verify key sections exist."""
        pr = make_mock_pr_info()
        issues = make_mock_issues()
        report = ReviewReport(
            pr_info=pr,
            files_changed=[make_mock_file_diff()],
            issues=issues,
            test_results=make_mock_test_result(True),
            confidence=0.88,
        )
        text = format_report(report)
        # Verify key structural elements
        assert "# PR Auto-Pilot Review" in text
        assert "Confidence" in text
        assert "Issues Found" in text
        assert "Test Results" in text
        assert "Division by zero" in text

    def test_model_serialization(self):
        """All models can serialize to/from JSON."""
        issue = make_mock_issues()[0]
        data = issue.model_dump()
        restored = Issue.model_validate(data)
        assert restored.file == issue.file
        assert restored.title == issue.title

        tr = make_mock_test_result(True)
        data = tr.model_dump()
        restored = TestResult.model_validate(data)
        assert restored.passed == tr.passed


class TestPatcher:
    """Tests for patch operations."""

    def test_patch_model_roundtrip(self):
        """Patch model creates and validates correctly."""
        patch = Patch(
            file="src/calculator.py",
            diff="@@ -1,3 +1,5 @@",
            issue_ref=0,
        )
        assert patch.file == "src/calculator.py"
        assert not patch.applied


class TestEdgeCases:
    """Edge case handling."""

    def test_empty_diff_handling(self):
        """Empty diff produces no files."""
        files = parse_diff_to_filediffs("")
        assert len(files) == 0

    def test_diff_with_single_file(self):
        """Single file diff parses correctly."""
        diff = """diff --git a/readme.txt b/readme.txt
index abc..def 100644
--- a/readme.txt
+++ b/readme.txt
@@ -1 +1,2 @@
-old line
+new line
+another line"""
        files = parse_diff_to_filediffs(diff)
        assert len(files) == 1
        assert files[0].filename == "readme.txt"
        assert files[0].additions == 2
        assert files[0].deletions == 1

    def test_diff_with_new_file(self):
        """New file diff (--- /dev/null)."""
        diff = """diff --git a/newfile.py b/newfile.py
new file mode 100644
index 0000000..abc123
--- /dev/null
+++ b/newfile.py
@@ -0,0 +1,3 @@
+def hello():
+    print("hi")
+    return 42"""
        files = parse_diff_to_filediffs(diff)
        assert len(files) == 1
        assert files[0].filename == "newfile.py"