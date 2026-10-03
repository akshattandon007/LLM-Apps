"""SubsSleuth — Multi-Agent Subscription Cancellation System.

CLI entry point. Orchestrates all three agents.

Usage:
    python -m subs_sleuth scan --email user@gmail.com --password app-password
    python -m subs_sleuth scan --demo
    python -m subs_sleuth cancel --demo
    python -m subs_sleuth verify --demo
    python -m subs_sleuth all --demo
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .models import FullReport, Subscription
from .utils import configure_llm


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SubsSleuth — Multi-Agent Subscription Cancellation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"v{__version__}")
    parser.add_argument(
        "--llm-key",
        help="LLM API key (Groq/OpenAI-compatible). Without it, rule-based fallbacks are used.",
    )
    parser.add_argument(
        "--llm-url",
        default="https://api.groq.com/openai/v1/chat/completions",
        help="LLM API endpoint URL",
    )
    parser.add_argument(
        "--llm-model",
        default="llama-3.3-70b-versatile",
        help="LLM model name",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    scan_p = sub.add_parser("scan", help="Scan emails for subscriptions")
    scan_p.add_argument("--email", help="Email address for IMAP login")
    scan_p.add_argument("--password", help="App password for IMAP login")
    scan_p.add_argument(
        "--server", default="imap.gmail.com", help="IMAP server hostname"
    )
    scan_p.add_argument("--since", help="Search emails since date (e.g. 01-Jan-2025)")
    scan_p.add_argument("--demo", action="store_true", help="Use demo data (no credentials)")
    scan_p.add_argument("--output", help="Save results to JSON file")

    # cancel
    cancel_p = sub.add_parser("cancel", help="Research cancellation methods")
    cancel_p.add_argument("--demo", action="store_true", help="Use demo subscriptions")
    cancel_p.add_argument("--input", help="JSON file with subscription list")
    cancel_p.add_argument(
        "--merchant", help="Research cancellation for a single merchant"
    )
    cancel_p.add_argument("--output", help="Save results to JSON file")

    # verify
    verify_p = sub.add_parser("verify", help="Verify subscriptions against statements")
    verify_p.add_argument("--demo", action="store_true", help="Use demo data")
    verify_p.add_argument("--input-subs", help="JSON file with subscription list")
    verify_p.add_argument("--input-statement", help="CSV file with bank statement")
    verify_p.add_argument("--output", help="Save results to JSON file")

    # all (full pipeline)
    all_p = sub.add_parser("all", help="Run the full pipeline")
    all_p.add_argument("--demo", action="store_true", help="Run with demo data")
    all_p.add_argument("--email", help="Email address for IMAP login")
    all_p.add_argument("--password", help="App password for IMAP login")
    all_p.add_argument("--server", default="imap.gmail.com", help="IMAP server hostname")
    all_p.add_argument("--output", help="Save full report to JSON file")

    return parser.parse_args(argv)


def _cmd_scan(args: argparse.Namespace) -> None:
    """Run the scanner agent."""
    if args.demo:
        from .scanner_agent import scan_demo
        report = scan_demo()
    elif args.email and args.password:
        from .scanner_agent import scan_email
        report = scan_email(
            server=args.server,
            email=args.email,
            password=args.password,
            search_since=args.since,
        )
    else:
        print("Error: provide --email/--password or --demo", file=sys.stderr)
        sys.exit(1)

    output = report.to_dict()
    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Scan report saved to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    print(f"\nFound {report.total_found} subscription(s) from {report.email_count_checked} email(s).")
    if report.errors:
        print(f"Warnings/errors: {report.errors}")


def _cmd_cancel(args: argparse.Namespace) -> None:
    """Run the cancellation research agent."""
    subscriptions: list[Subscription] = []

    if args.demo:
        from .scanner_agent import scan_demo
        report = scan_demo()
        subscriptions = report.subscriptions
    elif args.input:
        with open(args.input) as f:
            data = json.load(f)
            subscriptions = [Subscription(**s) for s in data.get("subscriptions", data)]
    elif args.merchant:
        subscriptions = [Subscription(merchant=args.merchant)]
    else:
        print("Error: provide --demo, --input, or --merchant", file=sys.stderr)
        sys.exit(1)

    from .cancel_agent import research_all
    guides = research_all(subscriptions)
    output = [g.to_dict() for g in guides]

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Cancellation guides saved to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    print(f"\nResearched cancellation for {len(guides)} subscription(s).")


def _cmd_verify(args: argparse.Namespace) -> None:
    """Run the verification agent."""
    subscriptions: list[Subscription] = []

    if args.demo:
        from .verify_agent import verify_demo
        reports = verify_demo()
        output = [r.to_dict() for r in reports]
        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2)
                print(f"Verification report saved to {args.output}")
        else:
            print(json.dumps(output, indent=2))
        found = sum(1 for r in reports if r.found_on_statement)
        print(f"\nVerified {found}/{len(reports)} subscriptions found on statement.")
        return

    if args.input_subs:
        with open(args.input_subs) as f:
            data = json.load(f)
            subscriptions = [Subscription(**s) for s in data.get("subscriptions", data)]

    if args.input_statement:
        from .verify_agent import parse_statement_csv
        with open(args.input_statement) as f:
            statement_lines = parse_statement_csv(f.read())
    else:
        print("Error: provide --input-subs and --input-statement, or --demo", file=sys.stderr)
        sys.exit(1)

    from .verify_agent import verify_subscriptions
    reports = verify_subscriptions(subscriptions, statement_lines)
    output = [r.to_dict() for r in reports]

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Verification report saved to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    found = sum(1 for r in reports if r.found_on_statement)
    print(f"\nMatched {found}/{len(reports)} subscriptions on statement.")


def _cmd_all(args: argparse.Namespace) -> None:
    """Run the full pipeline: scan → cancel → verify."""
    subscriptions: list[Subscription] = []

    if args.demo:
        from .scanner_agent import scan_demo
        print("=== Phase 1: Scan ===")
        scan_report = scan_demo()
        subscriptions = scan_report.subscriptions
        print(f"Found {len(subscriptions)} subscription(s) in demo mode.\n")

        print("=== Phase 2: Cancel ===")
        from .cancel_agent import research_all
        guides = research_all(subscriptions)
        for g in guides:
            print(f"  {g.merchant}: {g.cancellation_method} ({g.difficulty})")
        print()

        print("=== Phase 3: Verify ===")
        from .verify_agent import verify_demo
        verifications = verify_demo(subscriptions)
        found = sum(1 for v in verifications if v.found_on_statement)
        print(f"Verified {found}/{len(verifications)} on statement.\n")

        report = FullReport(scan=scan_report, guides=guides, verification=verifications)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report.to_json())
            print(f"Full report saved to {args.output}")
        else:
            print("=== Full Report ===")
            print(report.to_json())

        print("\nDone. Demo complete — no real credentials were used.")

    elif args.email and args.password:
        from .scanner_agent import scan_email
        from .cancel_agent import research_all
        from .verify_agent import verify_demo  # verification requires statement file

        print("=== Phase 1: Scan ===")
        scan_report = scan_email(
            server=args.server,
            email=args.email,
            password=args.password,
        )
        subscriptions = scan_report.subscriptions
        print(f"Found {len(subscriptions)} subscription(s).\n")

        print("=== Phase 2: Cancel ===")
        guides = research_all(subscriptions)
        print(f"Researched {len(guides)} cancellation guides.\n")

        print("=== Phase 3: Verify ===")
        print("Note: Verification via bank statement requires --input-statement.")
        print("For demo verification, use: subs-sleuth verify --demo")
        verifications = []

        report = FullReport(scan=scan_report, guides=guides)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report.to_json())
            print(f"Partial report saved to {args.output}")

    else:
        print("Provide --demo or --email/--password", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    # Configure LLM if key provided
    if args.llm_key:
        configure_llm(api_key=args.llm_key, api_url=args.llm_url, model=args.llm_model)

    commands = {
        "scan": _cmd_scan,
        "cancel": _cmd_cancel,
        "verify": _cmd_verify,
        "all": _cmd_all,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)


if __name__ == "__main__":
    main()