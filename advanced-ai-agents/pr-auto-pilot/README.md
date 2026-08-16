# ✈️ PR Auto-Pilot

**Your PRs, reviewed — bugs caught, patches written, tests green, all before you wake up.**

PR Auto-Pilot is an end-to-end PR review agent. Point it at a GitHub pull request and it fetches the diff, runs a four-pass LLM review (logic, security, edge cases, performance), generates patches for every issue it finds, applies them, runs the test suite, and iterates until everything passes or it runs out of rounds. It then produces a structured markdown report — optionally posted straight to the PR as a comment.

---

## How it works

```
       ┌─────────────┐
       │  GitHub PR   │
       └──────┬──────┘
              │
    ┌─────────▼──────────┐
    │ 1. Fetch diff       │  httpx + GitHub API
    │ 2. Clone repo       │  gitpython → /tmp/pr-autopilot-repos/
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │ 3. Multi-pass review│  Four LLM passes per file:
    │                     │   🔍 Logic · 🔒 Security
    │                     │   ⚠️  Edge Cases · ⚡ Performance
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │ 4. Patch & apply    │  Generate unified diffs, git apply
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │ 5. Run tests        │  Detect & run pytest / unittest
    └─────────┬──────────┘
              │
         ┌────▼────┐
         │ Pass?   │──No──→ Rollback → re-analyze
         └────┬────┘         (up to 3 iterations)
              │ Yes
    ┌─────────▼──────────┐
    │ 6. Post report      │  Structured markdown → PR comment
    └────────────────────┘
```

Each iteration is a full loop: re-patch the unfixed issues, re-run tests, and if they fail, roll everything back with `git checkout -- .` and try again with fresh analysis. The agent stops when tests pass or it hits `--max-iterations` (default: 3).

---

## Quick start

```bash
# 1. Clone and enter the project
git clone <this-repo>
cd pr-auto-pilot

# 2. Set up environment
cp .env.example .env
# Edit: add your GITHUB_TOKEN and ANTHROPIC_API_KEY

# 3. Install dependencies
pip install -r requirements.txt

# 4. Review a PR
python main.py --pr-url https://github.com/owner/repo/pull/42

# Dry-run (no comment posted to GitHub):
python main.py --pr-url https://github.com/owner/repo/pull/42 --no-post

# Point at an existing local clone (skips the clone step):
python main.py --pr-url https://github.com/owner/repo/pull/42 \
               --repo-path /home/user/my-project
```

---

## Example report snippet

```
# PR Auto-Pilot Review — owner/demo-repo#42

## Summary
Found **1 critical** issue(s) that should be addressed before merging.

**Confidence:** 85% [████████░░]
**Iterations:** 2
**Files changed:** 1
**Issues found:** 2

## Issues Found

### 🔴 Critical
| # | File | Lines | Category | Issue | Confidence |
|---|------|-------|----------|-------|------------|
| 1 | `src/calculator.py` | L2 | logic | Division by zero | 95% |

**1. Division by zero** (`src/calculator.py`:2)
   - **Category:** logic
   - **Confidence:** 95%
   - **Description:** The divide function does not handle division by zero.
   - **Suggested fix:**
     ```
     def divide(a, b):
     +    if b == 0:
     +        return None
         return a / b
     ```

## Patches Applied
- **1** patches applied successfully

### Patch: `src/calculator.py`
```diff
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,3 +1,5 @@
 def divide(a, b):
+    if b == 0:
+        return None
     return a / b
```

## Test Results
**Status:** ✅ PASSED
**Duration:** 1.2s
**Total:** 5 | **Passed:** 5 | **Failed:** 0
```

---

## CLI options

| Flag | Description |
|------|-------------|
| `--pr-url` (required) | Full GitHub PR URL |
| `--repo-path` | Path to existing local clone (skips clone step) |
| `--no-post` | Skip posting the review comment to GitHub |
| `--max-iterations` | Max patch-test-rollback iterations (default: 3) |
| `--verbose`, `-v` | Detailed progress output |

---

## Review categories

Each changed file is reviewed through four lenses:

| Category | What it catches |
|----------|----------------|
| **Logic** 🔍 | Incorrect conditionals, off-by-one, wrong data flow, dead code, missing returns |
| **Security** 🔒 | Injection, hardcoded secrets, missing validation, OWASP Top 10 |
| **Edge cases** ⚠️ | Null dereferences, boundary conditions, resource leaks, race conditions |
| **Performance** ⚡ | N+1 queries, O(n²) algorithms, unnecessary allocations, blocking I/O in async code |

The LLM scores every issue with a confidence rating (0.0–1.0) and a severity: **critical**, **major**, **minor**, or **suggestion**. Only critical and major issues trigger the patch-test loop.

---

## Project structure

```
pr-auto-pilot/
├── main.py                  # CLI entry point — the pipeline orchestrator
├── requirements.txt
├── .env.example             # GITHUB_TOKEN, ANTHROPIC_API_KEY
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── models.py            # Pydantic models (Issue, Patch, ReviewReport, etc.)
│   ├── github_client.py     # GitHub API wrapper (fetch diff, post comments)
│   ├── reviewer.py          # LLM-powered multi-pass review pipeline
│   ├── patcher.py           # Patch generation, git apply, rollback
│   ├── tester.py            # Test runner (auto-detect pytest/unittest/npm/cargo)
│   └── reporter.py          # Structured markdown report formatter
└── tests/
    ├── __init__.py
    ├── conftest.py           # Fixtures + FakeGitHubClient test double
    └── test_smoke.py         # Smoke tests (no real network calls)
```

---

## Tech stack

| Layer | What |
|-------|------|
| **Language** | Python 3.12+ |
| **HTTP** | [httpx](https://www.python-httpx.org/) — GitHub API calls |
| **Git** | [GitPython](https://gitpython.readthedocs.io/) — clone, checkout, apply patches, rollback |
| **Models** | [Pydantic](https://docs.pydantic.dev/) — typed data structures |
| **LLM** | [Anthropic Claude](https://docs.anthropic.com/) — multi-pass code review (swappable; supports OpenAI too) |
| **Testing** | [pytest](https://docs.pytest.org/) — test runner + test doubles |
| **Config** | [python-dotenv](https://pypi.org/project/python-dotenv/) — API key management |

---

## Testing

```bash
# Run the smoke tests (no real API keys needed)
pytest tests/ -v
```

All tests use `FakeGitHubClient` — a mock httpx client that returns canned PR data. No real network calls, no API keys required.

---

## Setup

### API keys

Create a `.env` file in the project root:

```bash
# GitHub personal access token with repo scope
GITHUB_TOKEN=ghp_your_token_here

# Anthropic API key (Claude powers the review)
ANTHROPIC_API_KEY=sk-ant_your_key_here
```

**`GITHUB_TOKEN`** — Create one at https://github.com/settings/tokens with the `repo` scope (for private repos) or `public_repo` (for public repos only).

**`ANTHROPIC_API_KEY`** — Get one at https://console.anthropic.com/ and make sure it has access to `claude-sonnet-4-20250514`.

### Running without API keys

If `ANTHROPIC_API_KEY` is not set, the reviewer falls back to a pattern-based simulated review that catches debug statements left in code, TODO comments, and potential hardcoded secrets. Good for a quick sanity check.

If `GITHUB_TOKEN` is not set (or `--no-post` is passed), the report is printed to stdout but not posted to the PR.