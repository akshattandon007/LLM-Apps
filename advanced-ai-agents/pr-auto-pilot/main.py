#!/usr/bin/env python3
"""PR Auto-Pilot — An end-to-end PR review agent.

Usage:
    python main.py --pr-url https://github.com/user/repo/pull/42
    python main.py --pr-url https://github.com/user/repo/pull/42 --no-post
    python main.py --pr-url https://github.com/user/repo/pull/42 --repo-path /path/to/repo
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

from src.github_client import (
    fetch_pr_diff,
    fetch_pr_files,
    get_pr_info_from_url,
    parse_diff_to_filediffs,
    post_pr_comment,
    post_review_comment,
)
from src.models import (
    Issue,
    IssueSeverity,
    Patch,
    PRInfo,
    ReviewCategory,
    ReviewReport,
    TestResult,
)
from src.patcher import (
    apply_issue_fix,
    apply_patches,
    checkout_pr,
    clone_repo,
    rollback_all,
)
from src.reporter import format_report, format_short_summary
from src.reviewer import run_full_review
from src.tester import diagnose_test_failures, run_tests

MAX_ITERATIONS = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="PR Auto-Pilot — Review, patch, and test GitHub pull requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--pr-url",
        required=True,
        help="Full GitHub PR URL (e.g. https://github.com/user/repo/pull/42)",
    )
    parser.add_argument(
        "--repo-path",
        default="",
        help="Local path to an already-cloned repo (skips clone step)",
    )
    parser.add_argument(
        "--no-post",
        action="store_true",
        help="Skip posting the review comment to GitHub",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help=f"Max patch-test-rollback iterations (default: {MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress",
    )
    return parser.parse_args(argv)


def log(msg: str, verbose: bool = True) -> None:
    """Print a log message if verbose is enabled."""
    if verbose:
        print(f"[PR-Auto-Pilot] {msg}")


def run_pipeline(args: argparse.Namespace) -> ReviewReport:
    """Run the full PR review pipeline."""
    # 1. Parse the PR URL
    log(f"Parsing PR URL: {args.pr_url}", args.verbose)
    pr_info = get_pr_info_from_url(args.pr_url)
    log(f"PR: {pr_info.repo_owner}/{pr_info.repo_name}#{pr_info.pr_number}", args.verbose)

    # 2. Fetch the diff
    log("Fetching PR diff...", args.verbose)
    diff_text = fetch_pr_diff(pr_info)
    files = parse_diff_to_filediffs(diff_text)
    log(f"Found {len(files)} changed file(s)", args.verbose)

    # If no patch content, try fetching via JSON API
    if not any(f.patch for f in files):
        log("No patch content in raw diff, trying JSON API...", args.verbose)
        files = fetch_pr_files(pr_info)
        log(f"Got {len(files)} file(s) from JSON API", args.verbose)

    report = ReviewReport(
        pr_info=pr_info,
        files_changed=files,
        iteration_count=0,
    )

    # 3. Clone repo
    repo_dir = ""
    if args.repo_path:
        repo_dir = args.repo_path
        log(f"Using existing repo at {repo_dir}", args.verbose)
    else:
        log("Cloning repository...", args.verbose)
        try:
            repo_dir = clone_repo(pr_info)
            # Checkout the PR branch
            checkout_pr(repo_dir, pr_info.pr_number)
            log(f"Cloned to {repo_dir}", args.verbose)
        except Exception as e:
            log(f"Failed to clone repo: {e}", args.verbose)
            log("Continuing with diff-only review...", args.verbose)
            repo_dir = ""

    # 4. Run multi-pass review
    log("Running multi-pass review...", args.verbose)
    issues = run_full_review(pr_info, files)
    report.issues = issues
    log(f"Found {len(issues)} issue(s)", args.verbose)

    # 5. Patch-Test-Iterate loop
    if repo_dir and issues:
        for iteration in range(args.max_iterations):
            log(f"Iteration {iteration + 1}/{args.max_iterations}...", args.verbose)

            # Filter to issues that haven't been patched yet
            unpatchable = [i for i in issues
                           if i.severity in (IssueSeverity.critical, IssueSeverity.major)
                           and i.status.value not in ("patched", "skipped")]

            if not unpatchable:
                log("No more issues to patch. Stopping iteration loop.", args.verbose)
                report.iteration_count = iteration
                break

            # Generate patches for each issue
            patches = []
            for idx, issue in enumerate(unpatchable):
                diff_obj = next((f for f in files if f.filename == issue.file), None)
                if diff_obj and issue.suggested_fix:
                    patch = Patch(
                        file=issue.file,
                        diff=issue.suggested_fix,
                        issue_ref=idx,
                    )
                    patches.append(patch)

            if not patches:
                log("No patches to apply. Stopping.", args.verbose)
                report.iteration_count = iteration
                break

            # Apply patches
            applied_patches = apply_patches(
                repo_dir, patches, {}
            )
            report.patches.extend(applied_patches)

            success_count = sum(1 for p in applied_patches if p.applied)
            log(f"Applied {success_count}/{len(applied_patches)} patch(es)", args.verbose)

            if success_count == 0:
                log("No patches applied. Stopping iteration.", args.verbose)
                report.iteration_count = iteration
                break

            # Run tests
            log("Running tests...", args.verbose)
            test_result = run_tests(repo_dir)

            if test_result.passed:
                log("All tests passed! ✅", args.verbose)
                report.test_results = test_result
                report.iteration_count = iteration + 1
                break
            else:
                log(f"Tests failed: {test_result.failed_count}/{test_result.total} failed ❌",
                    args.verbose)
                log(diagnose_test_failures(test_result), args.verbose)
                report.test_results = test_result

                # Rollback
                if iteration < args.max_iterations - 1:
                    log("Rolling back changes...", args.verbose)
                    rollback_all(repo_dir)
                    log("Rolled back. Re-analyzing...", args.verbose)
                else:
                    log("Max iterations reached. Stopping.", args.verbose)
                    report.iteration_count = iteration + 1

    # 6. Calculate confidence
    confidence = _calculate_confidence(report)
    report.confidence = confidence

    # 7. Generate summary
    report.summary = _generate_summary_text(report)

    return report


def _calculate_confidence(report: ReviewReport) -> float:
    """Calculate overall confidence score."""
    if not report.issues:
        return 0.95  # No issues = high confidence

    # Base confidence on average issue confidence
    avg_confidence = sum(i.confidence for i in report.issues) / len(report.issues)

    # Reduce for unaddressed critical/major issues
    unaddressed = sum(
        1 for i in report.issues
        if i.severity in (IssueSeverity.critical, IssueSeverity.major)
        and i.status.value not in ("patched", "skipped")
    )
    penalty = unaddressed * 0.1
    confidence = min(avg_confidence - penalty, 0.95)
    return max(confidence, 0.1)


def _generate_summary_text(report: ReviewReport) -> str:
    """Generate a summary sentence."""
    if not report.issues:
        return "No issues found. The code looks clean."

    critical = len([i for i in report.issues if i.severity == IssueSeverity.critical])
    major = len([i for i in report.issues if i.severity == IssueSeverity.major])

    parts = []
    if critical:
        parts.append(f"{critical} critical")
    if major:
        parts.append(f"{major} major")
    if not parts:
        parts.append(str(len(report.issues)))

    return f"Found {', '.join(parts)} issue(s) across {len(report.files_changed)} file(s)."


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    # Load .env from project root
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try current directory

    args = parse_args(argv)

    try:
        report = run_pipeline(args)

        # Print report
        print("\n" + "=" * 72)
        print(format_report(report))
        print("=" * 72)
        print(format_short_summary(report))

        # Post to GitHub
        if not args.no_post and os.environ.get("GITHUB_TOKEN"):
            log("Posting review to GitHub...", args.verbose)
            try:
                post_pr_comment(report.pr_info, format_report(report))
                log("Review posted successfully! ✅", args.verbose)
            except Exception as e:
                log(f"Failed to post review: {e} ⚠️", args.verbose)
        elif args.no_post:
            log("Skipping GitHub post (--no-post flag)", args.verbose)
        else:
            log("No GITHUB_TOKEN set. Skipping GitHub post.", args.verbose)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())