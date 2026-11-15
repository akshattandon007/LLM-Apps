"""Async probe implementations using asyncio.subprocess.

Each probe function returns a ProbeResult.  All use _run_cmd to execute
system commands asynchronously, falling back to Python-native sockets
when a tool isn't available.
"""

from __future__ import annotations

import asyncio
import re
import socket
import sys
from typing import Any

from .models import ProbeResult

# ── subprocess helper ────────────────────────────────────────────────────────

# Special return codes from _run_cmd
_RC_TIMEOUT = -1
_RC_NOT_FOUND = -2
_RC_ERROR = -3


async def _run_cmd(
    cmd: list[str],
    timeout: int = 15,
) -> tuple[int, str, str]:
    """Run *cmd* asynchronously and return ``(returncode, stdout, stderr)``.

    Special return codes:
        -1  command timed out
        -2  command not found on ``$PATH``
        -3  unexpected error (message in stderr)
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return (
                proc.returncode if proc.returncode is not None else 0,
                stdout.decode(errors="replace"),
                stderr.decode(errors="replace"),
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass
            return _RC_TIMEOUT, "", "TIMEOUT"
    except FileNotFoundError:
        return _RC_NOT_FOUND, "", "COMMAND_NOT_FOUND"
    except Exception as exc:
        return _RC_ERROR, "", str(exc)


# ── individual probes ────────────────────────────────────────────────────────


async def probe_dns(host: str) -> ProbeResult:
    """Resolve *host* via ``dig +short`` and return A/AAAA records."""
    code, stdout, stderr = await _run_cmd(["dig", "+short", host], timeout=10)

    if code == _RC_NOT_FOUND:
        return ProbeResult(
            "DNS",
            "ERROR",
            "dig not available (install dnsutils / bind-utils)",
            {"error": "dig not found"},
        )
    if code == _RC_TIMEOUT:
        return ProbeResult(
            "DNS", "TIMEOUT", "DNS resolution timed out", {"error": "timeout"}
        )
    if code < 0:
        return ProbeResult(
            "DNS", "ERROR", f"dig failed: {stderr}", {"error": stderr}
        )

    # NXDOMAIN / SERVFAIL is reported via stderr
    stderr_lower = stderr.lower().replace("\n", " ")
    if "nxdomain" in stderr_lower:
        return ProbeResult(
            "DNS", "FAIL", "NXDOMAIN \u2014 domain does not exist", {"ips": []}
        )
    if "servfail" in stderr_lower:
        return ProbeResult(
            "DNS", "FAIL", "SERVFAIL \u2014 DNS server error", {"ips": []}
        )

    lines = [line.strip() for line in stdout.split("\n") if line.strip()]
    ips: list[str] = []
    for line in lines:
        if line.startswith(";"):  # dig comment
            continue
        # CNAME targets end with a dot; A/AAAA records don't
        if line.endswith("."):
            continue
        # Looks like an IP address
        if re.match(r"^[\d.]+$", line) or re.match(
            r"^[0-9a-f:]+$", line, re.IGNORECASE
        ):
            ips.append(line)

    if not ips:
        return ProbeResult(
            "DNS", "FAIL", "No A/AAAA records found", {"ips": [], "raw": lines}
        )

    return ProbeResult(
        "DNS",
        "OK",
        ", ".join(ips),
        {"ips": ips, "count": len(ips)},
    )


async def probe_ping(host: str, count: int = 3) -> ProbeResult:
    """Ping *host* and extract latency / loss statistics."""
    if sys.platform == "win32":
        cmd = ["ping", "-n", str(count), host]
    elif sys.platform == "darwin":
        cmd = ["ping", "-c", str(count), "-W", "5", host]
    else:
        cmd = ["ping", "-c", str(count), "-W", "5", host]

    code, stdout, stderr = await _run_cmd(cmd, timeout=20)

    if code == _RC_NOT_FOUND:
        return ProbeResult(
            "Ping", "ERROR", "ping not available", {"error": "ping not found"}
        )
    if code == _RC_TIMEOUT:
        return ProbeResult(
            "Ping", "TIMEOUT", "Ping timed out", {"error": "timeout"}
        )

    # ---- packet loss ----
    loss_match = re.search(r"(\d+)% packet loss", stdout)
    packet_loss = int(loss_match.group(1)) if loss_match else 100

    if packet_loss == 100:
        return ProbeResult(
            "Ping",
            "FAIL",
            "Host unreachable (100% packet loss)",
            {"packet_loss": 100, "host": host},
        )

    # ---- RTT statistics (Linux: min/avg/max/mdev, macOS: min/avg/max/stddev) ----
    rtt_data: dict[str, Any] = {"packet_loss": packet_loss}
    detail: str = ""

    rtt_match = re.search(
        r"rtt\s+min/avg/max/(?:mdev|stddev)\s*=\s*"
        r"([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+)\s*ms",
        stdout,
    )
    if rtt_match:
        rtt_min, rtt_avg, rtt_max, rtt_mdev = rtt_match.groups()
        detail = (
            f"min {rtt_min} / avg {rtt_avg} / max {rtt_max} \u00b1 {rtt_mdev} ms"
        )
        rtt_data.update(
            {
                "rtt_min_ms": float(rtt_min),
                "rtt_avg_ms": float(rtt_avg),
                "rtt_max_ms": float(rtt_max),
                "rtt_mdev_ms": float(rtt_mdev),
            }
        )
    else:
        # Windows-style or other format: try a looser pattern
        simple = re.search(
            r"(?:min|minimum)\s*=\s*([0-9.]+).*?"
            r"(?:avg|average)\s*=\s*([0-9.]+).*?"
            r"(?:max|maximum)\s*=\s*([0-9.]+)",
            stdout,
            re.DOTALL,
        )
        if simple:
            rtt_min, rtt_avg, rtt_max = simple.groups()
            detail = f"min {rtt_min} / avg {rtt_avg} / max {rtt_max} ms"
            rtt_data.update(
                {
                    "rtt_min_ms": float(rtt_min),
                    "rtt_avg_ms": float(rtt_avg),
                    "rtt_max_ms": float(rtt_max),
                }
            )
        else:
            detail = f"Reachable ({packet_loss}% loss)"
            rtt_data["error"] = "could not parse RTT from ping output"

    return ProbeResult("Ping", "OK" if detail else "FAIL", detail, rtt_data)


async def probe_port(host: str, port: int, timeout: int = 5) -> ProbeResult:
    """Check if *port* on *host* is open using ``nc`` or a socket fallback."""
    name = f"Port {port}"

    code, _, stderr = await _run_cmd(
        ["nc", "-zv", "-w", str(timeout), host, str(port)],
        timeout=timeout + 2,
    )

    if code == _RC_NOT_FOUND:
        return await _probe_port_socket(host, port, timeout)
    if code == _RC_TIMEOUT:
        return ProbeResult(
            name,
            "TIMEOUT",
            f"Port {port} connection timed out",
            {"port": port, "open": False, "error": "timeout"},
        )
    if code == 0:
        return ProbeResult(
            name,
            "OPEN",
            f"Port {port} is open",
            {"port": port, "open": True},
        )

    # nc returned non-zero → port closed / host unreachable
    err = (stderr or "connection refused").strip()
    return ProbeResult(
        name,
        "CLOSED",
        f"Port {port}: {err}",
        {"port": port, "open": False, "error": err},
    )


async def _probe_port_socket(host: str, port: int, timeout: int) -> ProbeResult:
    """Fallback port check using ``asyncio.open_connection``."""
    name = f"Port {port}"
    try:
        _, _ = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        return ProbeResult(
            name,
            "OPEN",
            f"Port {port} is open",
            {"port": port, "open": True},
        )
    except asyncio.TimeoutError:
        return ProbeResult(
            name,
            "TIMEOUT",
            f"Port {port} connection timed out",
            {"port": port, "open": False, "error": "timeout"},
        )
    except ConnectionRefusedError:
        return ProbeResult(
            name,
            "CLOSED",
            f"Port {port}: connection refused",
            {"port": port, "open": False, "error": "connection refused"},
        )
    except OSError as exc:
        return ProbeResult(
            name,
            "CLOSED",
            f"Port {port}: {exc}",
            {"port": port, "open": False, "error": str(exc)},
        )


async def probe_http(host: str, scheme: str = "http") -> ProbeResult:
    """Fetch *scheme*://*host* and return status code, timing, content type."""
    url = f"{scheme}://{host}"
    label = f"HTTP {scheme}"
    null_dev = "NUL" if sys.platform == "win32" else "/dev/null"

    code, stdout, stderr = await _run_cmd(
        [
            "curl",
            "-s",
            "-o", null_dev,
            "-w", "%{http_code} %{time_total} %{content_type}",
            "--connect-timeout", "10",
            "--max-time", "15",
            url,
        ],
        timeout=18,
    )

    if code == _RC_NOT_FOUND:
        return ProbeResult(
            label, "ERROR", "curl not available", {"error": "curl not found"}
        )
    if code == _RC_TIMEOUT:
        return ProbeResult(
            label,
            "TIMEOUT",
            f"{url} \u2014 connection timed out",
            {"url": url, "error": "timeout"},
        )

    if code != 0:
        err = (stderr or f"curl exit {code}").strip()
        return ProbeResult(
            label,
            "FAIL",
            f"{url} \u2014 {err}",
            {"url": url, "error": err},
        )

    parts = stdout.strip().split(" ", 2)
    status_code_str = parts[0] if len(parts) > 0 else "000"
    time_total_str = parts[1] if len(parts) > 1 else "0"
    content_type_str = parts[2] if len(parts) > 2 else "unknown"

    is_ok = status_code_str.startswith("2") or status_code_str.startswith("3")
    status_label = "OK" if is_ok else "FAIL"

    return ProbeResult(
        label,
        status_label,
        f"{status_code_str} \u00b7 {time_total_str}s \u00b7 {content_type_str}",
        {
            "url": url,
            "status_code": int(status_code_str),
            "time_seconds": float(time_total_str),
            "content_type": content_type_str,
        },
    )


# ── orchestration ────────────────────────────────────────────────────────────


def _is_ip_address(host: str) -> bool:
    """Return *True* if *host* is a valid IPv4 or IPv6 address."""
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(family, host)
            return True
        except (OSError, socket.error):
            continue
    return False


async def run_all_probes(host: str) -> list[ProbeResult]:
    """Run all relevant probes in parallel via ``asyncio.gather``.

    DNS probe is skipped when *host* is a raw IP address.
    Results are returned in a fixed order: DNS \u2192 Ping \u2192 Ports \u2192 HTTP.
    """
    skip_dns = _is_ip_address(host)

    tasks = []

    if not skip_dns:
        tasks.append(probe_dns(host))
    tasks.append(probe_ping(host))
    tasks.append(probe_port(host, 80))
    tasks.append(probe_port(host, 443))
    tasks.append(probe_http(host, "http"))
    tasks.append(probe_http(host, "https"))

    results = await asyncio.gather(*tasks)

    # Sort into a consistent order
    rank: dict[str, int] = {
        "DNS": 0,
        "Ping": 1,
        "Port 80": 2,
        "Port 443": 3,
        "HTTP http": 4,
        "HTTP https": 5,
    }
    results.sort(key=lambda r: rank.get(r.probe, 99))
    return results
