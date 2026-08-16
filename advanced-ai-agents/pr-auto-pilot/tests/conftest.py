"""Test fixtures and mock data for PR Auto-Pilot."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from src.github_client import set_client
from src.models import (
    FileDiff,
    Issue,
    IssueSeverity,
    PRInfo,
    Patch,
    ReviewCategory,
    ReviewReport,
    TestResult,
)


MOCK_PR_URL = "https://github.com/owner/demo-repo/pull/42"
MOCK_REPO_OWNER = "owner"
MOCK_REPO_NAME = "demo-repo"
MOCK_PR_NUMBER = 42


def make_mock_pr_info() -> PRInfo:
    """Create a mock PRInfo."""
    return PRInfo(
        repo_owner=MOCK_REPO_OWNER,
        repo_name=MOCK_REPO_NAME,
        pr_number=MOCK_PR_NUMBER,
        clone_url="https://github.com/owner/demo-repo.git",
        default_branch="main",
    )


def make_mock_file_diff() -> FileDiff:
    """Create a mock file diff with sample patch content."""
    return FileDiff(
        filename="src/calculator.py",
        status="modified",
        patch="""--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,10 +1,15 @@
 def divide(a, b):
-    return a / b
+    if b == 0:
+        return None
+    return a / b
+
+def add(a, b):
+    return a + b""",
        additions=6,
        deletions=1,
    )


def make_mock_diff_text() -> str:
    """Create a full mock diff text as returned by GitHub API."""
    return """diff --git a/src/calculator.py b/src/calculator.py
index abc123..def456 100644
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,10 +1,15 @@
 def divide(a, b):
-    return a / b
+    if b == 0:
+        return None
+    return a / b
+
+def add(a, b):
+    return a + b
"""


def make_mock_issues() -> list[Issue]:
    """Create mock review issues."""
    return [
        Issue(
            file="src/calculator.py",
            line_start=2,
            line_end=2,
            category=ReviewCategory.logic,
            severity=IssueSeverity.critical,
            title="Division by zero",
            description="The divide function does not handle division by zero. This will raise a ZeroDivisionError.",
            suggested_fix="""--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,3 +1,5 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b""",
            confidence=0.95,
        ),
        Issue(
            file="src/calculator.py",
            line_start=6,
            line_end=6,
            category=ReviewCategory.logic,
            severity=IssueSeverity.minor,
            title="Unused new function",
            description="The add function is defined but not called anywhere.",
            suggested_fix="Consider removing the add function if it's not needed.",
            confidence=0.5,
        ),
    ]


def make_mock_test_result(passed: bool = True) -> TestResult:
    """Create a mock test result."""
    if passed:
        return TestResult(
            passed=True,
            total=5,
            passed_count=5,
            failed_count=0,
            duration_seconds=1.23,
        )
    return TestResult(
        passed=False,
        total=5,
        passed_count=3,
        failed_count=2,
        errors=["FAILED test_divide_by_zero"],
        output="3 passed, 2 failed in 1.23s\nFAILED test_divide_by_zero",
        duration_seconds=1.23,
    )


class FakeGitHubClient(httpx.Client):
    """A fake HTTPX client for testing that returns mock GitHub API responses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Pre-set the Accept header so it's available in overridden send()
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "pr-auto-pilot/1.0",
        }
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        super().__init__(*args, headers=headers, **kwargs)
        self.requests_made: list[dict] = []

    def send(
        self, request: httpx.Request, **kwargs: Any
    ) -> httpx.Response:
        """Handle mock requests."""
        self.requests_made.append({
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
        })
        url = str(request.url)
        # Route purely on URL patterns — httpx doesn't merge client-level
        # headers into the Request object before send() is called.
        if "/pulls/42/files" in url:
            # File list — GitHub JSON API
            return httpx.Response(
                200,
                json=[{
                    "filename": "src/calculator.py",
                    "status": "modified",
                    "additions": 6,
                    "deletions": 1,
                    "sha": "abc123",
                    "patch": "+    if b == 0:\n+        return None\n+    return a / b\n+\n+def add(a, b):\n+    return a + b",
                }],
                request=request,
            )
        elif url.endswith("pulls/42"):
            # PR detail — returns raw diff text (the default client Accept header
            # asks for vnd.github.v3.diff, which the real API uses to return diffs)
            return httpx.Response(
                200,
                text=make_mock_diff_text(),
                request=request,
            )
        elif "repos/owner/demo-repo" in url and "/issues/" not in url and "/pulls" not in url:
            # Repo info
            return httpx.Response(
                200,
                json={"default_branch": "main"},
                request=request,
            )
        else:
            return httpx.Response(404, text="Not found", request=request)


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset the global client singletons before each test."""
    set_client(None)
    yield
    set_client(None)


@pytest.fixture
def fake_http_client():
    """Create and inject a FakeGitHubClient."""
    client = FakeGitHubClient()
    set_client(client)
    return client


@pytest.fixture
def mock_pr_info():
    """Create a PRInfo for testing URL parsing."""
    return make_mock_pr_info()


@pytest.fixture
def mock_file_diff():
    """Create a FileDiff for testing."""
    return make_mock_file_diff()


@pytest.fixture
def mock_issues():
    """Create mock issues for testing."""
    return make_mock_issues()


@pytest.fixture
def mock_report():
    """Create a complete ReviewReport for testing."""
    pr_info = make_mock_pr_info()
    issues = make_mock_issues()
    return ReviewReport(
        pr_info=pr_info,
        files_changed=[make_mock_file_diff()],
        issues=issues,
        test_results=make_mock_test_result(True),
        confidence=0.85,
        summary="Found 2 issue(s) across 1 file(s).",
    )