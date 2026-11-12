# Decisions — ISBNScan

## 1. Open Library API over Google Books API

**Decision:** Use Open Library's Books API (free, no key required) instead of Google Books API (requires API key, quota limits).
**Rejected:** Google Books API — requires a Google Cloud project, API key setup, and has daily quota limits. Open Library is simpler to use and has no auth overhead.
**Trade-off:** Open Library's coverage may be slightly less complete for very recent or niche publications, but it covers the vast majority of commercially published books with ISBNs.

## 2. CLI tool over web app or GUI

**Decision:** Build as a command-line tool rather than a web application or GUI.
**Rejected:** Web app would require a server, database, frontend framework, and hosting — excessive complexity for a batch lookup tool. GUI adds platform dependency.
**Trade-off:** Less accessible to non-technical users, but far simpler to build, install, and maintain. The CSV export bridges the gap for spreadsheet users.

## 3. Individual API calls per ISBN over batch endpoint

**Decision:** Make individual API calls for each ISBN rather than trying to batch them.
**Rejected:** Open Library does support batch via multiple bibkeys in one request (`bibkeys=ISBN:...&bibkeys=ISBN:...`), but the response structure is a flat dict keyed by bibkey — effectively the same result as individual calls. The `batch_lookup()` function is a convenience loop.
**Trade-off:** Slightly more HTTP overhead for large batches, but the API response time is typically <500ms per call and the code is simpler.

## 4. httpx over requests library

**Decision:** Use `httpx` instead of `requests` for HTTP calls.
**Rejected:** `requests` is more widely known, but `httpx` has first-class `MockTransport` support for hermetic tests without monkey-patching.
**Trade-off:** Slightly less familiar API, but vastly better test isolation.

## 5. Per-ISBN client reuse over creating a new client each time

**Decision:** Accept an optional `httpx.Client` parameter in `lookup_isbn()` and create a default one if not provided.
**Rejected:** Always creating a new client wastes connection resources; requiring callers to always provide one adds friction.
**Trade-off:** A small amount of conditional logic in the function, but it's both flexible and ergonomic.

## 6. Clean ISBN normalization before lookup

**Decision:** Strip all non-digit characters and uppercase trailing 'X' before querying.
**Rejected:** Passing raw user input (with dashes, spaces, "ISBN:" prefix) directly to the API.
**Trade-off:** The API might handle some formats natively, but normalization is cheap and ensures consistent behavior regardless of input format.

## 7. Dataclass for BookResult over plain dict or NamedTuple

**Decision:** Use a `@dataclass` with typed fields for book lookup results.
**Rejected:** Plain dict has no type safety or IDE autocomplete; NamedTuple is immutable and less flexible for CSV serialization.
**Trade-off:** Slightly more verbose declaration, but cleaner access patterns and easier serialization with `asdict()`.

## 8. Colorized terminal output over plain text always

**Decision:** Use ANSI color codes when stdout is a TTY, disable when piped.
**Rejected:** Always using colors would embed escape codes in piped output; never using colors makes the terminal experience worse.
**Trade-off:** Requires detecting TTY state, which is one extra check. Well-established pattern (same as `ls --color=auto`).

## 9. File-based ISBN input over interactive mode

**Decision:** Support `--file` and `--stdin` for batch ISBN input rather than an interactive REPL.
**Rejected:** Interactive mode would be more beginner-friendly but adds a lot of state management code. File/stdin covers the batch-use case.
**Trade-off:** Users must prepare a file or pipe data, but the tool stays simple and composable with Unix pipelines.

## 10. Single CLI entry point over subcommands

**Decision:** One `isbnscan` command with options (`--file`, `--csv`, `--stdin`) rather than subcommands like `isbnscan lookup`, `isbnscan export`.
**Rejected:** Subcommands add complexity for a tool that does one thing. The tool is simple enough that options suffice.
**Trade-off:** If future features (e.g., `isbnscan validate`, `isbnscan compare`) are added, subcommands may become necessary. Easy to refactor to subcommands later.

## 11. pytest over unittest

**Decision:** Use pytest for tests instead of Python's built-in unittest.
**Rejected:** unittest is more verbose, requires class boilerplate, and has worse assertion introspection.
**Trade-off:** pytest is a dependency, but it's the de facto standard for Python testing and is installed separately in CI.

## 12. No caching layer

**Decision:** Don't implement local caching of lookup results.
**Rejected:** Adding SQLite or file-based caching would speed up repeated lookups of the same ISBNs.
**Trade-off:** Each run queries the API fresh. For most use cases (a few dozen ISBNs at a time), this is fast enough. Caching can be added later if needed.

## 13. pyproject.toml over requirements.txt + setup.py

**Decision:** Use a single `pyproject.toml` for both build config and dependency declarations.
**Rejected:** The legacy `setup.py` + `requirements.txt` pattern works but is deprecated. Modern Python packaging standardizes on `pyproject.toml`.
**Trade-off:** Requires setuptools>=64, but that's a reasonable minimum for Python 3.10+.
