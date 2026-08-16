"""Generate and apply patches to a local repository clone.

Handles rollbacks by using git stash / checkout patterns.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

import git

from src.models import Issue, Patch, PRInfo, TestResult

REPOS_BASE = "/tmp/pr-autopilot-repos"


def clone_repo(pr_info: PRInfo) -> str:
    """Clone the target repository to a local directory.

    Returns the path to the cloned repo.
    """
    repo_dir = os.path.join(
        REPOS_BASE,
        f"{pr_info.repo_owner}__{pr_info.repo_name}__pr{pr_info.pr_number}",
    )

    # Remove existing clone if present
    if os.path.exists(repo_dir):
        import shutil
        shutil.rmtree(repo_dir)

    os.makedirs(REPOS_BASE, exist_ok=True)

    repo = git.Repo.clone_from(
        pr_info.clone_url,
        repo_dir,
        branch=pr_info.default_branch,
        depth=1,
    )
    return repo_dir


def checkout_pr(repo_dir: str, pr_number: int) -> str:
    """Fetch and checkout the PR branch.

    Returns the branch name.
    """
    repo = git.Repo(repo_dir)
    branch_name = f"pr-{pr_number}"

    # Fetch the PR as a remote ref
    try:
        repo.git.fetch("origin", f"pull/{pr_number}/head:{branch_name}")
        repo.git.checkout(branch_name)
    except git.GitCommandError as e:
        # If the branch already exists locally
        repo.git.checkout(branch_name)

    return branch_name


def apply_patch(repo_dir: str, patch_content: str) -> bool:
    """Apply a unified diff patch to the repo.

    Returns True if applied cleanly, False otherwise.
    """
    repo = git.Repo(repo_dir)

    # Write patch to temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".patch", delete=False
    ) as f:
        f.write(patch_content)
        patch_path = f.name

    try:
        repo.git.apply(patch_path)
        os.unlink(patch_path)
        return True
    except git.GitCommandError:
        os.unlink(patch_path)
        return False
    except Exception:
        os.unlink(patch_path)
        return False


def apply_patches(
    repo_dir: str,
    patches: list[Patch],
    files: dict[str, str],
) -> list[Patch]:
    """Apply a list of patches, tracking success/failure.

    Args:
        repo_dir: Path to the cloned repo.
        patches: List of Patch objects (populated with diffs to apply).
        files: Dict mapping filename to contents (for direct file writes).

    Returns:
        The updated patches list with applied/error fields filled.
    """
    results: list[Patch] = []
    for i, patch_entry in enumerate(patches):
        # Try git apply if we have a diff
        if patch_entry.diff:
            success = apply_patch(repo_dir, patch_entry.diff)
        else:
            # Direct file write (e.g., for the initial fix)
            filename = patch_entry.file
            filepath = os.path.join(repo_dir, filename)
            if filename in files and os.path.exists(os.path.dirname(filepath)):
                with open(filepath, "w") as f:
                    f.write(files[filename])
                success = True
            else:
                success = False

        patch_entry.applied = success
        if not success:
            patch_entry.error = f"Failed to apply patch for {patch_entry.file}"
        results.append(patch_entry)

    return results


def rollback_all(repo_dir: str) -> bool:
    """Roll back all uncommitted changes in the repo.

    Uses git checkout to restore modified files.
    Returns True if successful.
    """
    try:
        repo = git.Repo(repo_dir)
        repo.git.checkout("--", ".")
        # Also clean untracked files that were patched
        repo.git.clean("-fd")
        return True
    except Exception:
        return False


def get_file_content(repo_dir: str, filename: str) -> str:
    """Read a file from the cloned repo."""
    filepath = os.path.join(repo_dir, filename)
    with open(filepath, "r") as f:
        return f.read()


def write_file_content(repo_dir: str, filename: str, content: str) -> None:
    """Write content to a file in the cloned repo."""
    filepath = os.path.join(repo_dir, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)


def apply_issue_fix(
    repo_dir: str,
    issue: Issue,
    fix_code: str,
) -> Optional[Patch]:
    """Attempt to apply a fix for a single issue.

    Returns a Patch object if successful, None if the fix is not applicable.
    """
    # If the suggested fix contains a diff format, use it
    if fix_code.startswith("--- ") or fix_code.startswith("diff "):
        patch = Patch(
            file=issue.file,
            diff=fix_code,
            issue_ref=0,
        )
        success = apply_patch(repo_dir, fix_code)
        patch.applied = success
        if not success:
            patch.error = "git apply failed"
        return patch

    # Otherwise, we need the current file and to apply the fix textually
    # (This is a simplified version — full implementation would use LLM to
    # generate proper unified diffs)
    return None