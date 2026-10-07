"""Smoke tests for ManualMate — verifies CLI responds and help works."""

import os
import subprocess
import sys


def test_cli_help():
    """ManualMate CLI should display help without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "manualmate", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
        env={**os.environ, "OPENAI_API_KEY": "sk-test-placeholder"},
    )
    assert result.returncode == 0
    assert "ManualMate" in result.stdout or "ingest" in result.stdout


def test_cli_ingest_help():
    """Ingest subcommand should display help."""
    result = subprocess.run(
        [sys.executable, "-m", "manualmate", "ingest", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
        env={**os.environ, "OPENAI_API_KEY": "sk-test-placeholder"},
    )
    assert result.returncode == 0
    assert "FILEPATH" in result.stdout or "FILE" in result.stdout


def test_cli_ask_help():
    """Ask subcommand should display help."""
    result = subprocess.run(
        [sys.executable, "-m", "manualmate", "ask", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
        env={**os.environ, "OPENAI_API_KEY": "sk-test-placeholder"},
    )
    assert result.returncode == 0
    assert "QUESTION" in result.stdout or "question" in result.stdout