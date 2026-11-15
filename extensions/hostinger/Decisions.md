# Architectural Decisions

## 1. Argparse over Click / Typer

**Decision:** Use Python's stdlib `argparse`.

**Rationale:** The CLI surface is tiny — one subcommand with three optional
flags. Argparse handles this without adding a dependency. Click and Typer are
better for larger CLIs with many subcommands, nested groups, or plugin systems.

**Rejected:**
- Click would be fine but adds a dependency for no benefit here.
- Typer is over-engineered for a single-command tool.

## 2. asyncio over threading for parallel probes

**Decision:** Use `asyncio.gather` to run all probes concurrently.

**Rationale:** Every probe spends most of its wall time waiting for subprocesses
or network I/O. Async I/O is the natural fit — no thread-safety issues, no GIL
contention, no thread-pool sizing. `asyncio.subprocess.create_subprocess_exec`
lets us run system commands without blocking the event loop.

**Rejected:**
- `threading.Thread` + `concurrent.futures` — threads add complexity for
  cancellation and result collection; no benefit when all probes are I/O-bound.
- `multiprocessing` — overkill; we're not CPU-bound.

## 3. subprocess (dig / ping / nc / curl) over Python libraries

**Decision:** Shell out to standard system tools rather than using Python-native
implementations (dnspython, pure-python ping, etc.).

**Rationale:** DNS debugging without `dig` is unusual; `ping` is the canonical
way to measure latency; `nc` is the standard port scanner; `curl` is the
definitive HTTP client. System administrators trust these tools and expect the
output to match familiar tool semantics. Every Linux/macOS machine ships them.

**Rejected:**
- dnspython — adds a dependency, doesn't use the system resolver.
- pure-python ping — needs root, unreliable ICMP socket handling.
- python port scanner — `socket.connect_ex` works but `nc` output is more
  readable for sysadmins.
- httpx/requests — add dependencies; curl already handles edge cases (redirects,
  SSL, timeouts).

## 4. Socket fallback for port scanning

**Decision:** When `nc` is not available, fall back to
`asyncio.open_connection`.

**Rationale:** Many minimal Docker containers and Windows systems lack `nc`.
A pure-Python TCP connect is trivial to implement with asyncio and doesn't need
any dependency.

**Rejected:**
- Require `nc` to be installed — less portable.
- Use a third-party library — unnecessary for three lines of code.

## 5. Rich for terminal output

**Decision:** Use the `rich` library for table rendering and colour.

**Rationale:** `rich.Table` handles borders, alignment, per-cell styling, and
Unicode box drawing in a few lines of code. Reimplementing this with raw ANSI
escape codes would be error-prone and verbose.

**Rejected:**
- `tabulate` — doesn't support styled cell colours or Unicode boxes well.
- `colorama` — ANSI wrappers only; no table layout.
- Raw `\033[` codes — fragile, unreadable, no cross-platform guarantees.

## 6. ProbeResult dataclass as the unified result type

**Decision:** All probes return a `ProbeResult` dataclass with `probe`,
`status`, `detail`, and `data` fields.

**Rationale:** A single type means the reporter doesn't need to understand each
probe. The reporter just iterates results and renders them — table or JSON. The
`data` dict carries structured fields for JSON consumers while `detail` holds a
human-readable summary.

**Rejected:**
- Per-probe result types — would require `isinstance` checks in the reporter.
- Plain dicts — no field validation, no `is_ok` helper, no `to_dict()` contract.

## 7. JSON output via `json.dump` to stdout

**Decision:** JSON output writes a single structured object to stdout.

**Rationale:** Scripting consumers (`jq`, shell pipes, dashboards) expect clean
JSON on stdout. Detecting `--json` switches the entire output format cleanly.

**Rejected:**
- JSON Lines (one line per probe) — harder to consume as a single document.
- Mixed output (table to stderr, JSON to stdout) — confusing, violates POLA.

## 8. DNS probe skipped for IP addresses

**Decision:** `run_all_probes` detects if the target is an IP address and skips
DNS resolution.

**Rationale:** Running `dig +short 192.168.1.1` returns nothing useful. An IP
address already *is* the resolved location.

**Rejected:**
- Always run DNS — wastes time; misleading "FAIL: No records" result for IPs.
- Reverse DNS (PTR) — out of scope; this tool debugs forward connectivity.

## 9. Watch mode as an asyncio loop, not cron

**Decision:** `--watch` runs `asyncio.sleep(30)` in a loop with terminal
clearing.

**Rationale:** Pure user-space, no cron dependency, instant interrupt with
Ctrl+C. The loop is free to add jitter, exponential backoff, or interactive
controls later.

**Rejected:**
- Shell `watch` — requires the user to wrap the command; less portable.
- Cron — overkill for an interactive tool.

## 10. `asyncio.gather` over `TaskGroup`

**Decision:** Use `asyncio.gather` for parallel probe execution (Python 3.10
compatible).

**Rationale:** `TaskGroup` (Python 3.11+) provides structured concurrency but
locks the API to 3.11+. `asyncio.gather` works on every supported Python
version and handles our use case (fire and collect all results).

**Rejected:**
- `TaskGroup` — cleaner but breaks Python 3.10 support.
- Sequential execution — defeats the purpose; latency would be additive.

## 11. Graceful degradation for missing tools

**Decision:** Each probe returns a `ProbeResult(status="ERROR")` with a clear
"not available" message when its tool isn't found.

**Rationale:** The tool should never crash with a `FileNotFoundError` stack
trace. A clear message in the results table tells the user what to install
without aborting other probes.

**Rejected:**
- Crash with an error message — hard to read when mixed with other output.
- Install-time dependency check — annoying; let probes run and report.

## 12. Cross-platform ping handling

**Decision:** Detect `sys.platform` and adjust ping flags (`-c` vs `-n`, `-W`
vs `-w`).

**Rationale:** Linux, macOS, and Windows all use different ping syntax. The
30-line platform check is cheap insurance against "unknown flag" errors.

**Rejected:**
- Use a cross-platform ping library — overkill for one flag difference.
- Support only Linux — the user explicitly asked for Windows handling.

## 13. Terminal clearing via `os.system`

**Decision:** Watch mode clears the terminal with `os.system("clear" if not
Windows else "cls")`.

**Rationale:** Simple, portable, works everywhere. A library-based approach
would add a dependency for a single system call every 30 seconds.

**Rejected:**
- `rich.live` — continuous update panel, but watch mode is a full re-run not a
  streaming update.
- `subprocess.run(["clear"])` — works but `os.system` is shorter for this case.

## 14. Low-level `_run_cmd` helper separated from probe logic

**Decision:** Extract `_run_cmd(cmd, timeout)` as a module-private helper that
all probes call.

**Rationale:** Every probe needs to: run a command, capture output, handle
timeout, handle missing tool. Centralising this avoids code duplication and
makes timeout/missing-tool semantics consistent across all probes.

**Rejected:**
- Duplicate `asyncio.create_subprocess_exec` in each probe — error-prone, hard
  to audit.
- `asyncio.subprocess` wrappers from third-party libs — unnecessary for ~20
  lines of code.
