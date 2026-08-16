"""GitHub API client — fetch PR diff, files, and post comments.

Module-level singleton pattern for testability.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import httpx

from src.models import PRInfo, FileDiff

DIFF_URL_TEMPLATE = (
    "https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
)
FILES_URL_TEMPLATE = (
    "https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files"
)
COMMENTS_URL_TEMPLATE = (
    "https://api.github.com/repos/{owner}/{repo}/pulls/{number}/comments"
)
PR_COMMENTS_URL_TEMPLATE = (
    "https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
)

_client: Optional[httpx.Client] = None


def _get_client() -> httpx.Client:
    """Lazy-initialize the shared HTTPX client (singleton)."""
    global _client
    if _client is None:
        token = os.environ.get("GITHUB_TOKEN", "")
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "pr-auto-pilot/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        _client = httpx.Client(headers=headers, timeout=60.0)
    return _client


def set_client(client: Optional[httpx.Client]) -> None:
    """Inject a test double. Pass None to reset."""
    global _client
    _client = client


def get_diff_url(pr: PRInfo) -> str:
    """Return the API URL that returns the raw diff."""
    return DIFF_URL_TEMPLATE.format(
        owner=pr.repo_owner, repo=pr.repo_name, number=pr.pr_number
    )


def get_files_url(pr: PRInfo) -> str:
    """Return the API URL that returns file metadata."""
    return FILES_URL_TEMPLATE.format(
        owner=pr.repo_owner, repo=pr.repo_name, number=pr.pr_number
    )


def fetch_pr_diff(pr: PRInfo) -> str:
    """Fetch the raw unified diff for a PR. Returns the diff text."""
    url = DIFF_URL_TEMPLATE.format(
        owner=pr.repo_owner, repo=pr.repo_name, number=pr.pr_number
    )
    client = _get_client()
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text


def fetch_pr_files(pr: PRInfo) -> list[FileDiff]:
    """Fetch metadata about each changed file in the PR."""
    url = FILES_URL_TEMPLATE.format(
        owner=pr.repo_owner, repo=pr.repo_name, number=pr.pr_number
    )
    client = _get_client()
    # Need JSON response for file metadata
    json_headers = dict(client.headers)
    json_headers["Accept"] = "application/vnd.github.v3+json"
    resp = client.get(url, headers=json_headers)
    resp.raise_for_status()
    data = resp.json()

    files = []
    for f in data:
        files.append(
            FileDiff(
                filename=f["filename"],
                status=f.get("status", "modified"),
                patch=f.get("patch", ""),
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
                sha=f.get("sha", ""),
            )
        )
    return files


def parse_diff_to_filediffs(diff_text: str) -> list[FileDiff]:
    """Parse a raw unified diff text into FileDiff objects.

    Handles the common diff format::

        diff --git a/file.py b/file.py
        index abc123..def456 100644
        --- a/file.py
        +++ b/file.py
        @@ -1,5 +1,7 @@
         ...
    """
    files: list[FileDiff] = []
    current: Optional[FileDiff] = None
    current_patch: list[str] = []
    adds = 0
    deletes = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            # Save previous file
            if current is not None:
                current.patch = "\n".join(current_patch)
                current.additions = adds
                current.deletions = deletes
                files.append(current)
            # Start new file
            parts = line.split()
            b_path = parts[-1]  # b/path
            filename = b_path[2:] if b_path.startswith("b/") else b_path
            current = FileDiff(filename=filename)
            current_patch = [line]
            adds = 0
            deletes = 0
        elif current is not None:
            current_patch.append(line)
            if line.startswith("+") and not line.startswith("+++"):
                adds += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletes += 1

    if current is not None:
        current.patch = "\n".join(current_patch)
        current.additions = adds
        current.deletions = deletes
        files.append(current)

    return files


def post_pr_comment(pr: PRInfo, body: str) -> dict:
    """Post a general comment on a PR (issue-style comment)."""
    client = _get_client()
    url = PR_COMMENTS_URL_TEMPLATE.format(
        owner=pr.repo_owner, repo=pr.repo_name, number=pr.pr_number
    )
    json_headers = dict(client.headers)
    json_headers["Accept"] = "application/vnd.github.v3+json"
    json_headers["Content-Type"] = "application/json"
    resp = client.post(url, headers=json_headers, json={"body": body})
    resp.raise_for_status()
    return resp.json()


def post_review_comment(pr: PRInfo, body: str, commit_id: str, path: str, line: int) -> dict:
    """Post a review comment on a specific line."""
    client = _get_client()
    url = COMMENTS_URL_TEMPLATE.format(
        owner=pr.repo_owner, repo=pr.repo_name, number=pr.pr_number
    )
    json_headers = dict(client.headers)
    json_headers["Accept"] = "application/vnd.github.v3+json"
    json_headers["Content-Type"] = "application/json"
    payload = {
        "body": body,
        "commit_id": commit_id,
        "path": path,
        "line": line,
    }
    resp = client.post(url, headers=json_headers, json=payload)
    resp.raise_for_status()
    return resp.json()


def get_pr_info_from_url(url: str) -> PRInfo:
    """Parse PR URL and fetch additional metadata (default branch)."""
    pr = PRInfo.from_url(url)
    try:
        api_url = (
            f"https://api.github.com/repos/{pr.repo_owner}/{pr.repo_name}"
        )
        client = _get_client()
        json_headers = dict(client.headers)
        json_headers["Accept"] = "application/vnd.github.v3+json"
        resp = client.get(api_url, headers=json_headers)
        resp.raise_for_status()
        data = resp.json()
        pr.default_branch = data.get("default_branch", "main")
    except Exception:
        pr.default_branch = "main"
    return pr