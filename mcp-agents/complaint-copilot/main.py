#!/usr/bin/env python3
"""Complaint Copilot — CLI entry point for testing.

Usage:
    python main.py draft --company "British Airways" --issue "Flight BA123 delayed 6 hours" --amount "$650" --issue-type delayed_cancelled_flight --country uk
    python main.py ombudsman --company "British Airways" --issue-type delayed_cancelled_flight
    python main.py rights --issue-type delayed_cancelled_flight --country uk
    python main.py track --company "British Airways" --reference "CC-20260311-ABC123"
    python main.py escalate --company "British Airways" --ombudsman "CAA" --case-summary "Flight delayed 6 hours, no compensation offered"
    python main.py server    # Run MCP server in stdio mode
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import argparse

from src.drafter import draft_complaint
from src.ombudsman import find_ombudsman
from src.rights import get_rights
from src.tracker import track_complaint
from src.escalation import escalate_to_regulator
from src.models import IssueType, Country


def _resolve_issue_type(raw: str) -> IssueType | None:
    raw_clean = raw.strip().lower().replace(" ", "_").replace("-", "_")
    for member in IssueType:
        if member.value == raw_clean:
            return member
    return None


def _resolve_country(raw: str) -> Country | None:
    raw_clean = raw.strip().lower()
    for member in Country:
        if member.value == raw_clean:
            return member
    return None


def cmd_draft(args: argparse.Namespace) -> None:
    it = _resolve_issue_type(args.issue_type) if args.issue_type else None
    ct = _resolve_country(args.country) if args.country else None
    result = draft_complaint(
        company=args.company,
        issue=args.issue,
        amount=args.amount,
        outcome=args.outcome,
        issue_type=it,
        country=ct,
    )
    print(result)


def cmd_ombudsman(args: argparse.Namespace) -> None:
    it = _resolve_issue_type(args.issue_type)
    if it is None:
        print(f"Unknown issue type: {args.issue_type}")
        sys.exit(1)
    results = find_ombudsman(args.company, it)
    for i, info in enumerate(results, 1):
        print(f"{i}. {info.name}")
        print(f"   URL: {info.url}")
        print(f"   Jurisdiction: {info.jurisdiction}")
        print(f"   Eligibility: {info.eligibility}")
        if info.notes:
            print(f"   Notes: {info.notes}")
        print()


def cmd_rights(args: argparse.Namespace) -> None:
    it = _resolve_issue_type(args.issue_type)
    ct = _resolve_country(args.country)
    if it is None:
        print(f"Unknown issue type: {args.issue_type}")
        sys.exit(1)
    if ct is None:
        print(f"Unknown country: {args.country}")
        sys.exit(1)
    right = get_rights(it, ct)
    if right is None:
        print(f"No rights found for {args.issue_type} in {args.country}")
        return
    print(f"Right: {right.right}")
    print(f"\nSummary: {right.summary}")
    print(f"\nDeadline: {right.deadline}")
    print(f"\nReference: {right.reference}")
    print(f"\nDetails: {right.details}")


def cmd_track(args: argparse.Namespace) -> None:
    result = track_complaint(company=args.company, reference=args.reference)
    print(result)


def cmd_escalate(args: argparse.Namespace) -> None:
    result = escalate_to_regulator(
        company=args.company,
        ombudsman=args.ombudsman,
        case_summary=args.case_summary,
    )
    print(result)


def cmd_server(args: argparse.Namespace) -> None:
    from server import main
    main()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Complaint Copilot — Draft complaints, find ombudsmen, track escalation."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # draft
    p_draft = sub.add_parser("draft", help="Draft a formal complaint letter")
    p_draft.add_argument("--company", required=True)
    p_draft.add_argument("--issue", required=True)
    p_draft.add_argument("--amount")
    p_draft.add_argument("--outcome")
    p_draft.add_argument("--issue-type")
    p_draft.add_argument("--country")
    p_draft.set_defaults(func=cmd_draft)

    # ombudsman
    p_omb = sub.add_parser("ombudsman", help="Find the right ombudsman/regulator")
    p_omb.add_argument("--company", required=True)
    p_omb.add_argument("--issue-type", required=True)
    p_omb.set_defaults(func=cmd_ombudsman)

    # rights
    p_rights = sub.add_parser("rights", help="Look up consumer rights")
    p_rights.add_argument("--issue-type", required=True)
    p_rights.add_argument("--country", required=True)
    p_rights.set_defaults(func=cmd_rights)

    # track
    p_track = sub.add_parser("track", help="Track a complaint status")
    p_track.add_argument("--company", required=True)
    p_track.add_argument("--reference")
    p_track.set_defaults(func=cmd_track)

    # escalate
    p_esc = sub.add_parser("escalate", help="Generate a regulatory referral letter")
    p_esc.add_argument("--company", required=True)
    p_esc.add_argument("--ombudsman", required=True)
    p_esc.add_argument("--case-summary", required=True)
    p_esc.set_defaults(func=cmd_escalate)

    # server
    p_srv = sub.add_parser("server", help="Run the MCP server in stdio mode")
    p_srv.set_defaults(func=cmd_server)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
