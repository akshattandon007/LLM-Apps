"""Run tests on a cloned repository and capture results.

Handles finding and executing the test suite, parsing output, and
returning structured results.
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Optional

from src.models import TestResult


def find_test_command(repo_dir: str) -> Optional[str]:
    """Detect the test framework and return the run command.

    Checks in order: pytest.ini, setup.py/test, Makefile/test, tox.ini.
    Returns None if no test framework is detected.
    """
    checks = [
        ("pytest.ini", "pytest"),
        ("pyproject.toml", "pytest"),
        ("setup.cfg", "pytest"),
        ("tox.ini", "tox"),
        ("Makefile", "make test"),
        ("package.json", "npm test"),
        ("Cargo.toml", "cargo test"),
    ]

    for config_file, command in checks:
        if os.path.exists(os.path.join(repo_dir, config_file)):
            return command

    # Default: try pytest, fall back to python -m unittest
    try:
        result = subprocess.run(
            ["pytest", "--version"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return "pytest"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "python -m unittest discover"


def run_tests(repo_dir: str, timeout: int = 120) -> TestResult:
    """Run the test suite in the cloned repo.

    Args:
        repo_dir: Path to the cloned repository.
        timeout: Max seconds to wait for tests.

    Returns:
        TestResult with pass/fail info.
    """
    test_cmd = find_test_command(repo_dir)
    if test_cmd is None:
        test_cmd = "python -m unittest discover"

    start = time.time()

    try:
        result = subprocess.run(
            test_cmd.split(),
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.time() - start
        output = result.stdout + "\n" + result.stderr
        output = output.strip()

        # Parse test counts from output
        passed = result.returncode == 0
        total = 0
        passed_count = 0
        failed_count = 0
        errors: list[str] = []

        # Parse pytest output
        lines = output.split("\n")
        for line in lines:
            if "passed" in line and "failed" in line and "error" in line:
                # e.g. "3 passed, 1 failed in 2.34s"
                import re
                passed_match = re.search(r"(\d+)\s+passed", line)
                failed_match = re.search(r"(\d+)\s+failed", line)
                error_match = re.search(r"(\d+)\s+error", line)
                total_match = re.search(r"(\d+)\s+ran", line)

                if passed_match:
                    passed_count = int(passed_match.group(1))
                if failed_match:
                    failed_count = int(failed_match.group(1))
                if error_match:
                    errors.append(f"{error_match.group(1)} errors")
                if total_match:
                    total = int(total_match.group(1))
                else:
                    total = passed_count + failed_count

            # Collect error/failure details
            if "FAILED" in line or "ERROR" in line:
                errors.append(line.strip())

        # If no structured parse, infer from return code
        if total == 0:
            if passed:
                total = 1
                passed_count = 1
            else:
                total = 1
                failed_count = 1

        return TestResult(
            passed=passed,
            total=total,
            passed_count=passed_count,
            failed_count=failed_count,
            errors=errors if errors else [],
            output=output[:5000],  # Truncate long output
            duration_seconds=round(duration, 2),
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return TestResult(
            passed=False,
            total=0,
            passed_count=0,
            failed_count=0,
            errors=["Test suite timed out after {} seconds".format(timeout)],
            output="Timed out after {}s".format(timeout),
            duration_seconds=round(duration, 2),
        )
    except FileNotFoundError as e:
        return TestResult(
            passed=False,
            total=0,
            passed_count=0,
            failed_count=0,
            errors=[f"Test runner not found: {e}"],
            output=str(e),
            duration_seconds=0.0,
        )


def diagnose_test_failures(test_result: TestResult) -> str:
    """Generate a diagnostic description of test failures.

    Returns a human-readable explanation of what failed and why.
    """
    if test_result.passed:
        return "All tests passed. No issues detected."

    parts: list[str] = []
    if test_result.failed_count > 0:
        parts.append(f"{test_result.failed_count} test(s) failed.")

    if test_result.errors:
        parts.append("Failure details:")
        for err in test_result.errors[:10]:
            parts.append(f"  - {err}")

    if test_result.output:
        # Extract FAILURES section from pytest output
        output = test_result.output
        failures_start = output.find("FAILURES")
        if failures_start >= 0:
            parts.append("\n" + output[failures_start:2000])

    return "\n".join(parts) if parts else "Unknown test failure."