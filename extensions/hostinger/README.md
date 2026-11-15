# hostinger

Debug why a host is down — DNS, ping, port scan, and HTTP check, all run in
parallel and displayed in a single colour-coded table.

## What it does

```
hostinger check example.com
hostinger check example.com --json
hostinger check example.com --watch
hostinger check 192.168.1.1
```

Four probes run simultaneously:

| Probe   | Command                        | What you see                          |
|---------|--------------------------------|---------------------------------------|
| DNS     | `dig +short <host>`            | Resolved IPs, NXDOMAIN                |
| Ping    | `ping -c 3 <host>`             | min/avg/max latency, packet loss      |
| Port    | `nc -zv <host> 80/443`         | OPEN / CLOSED per port                |
| HTTP    | `curl -s -w <format> <url>`    | Status code, response time, type      |

## Installation

```bash
pip install rich
```

Or from the project:

```bash
cd hostinger
pip install -r requirements.txt
```

## Usage

```bash
# Run all probes
python -m hostinger check example.com

# JSON output (for scripting)
python -m hostinger check example.com --json

# Watch mode — re-check every 30 seconds
python -m hostinger check example.com --watch

# IP addresses (skips DNS)
python -m hostinger check 192.168.1.1
```

## Output

Default output is a colourised table (uses `rich`):

```
┌───────────────────────────────────────────────────────────┐
│ hostinger — host diagnostics for example.com              │
├──────────┬──────────┬─────────────────────────────────────┤
│ PROBE    │ STATUS   │ DETAILS                             │
├──────────┼──────────┼─────────────────────────────────────┤
│ DNS      │ ✅ OK   │ 93.184.216.34                        │
│ Ping     │ ✅ OK   │ min 42.1 / avg 44.3 / max 47.2 ms   │
│ Port 80  │ ✅ OPEN │ Port 80 is open                      │
│ Port 443 │ ✅ OPEN │ Port 443 is open                     │
│ HTTP http│ ✅ 200   │ 0.187s · text/html                   │
│ HTTP https│ ✅ 200  │ 0.201s · text/html                   │
└──────────┴──────────┴─────────────────────────────────────┘
```

Colours: green for OK/OPEN, red for FAIL/CLOSED, yellow for TIMEOUT/ERROR.

JSON mode outputs structured data suitable for alerts or dashboards:

```json
{
  "host": "example.com",
  "results": [
    { "probe": "DNS", "status": "OK", "detail": "93.184.216.34",
      "data": { "ips": ["93.184.216.34"], "count": 1 } },
    ...
  ]
}
```

## Requirements

- Python 3.10+
- `rich` (pip package)
- System tools: `dig`, `ping`, `nc`, `curl` (standard on most Linux/macOS systems)

When a tool is missing the probe shows "not available" instead of crashing.
For port scanning, `hostinger` falls back to Python sockets when `nc` is
absent.

## Running tests

```bash
pip install pytest pytest-asyncio
cd hostinger
pytest tests/
```

## Project structure

```
hostinger/
├── __init__.py       # Package metadata
├── __main__.py       # python -m hostinger entry
├── cli.py            # Argparse CLI definition
├── probes.py         # DNS, Ping, Port, HTTP probes (asyncio)
├── reporter.py       # Rich table rendering + JSON output
├── models.py         # ProbeResult dataclass
├── tests/
│   ├── conftest.py   # Path setup
│   └── test_probes.py # 38 mock-based tests
├── requirements.txt
├── pytest.ini
├── README.md
├── Decisions.md
└── Flow.md
```
