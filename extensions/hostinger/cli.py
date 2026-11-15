"""CLI definition using argparse (stdlib, zero dependencies)."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from . import probes
from .reporter import print_output

# ── parser ───────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hostinger",
        description="Debug why a host is down \u2014 DNS, ping, port scan, HTTP check.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  hostinger check example.com          # run all probes\n"
            "  hostinger check example.com --json   # JSON output\n"
            "  hostinger check example.com --watch  # re-check every 30s\n"
            "  hostinger check 192.168.1.1          # also accept IPs"
        ),
    )

    sub = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    check = sub.add_parser("check", help="Run diagnostics on a host")
    check.add_argument("host", help="Hostname or IP address to check")
    check.add_argument("--json", action="store_true", help="Output as JSON")
    check.add_argument(
        "--watch", action="store_true", help="Re-check every 30 seconds"
    )

    return parser


# ── command logic ────────────────────────────────────────────────────────────


async def run_check(host: str, json_mode: bool, watch: bool) -> None:
    """Execute the *check* command, optionally in watch mode."""
    if watch:
        while True:
            os.system("cls" if sys.platform == "win32" else "clear")
            results = await probes.run_all_probes(host)
            print_output(results, host, json_mode=False)
            print(f"\n[Ctrl+C to stop] Next check in 30 s ...")
            await asyncio.sleep(30)
    else:
        results = await probes.run_all_probes(host)
        print_output(results, host, json_mode)


# ── entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point (called from ``__main__.py`` or installed script)."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        try:
            asyncio.run(run_check(args.host, args.json, args.watch))
        except KeyboardInterrupt:
            sys.exit(0)
