"""Pydantic models for the PR review pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCategory(str, Enum):
    logic = "logic"
    security = "security"
    edge_case = "edge_case"
    performance = "performance"


class IssueSeverity(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    suggestion = "suggestion"


class IssueStatus(str, Enum):
    found = "found"
    patched = "patched"
    failed = "failed"
    skipped = "skipped"


class PRInfo(BaseModel):
    """Information about a pull request extracted from its URL."""
    repo_owner: str
    repo_name: str
    pr_number: int
    clone_url: str = ""
    default_branch: str = "main"

    @classmethod
    def from_url(cls, url: str) -> PRInfo:
        """Parse a GitHub PR URL like https://github.com/owner/repo/pull/42."""
        # Strip trailing slashes, .git, etc.
        url = url.rstrip("/")
        parts = url.split("/")
        # Expected: https://github.com/owner/repo/pull/42
        if "github.com" not in url:
            raise ValueError(f"Not a GitHub URL: {url}")
        try:
            idx = parts.index("github.com")
            owner = parts[idx + 1]
            repo = parts[idx + 2].replace(".git", "")
            pr_number = int(parts[idx + 4])
        except (IndexError, ValueError):
            raise ValueError(
                f"Could not parse PR URL. Expected format: "
                f"https://github.com/owner/repo/pull/NUM, got {url}"
            )
        return cls(
            repo_owner=owner,
            repo_name=repo,
            pr_number=pr_number,
            clone_url=f"https://github.com/{owner}/{repo}.git",
        )


class FileDiff(BaseModel):
    """A single file's diff in a pull request."""
    filename: str
    status: str = "modified"  # added, modified, removed, renamed
    patch: str = ""
    additions: int = 0
    deletions: int = 0
    sha: str = ""


class Issue(BaseModel):
    """A code issue found during review."""
    file: str
    line_start: int = 0
    line_end: int = 0
    category: ReviewCategory
    severity: IssueSeverity
    title: str
    description: str
    suggested_fix: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    status: IssueStatus = IssueStatus.found


class Patch(BaseModel):
    """A patch to apply to the repository."""
    file: str
    diff: str = ""  # Unified diff format
    issue_ref: int = 0  # Index into the issues list
    applied: bool = False
    rolled_back: bool = False
    error: str = ""


class TestResult(BaseModel):
    """Result of running the test suite."""
    passed: bool = False
    total: int = 0
    passed_count: int = 0
    failed_count: int = 0
    errors: list[str] = Field(default_factory=list)
    output: str = ""
    duration_seconds: float = 0.0


class ReviewReport(BaseModel):
    """Complete review report."""
    pr_info: PRInfo
    files_changed: list[FileDiff] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    patches: list[Patch] = Field(default_factory=list)
    test_results: Optional[TestResult] = None
    iteration_count: int = 0
    confidence: float = 0.0
    summary: str = ""