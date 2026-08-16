"""LLM-powered multi-pass review pipeline.

Examines each changed file for logic errors, security holes, edge-case bugs,
and performance issues using the Anthropic API.
"""

from __future__ import annotations

import os
from typing import Optional

from src.models import (
    FileDiff,
    Issue,
    IssueSeverity,
    PRInfo,
    ReviewCategory,
    ReviewReport,
    TestResult,
)

# Module-level client singleton for Anthropic
_claude: Optional[object] = None


def _get_anthropic():
    """Lazy-init the Anthropic client."""
    global _claude
    if _claude is None:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        _claude = anthropic.Anthropic(api_key=api_key)
    return _claude


def set_anthropic_client(client: Optional[object]) -> None:
    """Inject a test double. Pass None to reset."""
    global _claude
    _claude = client


def _build_review_prompt(
    diff: FileDiff,
    category: ReviewCategory,
    all_diffs: list[FileDiff],
) -> str:
    """Build a prompt for a single review pass on one file."""
    category_descriptions = {
        ReviewCategory.logic: (
            "LOGIC ERRORS: Look for incorrect conditionals, off-by-one errors, "
            "wrong operator precedence, incorrect assumptions about data flow, "
            "dead code that should be alive, missing return statements, "
            "incorrect state transitions, or any bug that would cause wrong output."
        ),
        ReviewCategory.security: (
            "SECURITY HOLES: Look for SQL injection, command injection, "
            "path traversal, hardcoded secrets, missing input validation, "
            "insecure deserialization, improper access control, "
            "XSS, CSRF, or any OWASP Top 10 vulnerability."
        ),
        ReviewCategory.edge_case: (
            "EDGE-CASE BUGS: Look for crashes on empty input, None/null dereferences, "
            "boundary conditions (off-by-one, integer overflow), "
            "missing handling of unusual or malformed input, "
            "race conditions, resource leaks, error-handling gaps."
        ),
        ReviewCategory.performance: (
            "PERFORMANCE ISSUES: Look for O(n2) where O(n) would do, "
            "unnecessary allocations in hot paths, redundant computations, "
            "N+1 database queries, missing caching opportunities, "
            "blocking I/O in async code, large data copies."
        ),
    }

    return f"""You are an expert code reviewer. Review the following code diff for a pull request.

CATEGORY: {category.value.upper()}
{category_descriptions.get(category, "")}

DIFF:
```
{diff.patch}
```

FULL FILE LIST (for context on how this file fits in):
{", ".join(f.filename + " (" + f.status + ")" for f in all_diffs)}

Respond in this exact JSON format for EACH issue you find:

{{
  "issues": [
    {{
      "line_start": <int>,
      "line_end": <int>,
      "title": "<short title>",
      "description": "<detailed explanation of the bug>",
      "suggested_fix": "<exact code or approach to fix>",
      "confidence": <0.0 to 1.0>,
      "severity": "<critical|major|minor|suggestion>"
    }}
  ]
}}

If you find no issues in this category, respond with: {{"issues": []}}

Be thorough but practical. Focus on real bugs, not style preferences.
Confidence > 0.7 means you're nearly certain; < 0.5 means plausible but uncertain.
"""


def _parse_issues_from_response(
    response_text: str,
    filename: str,
    category: ReviewCategory,
) -> list[Issue]:
    """Parse the LLM response into Issue objects."""
    import json

    # Extract JSON from the response (it may be wrapped in markdown)
    text = response_text.strip()
    # Try to find JSON block
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        text = text[json_start:json_end]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    issues: list[Issue] = []
    for item in data.get("issues", []):
        severity_str = item.get("severity", "minor")
        try:
            severity = IssueSeverity(severity_str)
        except ValueError:
            severity = IssueSeverity.minor

        issues.append(
            Issue(
                file=filename,
                line_start=item.get("line_start", 0),
                line_end=item.get("line_end", 0),
                category=category,
                severity=severity,
                title=item.get("title", "Unknown issue"),
                description=item.get("description", ""),
                suggested_fix=item.get("suggested_fix", ""),
                confidence=float(item.get("confidence", 0.5)),
            )
        )
    return issues


def review_file(
    diff: FileDiff,
    category: ReviewCategory,
    all_diffs: list[FileDiff],
) -> list[Issue]:
    """Run a single review pass on one file for one category.

    Returns the list of issues found. In test mode (no Anthropic key),
    returns simulated issues.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Simulate issues for testing when no API key is set
        return _simulate_review(diff, category)

    client = _get_anthropic()
    prompt = _build_review_prompt(diff, category, all_diffs)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text
    except Exception as e:
        # Fallback to simulated on error
        return _simulate_review(diff, category)

    return _parse_issues_from_response(response_text, diff.filename, category)


def _simulate_review(diff: FileDiff, category: ReviewCategory) -> list[Issue]:
    """Return simulated issues for testing without an API key."""
    issues: list[Issue] = []
    patch = diff.patch or ""

    # Check for common issues based on patterns in the diff
    if "+    print(" in patch or "+    console.log(" in patch or "+    logger.info(" in patch:
        issues.append(
            Issue(
                file=diff.filename,
                line_start=1,
                line_end=1,
                category=category,
                severity=IssueSeverity.suggestion if category != ReviewCategory.security else IssueSeverity.minor,
                title="Debug statement left in code",
                description="A debug print/log statement appears in the diff. Consider removing it before merging, or replacing with a proper logging call.",
                suggested_fix="Remove the debug print/log line, or use a proper structured logging approach.",
                confidence=0.85,
            )
        )

    lines = patch.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("+") and line.lstrip("+").strip().startswith("#") and "TODO" in line.upper():
            issues.append(
                Issue(
                    file=diff.filename,
                    line_start=max(1, i),
                    line_end=max(1, i),
                    category=category,
                    severity=IssueSeverity.minor,
                    title="TODO comment in committed code",
                    description="A TODO comment was added. Address it before merging or track it as an issue.",
                    suggested_fix="Resolve the TODO or create a tracking issue and reference the issue number.",
                    confidence=0.6,
                )
            )
        if line.startswith("+") and "password" in line.lower() and "=" in line:
            issues.append(
                Issue(
                    file=diff.filename,
                    line_start=max(1, i),
                    line_end=max(1, i),
                    category=ReviewCategory.security,
                    severity=IssueSeverity.critical,
                    title="Potential hardcoded secret",
                    description="A line containing 'password' and an assignment was added. This could be a hardcoded credential.",
                    suggested_fix="Use environment variables or a secrets manager instead of hardcoding.",
                    confidence=0.7,
                )
            )

    return issues


def run_full_review(
    pr_info: PRInfo,
    files: list[FileDiff],
    previous_test_results: Optional[TestResult] = None,
    iteration: int = 0,
) -> list[Issue]:
    """Run all four review passes across all changed files.

    Args:
        pr_info: The PR info.
        files: All changed files with diff patches.
        previous_test_results: If we're iterating, the last test run.
        iteration: Which iteration we're on (0-based).

    Returns:
        A list of all issues found across all passes.
    """
    categories = [
        ReviewCategory.logic,
        ReviewCategory.security,
        ReviewCategory.edge_case,
        ReviewCategory.performance,
    ]

    all_issues: list[Issue] = []
    for diff in files:
        for category in categories:
            issues = review_file(diff, category, files)
            all_issues.extend(issues)

    return all_issues


def generate_patch_plan(
    issue: Issue,
    diff: FileDiff,
) -> str:
    """Generate a suggested fix patch for a given issue.

    In production this would call the LLM to produce a unified diff.
    For the thin slice, returns the suggested_fix text as a patch.
    """
    return issue.suggested_fix