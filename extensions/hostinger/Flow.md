# Flow — call chains, data flow, and module dependencies

## Module dependency graph

```
__main__.py  ──────────────┐
                           │
__init__.py  (version)     │
                           ↓
cli.py  ───────────────────┬─────────────────────┐
                           │                     │
                    probes.py                reporter.py
                           │                     │
                    models.py              models.py
```

**Dependency direction:** `__main__` → `cli` → `probes` + `reporter`.
Both `probes` and `reporter` import `models`.

## Data flow

```
CLI input (argparse)
      │ host, --json, --watch
      ▼
run_check()
      │
      ▼
probes.run_all_probes(host)          ─────▶ results: list[ProbeResult]
      │                                        ▲         ▲         ▲
      │  asyncio.gather                         │         │         │
      ├── probe_dns(host)          ──────────────┘         │         │
      ├── probe_ping(host)         ────────────────────────┘         │
      ├── probe_port(host, 80)     ──────────────────────────────────┘
      ├── probe_port(host, 443)    ───────────────────────────────────┘
      ├── probe_http(host, "http") ──────────────────────────────────┘
      └── probe_http(host, "https")
      │
      ▼  (results, host, json_mode)
reporter.print_output(results, host, json_mode)
      │
      ├── json_mode=False ──▶ print_table() ──▶ build_table() ──▶ rich.Table → stderr
      └── json_mode=True  ──▶ print_json()  ──▶ json.dump()    → stdout
```

## Entry-point call chain

```
$ python -m hostinger check example.com
  │
  └── hostinger/__main__.py
        └── main()
              │
              └── cli.py::main()
                    │
                    ├── build_parser() → argparse parser
                    ├── parse_args()   → namespace(host, json, watch)
                    │
                    └── asyncio.run(run_check(host, json, watch))
                          │
                          ├── watch=False: run_once
                          │     └─ probes.run_all_probes(host)
                          │           └─ asyncio.gather(probe_*)
                          │     └─ reporter.print_output(results, host, json)
                          │
                          └── watch=True: loop
                                └─ while True:
                                      ├── clear terminal
                                      ├── probes.run_all_probes(host)
                                      ├── reporter.print_output(results, host, False)
                                      └── asyncio.sleep(30)
```

## Function-level call chains

### _run_cmd (shared by every probe)

```python
_run_cmd(cmd: list[str], timeout: int=15) -> tuple[int, str, str]
    │
    └─ asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
         │
         ├─ await proc.communicate()
         │     │
         │     └─ asyncio.wait_for(..., timeout=timeout)
         │           │
         │           ├─ success → (returncode, stdout_str, stderr_str)
         │           └─ TimeoutError → proc.kill() / return (-1, "", "TIMEOUT")
         │
         ├─ FileNotFoundError → return (-2, "", "COMMAND_NOT_FOUND")
         └─ Exception → return (-3, "", str(exc))
```

### probe_dns

```python
probe_dns(host: str) -> ProbeResult
    │
    └─ _run_cmd(["dig", "+short", host], timeout=10)
         │
         ├─ -2 (not found)      → ERROR "dig not available"
         ├─ -1 (timeout)        → TIMEOUT
         ├─ NXDOMAIN in stderr  → FAIL "NXDOMAIN"
         ├─ SERVFAIL in stderr   → FAIL "SERVFAIL"
         ├─ no valid IPs        → FAIL "No A/AAAA records"
         └─ has IPs             → OK (e.g. "93.184.216.34")
```

### probe_ping

```python
probe_ping(host: str, count: int=3) -> ProbeResult
    │
    ├─ platform="win32"   → cmd: ["ping", "-n", count, host]
    ├─ platform="darwin"  → cmd: ["ping", "-c", count, "-W", "5", host]
    └─ default (linux)    → cmd: ["ping", "-c", count, "-W", "5", host]
    │
    └─ _run_cmd(cmd, timeout=20)
         │
         ├─ -2 (not found)         → ERROR
         ├─ -1 (timeout)           → TIMEOUT
         ├─ 100% packet loss       → FAIL "Host unreachable"
         ├─ RTT parsed (mdev)      → OK "min X / avg Y / max Z ms"
         ├─ RTT parsed (stddev)    → OK (macOS variant)
         └─ RTT parsed (simple)    → OK "min X / avg Y / max Z ms"
```

### probe_port

```python
probe_port(host: str, port: int, timeout: int=5) -> ProbeResult
    │
    └─ _run_cmd(["nc", "-zv", "-w", timeout, host, str(port)])
         │
         ├─ -2 (nc not found)  → _probe_port_socket(host, port, timeout)
         │                         └─ asyncio.open_connection(host, port)
         │                               ├─ success      → OPEN
         │                               ├─ TimeoutError → TIMEOUT
         │                               └─ OSError     → CLOSED
         ├─ -1 (timeout)        → TIMEOUT
         ├─ exit 0              → OPEN
         └─ exit ≠ 0            → CLOSED
```

### probe_http

```python
probe_http(host: str, scheme: str="http") -> ProbeResult
    │
    └─ _run_cmd(["curl", "-s", "-o", "/dev/null",
                 "-w", "%{http_code} %{time_total} %{content_type}",
                 "--connect-timeout", "10", "--max-time", "15", url])
         │
         ├─ -2 (not found)         → ERROR "curl not available"
         ├─ -1 (timeout)           → TIMEOUT
         ├─ curl exit ≠ 0           → FAIL (connection error)
         ├─ 2xx or 3xx status      → OK "200 · 0.187s · text/html"
         └─ 4xx or 5xx status      → FAIL "404 · 0.100s · text/html"
```

### run_all_probes (orchestrator)

```python
run_all_probes(host: str) -> list[ProbeResult]
    │
    ├─ _is_ip_address(host)?
    │     ├─ True  → skip DNS probe (5 coroutines)
    │     └─ False → include DNS probe (6 coroutines)
    │
    ├─ asyncio.gather(*tasks)
    │     └─ all probes run concurrently
    │
    └─ results.sort(key=rank)   ← fixed order: DNS, Ping, Port 80/443, HTTP http/https
```

## Probe latency assumptions

Each probe has a generous timeout so slow hosts don't hang the CLI:

| Probe      | Command timeout | Total deadline |
|------------|-----------------|----------------|
| DNS        | 10 s            | asyncio.gather |
| Ping       | 20 s            | (all finish at |
| Port (nc)  | 7 s  (5+2)      |  the same time)|
| Port (soc) | 5 s             |                |
| HTTP       | 18 s            |                |

Because `asyncio.gather` waits for the *slowest* probe, total wall time is
bounded by the longest probe (typically ping or HTTP at ~18-20 s).
