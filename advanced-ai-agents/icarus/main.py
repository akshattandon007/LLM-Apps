#!/usr/bin/env python3
"""Icarus — Incident Remediation Agent. CLI entry point.

Usage:
    python main.py --simulate
    python main.py --simulate --source prometheus
    python main.py --alert '{"severity":"critical","title":"High error rate","service":"api"}'
    python main.py --alert /path/to/alert.json --source pagerduty --auto-approve
    python main.py --simulate --output /tmp/postmortem.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.alert_ingest import parse_alert, simulate_alert_payload
from src.models import AlertSeverity, Incident, RemediationActionStatus
from src.monitor import record_incident
from src.postmortem import draft_postmortem, render_markdown
from src.rca import run_rca
from src.remediate import approve_action, execute_action, propose_remediation
from src.triage import gather_evidence


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Icarus — Incident Remediation Agent: alert in, root cause, fix, post-mortem.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument(
        "--alert",
        help="Alert payload: inline JSON string or a path to a JSON file",
    )
    src_group.add_argument(
        "--simulate",
        action="store_true",
        help="Generate a simulated alert and run the full pipeline end-to-end",
    )
    parser.add_argument(
        "--source",
        choices=["pagerduty", "prometheus", "cloudwatch", "manual"],
        default="pagerduty",
        help="Alert source format (default: pagerduty)",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Approve all remediation actions without prompting. "
        "The human authorizes via this explicit flag; destructive actions are "
        "still never auto-executed without it.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Write the post-mortem markdown to this file (default: stdout)",
    )
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Do not persist the incident to the incident database",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress",
    )
    return parser.parse_args(argv)


def log(msg: str, verbose: bool = True) -> None:
    if verbose:
        print(f"[icarus] {msg}")


def load_alert_payload(raw: str) -> dict:
    """Load an alert payload from an inline JSON string or a file path."""
    path = Path(raw)
    if path.exists():
        return json.loads(path.read_text())
    return json.loads(raw)


def _confirm(prompt: str) -> bool:
    """Interactive confirmation for remediation actions.

    Never auto-approves on a non-interactive stdin (CI): returns False.
    """
    if not sys.stdin.isatty():
        return False
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


def run_pipeline(args: argparse.Namespace) -> Incident:
    """Run the full Icarus pipeline: ingest -> triage -> rca -> remediate -> post-mortem."""
    # 1. Ingest
    if args.simulate:
        log("Ingesting simulated alert...")
        payload = simulate_alert_payload(args.source)
        alert = parse_alert(args.source, payload)
    else:
        log("Parsing alert payload...")
        alert = parse_alert(args.source, load_alert_payload(args.alert))
    log(f"Alert {alert.id} [{alert.source.value}/{alert.severity.value}] "
        f"service={alert.service}: {alert.title}")

    incident = Incident(id=f"inc-{alert.id}", alert=alert, severity=alert.severity)

    # 2. Triage
    log("Triage: fetching logs, metrics, deployments...")
    evidence = gather_evidence(alert)
    log(f"  {len(evidence.logs)} log entries, {len(evidence.metrics)} metric samples, "
        f"{len(evidence.deployments)} deployments")

    # 3. RCA
    log("RCA: correlating events...")
    root_cause = run_rca(alert, evidence)
    log(f"  hypothesis: {root_cause.hypothesis} (confidence {root_cause.confidence:.0%})")
    for step in root_cause.reasoning_steps:
        log(f"    {step}")

    # 4. Remediation (human-gated)
    log("Remediation: proposing plan...")
    plan = propose_remediation(root_cause, evidence)
    for action in plan.actions:
        gate = "DESTRUCTIVE" if action.destructive else "safe"
        log(f"  proposed [{gate}] {action.id}: {action.description} -> {action.command}")

    if args.auto_approve:
        log("--auto-approve set: approving all actions (explicit human authorization).")
        for action in plan.actions:
            approve_action(plan, action.id)
    else:
        for action in plan.actions:
            if _confirm(f"  Approve {action.id} ({action.description})?"):
                approve_action(plan, action.id)
                log(f"  approved {action.id}")
            else:
                action.status = RemediationActionStatus.skipped
                log(f"  skipped {action.id}")

    for action in plan.actions:
        if action.status.value == "approved":
            execute_action(plan, action.id)
            log(f"  executed {action.id} (dry-run)")
        else:
            log(f"  {action.id} not executed (status={action.status.value})")

    # 5. Post-mortem
    log("Drafting post-mortem...")
    postmortem = draft_postmortem(incident, root_cause, plan, evidence)

    # 6. Persist to incident DB (memory)
    if not args.no_record:
        db_path = record_incident(incident, root_cause, postmortem)
        log(f"Recorded incident to {db_path}")
    else:
        log("--no-record set: skipping incident database write.")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_markdown(postmortem))
        log(f"Post-mortem written to {out_path}")
    else:
        print("\n" + "=" * 72)
        print(render_markdown(postmortem))
        print("=" * 72)

    return incident


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    args = parse_args(argv)

    try:
        run_pipeline(args)
        return 0
    except Exception as e:  # noqa: BLE001 — CLI should always print a friendly error
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())