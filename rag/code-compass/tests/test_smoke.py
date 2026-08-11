"""Smoke tests for Code Compass.

Runs against a live FastAPI test server with the sample codebase.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

# Paths
PROJECT_DIR = Path(__file__).parent.parent
SAMPLE_DIR = PROJECT_DIR / "data" / "sample-project"
INDEX_DIR = PROJECT_DIR / "data" / "index"

# Ensure the sample codebase exists
SAMPLE_GENERATOR = PROJECT_DIR / "generate_sample_codebase.py"
if not SAMPLE_DIR.exists():
    print("Generating sample codebase...")
    import subprocess

    subprocess.run([sys.executable, str(SAMPLE_GENERATOR)], cwd=str(PROJECT_DIR), check=True)

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30


def _wait_for_server(max_retries=15, delay=2):
    """Wait for the FastAPI server to be ready."""
    for i in range(max_retries):
        try:
            r = requests.get(f"{BASE_URL}/api/status", timeout=5)
            if r.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        print(f"  Waiting for server (attempt {i + 1}/{max_retries})...")
        time.sleep(delay)
    return False


def test_status():
    """Server status endpoint works."""
    r = requests.get(f"{BASE_URL}/api/status", timeout=TIMEOUT)
    assert r.status_code == 200, f"Status failed: {r.status_code}"
    data = r.json()
    assert data["status"] == "ok", f"Unexpected status: {data}"
    print(f"  [PASS] Server status: {data}")
    return data


def test_ingest():
    """Ingest the sample codebase."""
    r = requests.post(
        f"{BASE_URL}/api/ingest",
        json={"directory_path": str(SAMPLE_DIR)},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Ingest failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"  [PASS] Ingested: {data}")
    assert data["files_ingested"] >= 3, f"Expected >=3 files, got {data['files_ingested']}"
    assert data["chunks_created"] > 0, f"Expected >0 chunks, got {data['chunks_created']}"
    return data


def test_query_main_entry():
    """Query: 'Where is the main entry point?'"""
    r = requests.post(
        f"{BASE_URL}/api/query",
        json={"query": "Where is the main entry point?", "top_k": 3},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Query failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"  [PASS] Query returned answer ({len(data['answer'])} chars)")
    print(f"  Sources: {len(data['sources'])}")
    for src in data["sources"]:
        print(f"    - {src['file_path']}:{src['start_line']} (score: {src['relevance_score']:.3f})")
    # Should find main.py
    files = [s["file_path"] for s in data["sources"]]
    assert any("main.py" in f for f in files), f"Expected main.py in results, got {files}"
    return data


def test_query_validation():
    """Query: 'Find the function that handles validation'"""
    r = requests.post(
        f"{BASE_URL}/api/query",
        json={"query": "Find the function that handles validation", "top_k": 3},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Query failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"  [PASS] Query returned answer ({len(data['answer'])} chars)")
    print(f"  Sources: {len(data['sources'])}")
    for src in data["sources"]:
        print(f"    - {src['file_path']}:{src['start_line']} (score: {src['relevance_score']:.3f})")
    # Should find validators.py
    files = [s["file_path"] for s in data["sources"]]
    assert any(
        "validators" in f for f in files
    ), f"Expected validators in results, got {files}"
    return data


def test_query_classes():
    """Query: 'What classes are defined in this codebase?'"""
    r = requests.post(
        f"{BASE_URL}/api/query",
        json={"query": "What classes are defined in this codebase?", "top_k": 5},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"Query failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"  [PASS] Query returned answer ({len(data['answer'])} chars)")
    print(f"  Sources: {len(data['sources'])}")
    for src in data["sources"]:
        print(f"    - {src['file_path']}:{src['start_line']} (score: {src['relevance_score']:.3f})")
    return data


def test_clear_index():
    """Clear the index."""
    r = requests.post(f"{BASE_URL}/api/clear", timeout=TIMEOUT)
    assert r.status_code == 200, f"Clear failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"  [PASS] Clear: {data}")
    return data


def main():
    print("=" * 60)
    print("Code Compass — Smoke Tests")
    print("=" * 60)
    print()

    if not _wait_for_server():
        print("FAIL: Server did not start in time.")
        sys.exit(1)
    print("  Server is ready.\n")

    failures = []
    tests = [
        ("Status", test_status),
        ("Ingest", test_ingest),
        ("Query: main entry", test_query_main_entry),
        ("Query: validation", test_query_validation),
        ("Query: classes", test_query_classes),
        ("Clear", test_clear_index),
    ]

    for name, fn in tests:
        print(f"--- {name} ---")
        try:
            fn()
        except Exception as e:
            print(f"  [FAIL] {e}")
            failures.append(name)
        print()

    print("=" * 60)
    if failures:
        print(f"FAILED: {len(failures)}/{len(tests)} tests failed: {failures}")
        sys.exit(1)
    else:
        print(f"ALL {len(tests)} TESTS PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()
