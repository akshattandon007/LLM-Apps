"""Mock-based tests for every probe function.

All network calls are replaced by patches on ``_run_cmd`` so tests run
without external tools or network access.
"""

from __future__ import annotations

import asyncio
import json
import re
from unittest.mock import AsyncMock, patch

import pytest

from hostinger.models import ProbeResult
from hostinger.probes import (
    _is_ip_address,
    _run_cmd,
    probe_dns,
    probe_http,
    probe_ping,
    probe_port,
    run_all_probes,
)

# =============================================================================
#  _run_cmd helper
# =============================================================================


class TestRunCmd:
    """Test the _run_cmd helper directly (still mocked at a lower level)."""

    @patch("hostinger.probes.asyncio.create_subprocess_exec")
    async def test_normal(self, mock_spawn):
        """Normal execution returns (code, stdout, stderr)."""
        proc = AsyncMock()
        proc.communicate.return_value = (b"hello\n", b"")
        proc.returncode = 0
        mock_spawn.return_value = proc

        rc, out, err = await _run_cmd(["echo", "hello"])
        assert rc == 0
        assert out == "hello\n"
        assert err == ""

    @patch("hostinger.probes.asyncio.create_subprocess_exec")
    async def test_timeout(self, mock_spawn):
        """Timeout returns rc=-1."""
        proc = AsyncMock()
        proc.communicate.side_effect = asyncio.TimeoutError()
        mock_spawn.return_value = proc

        rc, out, err = await _run_cmd(["sleep", "99"], timeout=1)
        assert rc == -1
        assert err == "TIMEOUT"

    @patch("hostinger.probes.asyncio.create_subprocess_exec")
    async def test_not_found(self, mock_spawn):
        """FileNotFoundError returns rc=-2."""
        mock_spawn.side_effect = FileNotFoundError()

        rc, out, err = await _run_cmd(["nonexistent_tool"])
        assert rc == -2
        assert err == "COMMAND_NOT_FOUND"


# =============================================================================
#  DNS probe
# =============================================================================


class TestDNSProbe:
    @patch("hostinger.probes._run_cmd")
    async def test_ok_ipv4(self, mock_run_cmd):
        """Single IPv4 address resolves successfully."""
        mock_run_cmd.return_value = (0, "93.184.216.34\n", "")
        result = await probe_dns("example.com")
        assert result.status == "OK"
        assert "93.184.216.34" in result.detail
        assert result.data["ips"] == ["93.184.216.34"]

    @patch("hostinger.probes._run_cmd")
    async def test_ok_multiple_ips(self, mock_run_cmd):
        """Multiple IPs (IPv4 + IPv6)."""
        mock_run_cmd.return_value = (
            0,
            "93.184.216.34\n2606:2800:220:1:248:1893:25c8:1946\n",
            "",
        )
        result = await probe_dns("example.com")
        assert result.status == "OK"
        assert len(result.data["ips"]) == 2

    @patch("hostinger.probes._run_cmd")
    async def test_ok_cname_filtered(self, mock_run_cmd):
        """CNAME records (ending with '.') are filtered out."""
        mock_run_cmd.return_value = (
            0,
            "example.com.\n93.184.216.34\n",
            "",
        )
        result = await probe_dns("www.example.com")
        assert result.status == "OK"
        assert result.data["ips"] == ["93.184.216.34"]

    @patch("hostinger.probes._run_cmd")
    async def test_nxdomain(self, mock_run_cmd):
        """NXDOMAIN in stderr produces FAIL."""
        mock_run_cmd.return_value = (0, "", ";; NXDOMAIN\n")
        result = await probe_dns("nonexistent.example")
        assert result.status == "FAIL"
        assert "NXDOMAIN" in result.detail

    @patch("hostinger.probes._run_cmd")
    async def test_servfail(self, mock_run_cmd):
        """SERVFAIL in stderr produces FAIL."""
        mock_run_cmd.return_value = (0, "", ";; SERVFAIL\n")
        result = await probe_dns("bad.example")
        assert result.status == "FAIL"

    @patch("hostinger.probes._run_cmd")
    async def test_empty_stdout(self, mock_run_cmd):
        """No records returned produces FAIL."""
        mock_run_cmd.return_value = (0, "", "")
        result = await probe_dns("empty.example")
        assert result.status == "FAIL"
        assert "No" in result.detail or "no" in result.detail

    @patch("hostinger.probes._run_cmd")
    async def test_timeout(self, mock_run_cmd):
        """Timeout returns TIMEOUT."""
        mock_run_cmd.return_value = (-1, "", "TIMEOUT")
        result = await probe_dns("slow.example")
        assert result.status == "TIMEOUT"

    @patch("hostinger.probes._run_cmd")
    async def test_dig_not_found(self, mock_run_cmd):
        """Missing dig tool returns ERROR."""
        mock_run_cmd.return_value = (-2, "", "COMMAND_NOT_FOUND")
        result = await probe_dns("example.com")
        assert result.status == "ERROR"
        assert "not available" in result.detail


# =============================================================================
#  Ping probe
# =============================================================================


class TestPingProbe:
    _PING_OK_LINUX = (
        "PING example.com (93.184.216.34) 56(84) bytes of data.\n"
        "64 bytes from 93.184.216.34: icmp_seq=1 ttl=52 time=42.1 ms\n"
        "64 bytes from 93.184.216.34: icmp_seq=2 ttl=52 time=44.3 ms\n"
        "64 bytes from 93.184.216.34: icmp_seq=3 ttl=52 time=47.2 ms\n"
        "\n"
        "--- example.com ping statistics ---\n"
        "3 packets transmitted, 3 received, 0% packet loss, time 2004ms\n"
        "rtt min/avg/max/mdev = 42.123/44.456/47.789/2.345 ms\n"
    )

    _PING_LOSS = (
        "PING example.com (93.184.216.34) 56(84) bytes of data.\n"
        "\n"
        "--- example.com ping statistics ---\n"
        "3 packets transmitted, 0 received, 100% packet loss, time 2004ms\n"
    )

    @patch("hostinger.probes._run_cmd")
    async def test_ok(self, mock_run_cmd):
        """Successful ping with RTT stats."""
        mock_run_cmd.return_value = (0, self._PING_OK_LINUX, "")
        result = await probe_ping("example.com")
        assert result.status == "OK"
        assert "42.123" in result.detail
        assert result.data["rtt_avg_ms"] == 44.456
        assert result.data["rtt_mdev_ms"] == 2.345

    @patch("hostinger.probes._run_cmd")
    async def test_packet_loss_100(self, mock_run_cmd):
        """100% loss returns FAIL."""
        mock_run_cmd.return_value = (0, self._PING_LOSS, "")
        result = await probe_ping("unreachable.example")
        assert result.status == "FAIL"
        assert "100%" in result.detail

    @patch("hostinger.probes._run_cmd")
    async def test_timeout(self, mock_run_cmd):
        """Timeout returns TIMEOUT."""
        mock_run_cmd.return_value = (-1, "", "TIMEOUT")
        result = await probe_ping("slow.example")
        assert result.status == "TIMEOUT"

    @patch("hostinger.probes._run_cmd")
    async def test_not_found(self, mock_run_cmd):
        """Missing ping returns ERROR."""
        mock_run_cmd.return_value = (-2, "", "COMMAND_NOT_FOUND")
        result = await probe_ping("example.com")
        assert result.status == "ERROR"

    @patch("hostinger.probes._run_cmd")
    async def test_macos_stddev(self, mock_run_cmd):
        """macOS reports stddev instead of mdev."""
        macos_out = self._PING_OK_LINUX.replace("mdev", "stddev")
        mock_run_cmd.return_value = (0, macos_out, "")
        result = await probe_ping("example.com")
        assert result.status == "OK"
        assert result.data["rtt_avg_ms"] == 44.456

    @patch("hostinger.probes._run_cmd")
    async def test_partial_loss_ok(self, mock_run_cmd):
        """Partial loss with some success is still OK."""
        partial = self._PING_OK_LINUX.replace("3 received", "2 received")
        partial = partial.replace("0% packet loss", "33% packet loss")
        mock_run_cmd.return_value = (0, partial, "")
        result = await probe_ping("flaky.example")
        assert result.status == "OK"


# =============================================================================
#  Port probe
# =============================================================================


class TestPortProbe:
    @patch("hostinger.probes._run_cmd")
    async def test_open_via_nc(self, mock_run_cmd):
        """nc reports port open (exit 0)."""
        mock_run_cmd.return_value = (0, "", "succeeded!")
        result = await probe_port("example.com", 80)
        assert result.status == "OPEN"
        assert result.data["open"] is True

    @patch("hostinger.probes._run_cmd")
    async def test_closed_via_nc(self, mock_run_cmd):
        """nc reports port closed (exit 1)."""
        mock_run_cmd.return_value = (1, "", "connection refused")
        result = await probe_port("example.com", 81)
        assert result.status == "CLOSED"
        assert result.data["open"] is False

    @patch("hostinger.probes._run_cmd")
    async def test_nc_not_found_socket_fallback_open(self, mock_run_cmd):
        """When nc is missing, socket fallback is used."""
        mock_run_cmd.return_value = (-2, "", "COMMAND_NOT_FOUND")

        with patch(
            "hostinger.probes.asyncio.open_connection",
            new_callable=AsyncMock,
        ) as mock_conn:
            mock_conn.return_value = (AsyncMock(), AsyncMock())
            result = await probe_port("example.com", 443)
            assert result.status == "OPEN"

    @patch("hostinger.probes._run_cmd")
    async def test_nc_not_found_socket_fallback_closed(self, mock_run_cmd):
        """Socket fallback correctly reports connection refused."""
        mock_run_cmd.return_value = (-2, "", "COMMAND_NOT_FOUND")

        with patch(
            "hostinger.probes.asyncio.open_connection",
            new_callable=AsyncMock,
        ) as mock_conn:
            mock_conn.side_effect = ConnectionRefusedError()
            result = await probe_port("example.com", 443)
            assert result.status == "CLOSED"

    @patch("hostinger.probes._run_cmd")
    async def test_timeout(self, mock_run_cmd):
        """Timeout returns TIMEOUT."""
        mock_run_cmd.return_value = (-1, "", "TIMEOUT")
        result = await probe_port("example.com", 80)
        assert result.status == "TIMEOUT"


# =============================================================================
#  HTTP probe
# =============================================================================


class TestHTTPProbe:
    @patch("hostinger.probes._run_cmd")
    async def test_200_ok(self, mock_run_cmd):
        """HTTP 200 returns OK."""
        mock_run_cmd.return_value = (0, "200 0.187 text/html\n", "")
        result = await probe_http("example.com", "http")
        assert result.status == "OK"
        assert result.probe == "HTTP http"
        assert result.data["status_code"] == 200
        assert result.data["time_seconds"] == 0.187

    @patch("hostinger.probes._run_cmd")
    async def test_301_redirect_ok(self, mock_run_cmd):
        """3xx redirects are considered OK."""
        mock_run_cmd.return_value = (0, "301 0.050 text/html\n", "")
        result = await probe_http("example.com", "http")
        assert result.status == "OK"

    @patch("hostinger.probes._run_cmd")
    async def test_404_fail(self, mock_run_cmd):
        """4xx returns FAIL."""
        mock_run_cmd.return_value = (0, "404 0.100 text/html\n", "")
        result = await probe_http("example.com", "http")
        assert result.status == "FAIL"

    @patch("hostinger.probes._run_cmd")
    async def test_500_fail(self, mock_run_cmd):
        """5xx returns FAIL."""
        mock_run_cmd.return_value = (0, "500 0.200 text/html\n", "")
        result = await probe_http("example.com", "http")
        assert result.status == "FAIL"

    @patch("hostinger.probes._run_cmd")
    async def test_curl_not_found(self, mock_run_cmd):
        """Missing curl returns ERROR."""
        mock_run_cmd.return_value = (-2, "", "COMMAND_NOT_FOUND")
        result = await probe_http("example.com", "http")
        assert result.status == "ERROR"

    @patch("hostinger.probes._run_cmd")
    async def test_connection_error(self, mock_run_cmd):
        """Curl connection failure returns FAIL."""
        mock_run_cmd.return_value = (7, "", "Failed to connect")
        result = await probe_http("example.com", "http")
        assert result.status == "FAIL"

    @patch("hostinger.probes._run_cmd")
    async def test_timeout(self, mock_run_cmd):
        """Timeout returns TIMEOUT."""
        mock_run_cmd.return_value = (-1, "", "TIMEOUT")
        result = await probe_http("example.com", "https")
        assert result.status == "TIMEOUT"


# =============================================================================
#  _is_ip_address helper
# =============================================================================


class TestIsIpAddress:
    def test_ipv4(self):
        assert _is_ip_address("192.168.1.1") is True

    def test_ipv6(self):
        assert _is_ip_address("::1") is True
        assert _is_ip_address("2001:db8::1") is True

    def test_hostname(self):
        assert _is_ip_address("example.com") is False

    def test_localhost(self):
        assert _is_ip_address("127.0.0.1") is True


# =============================================================================
#  Orchestration
# =============================================================================


class TestRunAllProbes:
    @patch("hostinger.probes.probe_dns")
    @patch("hostinger.probes.probe_ping")
    @patch("hostinger.probes.probe_port")
    @patch("hostinger.probes.probe_http")
    async def test_ordering_hostname(
        self,
        mock_http,
        mock_port,
        mock_ping,
        mock_dns,
    ):
        """Results are returned in DNS → Ping → Ports → HTTP order."""
        mock_dns.return_value = ProbeResult("DNS", "OK", "1.2.3.4", {})
        mock_ping.return_value = ProbeResult("Ping", "OK", "min 10 ms", {})
        mock_port.side_effect = lambda host, port, **kw: ProbeResult(
            f"Port {port}", "OPEN", f"Port {port} open", {}
        )
        mock_http.side_effect = lambda host, scheme, **kw: ProbeResult(
            f"HTTP {scheme}", "OK", "200", {}
        )

        results = await run_all_probes("example.com")

        names = [r.probe for r in results]
        assert names == ["DNS", "Ping", "Port 80", "Port 443", "HTTP http", "HTTP https"]
        assert len(results) == 6

    @patch("hostinger.probes.probe_ping")
    @patch("hostinger.probes.probe_port")
    @patch("hostinger.probes.probe_http")
    async def test_ordering_ip_skips_dns(
        self,
        mock_http,
        mock_port,
        mock_ping,
    ):
        """IP address skips DNS probe."""
        mock_ping.return_value = ProbeResult("Ping", "OK", "min 10 ms", {})
        mock_port.side_effect = lambda host, port, **kw: ProbeResult(
            f"Port {port}", "OPEN", f"Port {port} open", {}
        )
        mock_http.side_effect = lambda host, scheme, **kw: ProbeResult(
            f"HTTP {scheme}", "OK", "200", {}
        )

        results = await run_all_probes("192.168.1.1")

        names = [r.probe for r in results]
        assert names == ["Ping", "Port 80", "Port 443", "HTTP http", "HTTP https"]
        assert len(results) == 5
        mock_ping.assert_called_once_with("192.168.1.1")


# =============================================================================
#  Model helpers
# =============================================================================


class TestProbeResult:
    def test_is_ok(self):
        assert ProbeResult("test", "OK", "").is_ok is True
        assert ProbeResult("test", "OPEN", "").is_ok is True
        assert ProbeResult("test", "FAIL", "").is_ok is False
        assert ProbeResult("test", "CLOSED", "").is_ok is False

    def test_to_dict(self):
        r = ProbeResult("DNS", "OK", "1.2.3.4", {"ips": ["1.2.3.4"]})
        d = r.to_dict()
        assert d["probe"] == "DNS"
        assert d["status"] == "OK"
        assert d["data"]["ips"] == ["1.2.3.4"]


# =============================================================================
#  Reporter smoke test (JSON path — table path is visual)
# =============================================================================


class TestReporterJSON:
    def test_print_json(self, capsys):
        """JSON output is valid and contains expected fields."""
        from hostinger.reporter import print_json

        results = [
            ProbeResult("DNS", "OK", "1.2.3.4", {"ips": ["1.2.3.4"]}),
            ProbeResult("Ping", "OK", "min 10 ms", {}),
        ]
        print_json(results, "example.com")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["host"] == "example.com"
        assert len(data["results"]) == 2
        assert data["results"][0]["probe"] == "DNS"
