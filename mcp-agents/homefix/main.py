#!/usr/bin/env python3
"""CLI entry point for testing HomeFix MCP tools directly (no MCP client needed)."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.searcher import find_pros, get_pro_details
from src.licenser import check_license
from src.estimator import get_estimate
from src.reviewer import summarize_reviews
from src.scheduler import book_appointment, get_available_slots


def cmd_find(args):
    results = find_pros(args.service_type, args.zip, emergency=args.emergency)
    if not results:
        print(f"No {args.service_type}s found for ZIP {args.zip}.")
        return
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['name']} ⭐{r['rating']} ({r['review_count']} reviews) — {r['phone']}")
        print(f"   Licensed: {r['licensed']} | Available now: {r['available_now']}")


def cmd_estimate(args):
    result = get_estimate(args.service, args.description, args.zip)
    print(result)


def cmd_license(args):
    result = check_license(args.company, args.state)
    print(f"Company: {result['company']}")
    print(f"State: {result['state']}")
    print(f"License #: {result['license_number']}")
    print(f"Status: {result['license_status']}")
    print(f"Insurance: {result['insurance_status']}")
    print(f"Bond: {result['bond_status']}")
    print(f"\n{result['summary']}")


def cmd_reviews(args):
    result = summarize_reviews(args.professional)
    print(f"Professional: {result.get('professional', args.professional)}")
    print(f"Rating: {result.get('rating', 'N/A')}/5.0 ({result.get('review_count', 0)} reviews)")
    print(f"Sentiment: {result.get('sentiment', 'unknown')}")
    print(f"\n{result.get('summary', 'N/A')}")


def cmd_emergency(args):
    results = find_pros("plumber", args.zip, emergency=True)
    results += find_pros("electrician", args.zip, emergency=True)
    results += find_pros("locksmith", args.zip, emergency=True)
    results += find_pros("hvac", args.zip, emergency=True)
    if not results:
        print(f"No emergency services available in ZIP {args.zip}.")
        return
    print(f"🚨 Emergency services near {args.zip}:")
    for r in results:
        print(f"  • {r['name']} ⭐{r['rating']} — {r['phone']}")


def cmd_book(args):
    date_param = args.date if args.date else None
    result = book_appointment(args.pro_name, args.time, date_param)
    if result.get("success"):
        print(f"✅ Booked! Confirmation: {result['confirmation_number']}")
        print(f"   {result['professional']} on {result['appointment_date']} at {result['appointment_time']}")
    else:
        print(f"❌ {result.get('error', 'Booking failed')}")


def main():
    parser = argparse.ArgumentParser(description="HomeFix CLI — test HomeFix tools directly")
    sub = parser.add_subparsers(dest="command", required=True)

    p_find = sub.add_parser("find", help="Find pros by service type + ZIP")
    p_find.add_argument("service_type", help="plumber, electrician, hvac, etc.")
    p_find.add_argument("zip", help="ZIP code")
    p_find.add_argument("--emergency", action="store_true", help="Only 24/7 available")
    p_find.set_defaults(func=cmd_find)

    p_est = sub.add_parser("estimate", help="Get price estimate")
    p_est.add_argument("service", help="Service type")
    p_est.add_argument("description", help="Job description")
    p_est.add_argument("zip", help="ZIP code")
    p_est.set_defaults(func=cmd_estimate)

    p_lic = sub.add_parser("license", help="Check license / insurance / bond")
    p_lic.add_argument("company", help="Company name")
    p_lic.add_argument("state", help="Two-letter state code")
    p_lic.set_defaults(func=cmd_license)

    p_rev = sub.add_parser("reviews", help="Summarize reviews")
    p_rev.add_argument("professional", help="Professional name")
    p_rev.set_defaults(func=cmd_reviews)

    p_emerg = sub.add_parser("emergency", help="Find emergency services")
    p_emerg.add_argument("zip", help="ZIP code")
    p_emerg.set_defaults(func=cmd_emergency)

    p_book = sub.add_parser("book", help="Book appointment")
    p_book.add_argument("pro_name", help="Professional name")
    p_book.add_argument("time", help="Time (e.g. '9:00 am' or '14:00')")
    p_book.add_argument("--date", help="Date YYYY-MM-DD (default: tomorrow)")
    p_book.set_defaults(func=cmd_book)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()