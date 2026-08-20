#!/usr/bin/env python3
"""FridgeFighter — gamified fridge food tracker.

Snap a photo of your fridge, AI identifies items and expiry,
generates daily challenges to use expiring food, and tracks
your zero-waste streak.

Usage:

    python main.py scan
        Simulate scanning a fridge, print detected items.

    python main.py challenges
        Generate and display today's challenges.

    python main.py use <item-id> [... <item-id>]
        Record that you used (ate, froze, cooked) an item.
        Awards points and updates streak.

    python main.py status
        Show your current profile stats, streak, and badges.

    python main.py --simulate
        Run a full demo: scan → challenges → use items → status.

    python main.py --seed 42
        Use a fixed seed for reproducible output (useful for testing).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from src import models
from src.challenges import generate
from src.item_db import add, expire_soon, list_items, load, remove
from src.scoring import record_use, summarize
from src.vision import scan


def cmd_scan(args):
    """Detect items in the fridge (simulated)."""
    items = scan(seed=args.seed, count=args.count)
    load(items)

    now = date.today()
    expiring = [it for it in items if it.expiry_date <= now]

    print(f"\n  Fridge scan complete — {len(items)} items detected.\n")
    for it in items:
        days_left = (it.expiry_date - now).days
        expiry_str = f"{it.expiry_date} ({days_left} day{'s' if days_left != 1 else ''} left)"
        if days_left <= 0:
            expiry_str = f"{it.expiry_date} (⚠️  EXPIRED!)"
        elif days_left <= 2:
            expiry_str = f"{it.expiry_date} (🔥 expiring soon!)"
        print(
            f"    [{it.id}] {it.name:30s}  {it.quantity:3d} {it.unit:8s}"
            f"  ({it.category:12s})  {expiry_str}"
        )

    if expiring:
        print(f"\n  ⚠️  {len(expiring)} item(s) are already past expiry!")

    return items


def cmd_challenges(args):
    """Generate and display today's challenges."""
    # Ensure items are loaded
    items = list_items()
    if not items:
        print("  No items in inventory. Run 'scan' first.")
        return []

    challenges = generate(seed=args.seed)
    print(f"\n  🎯  Today's Challenges ({len(challenges)})\n")
    for c in challenges:
        count_str = f" ({c.criteria.get('count', '?')} items)" if "count" in c.criteria else ""
        print(f"    [{c.id}] {c.title}{count_str}")
        print(f"           {c.description}")
        print(f"           🏅  {c.points} points")
        if c.completed:
            print("           ✅  COMPLETED")
        print()

    return challenges


def cmd_use(args):
    """Record that an item was used."""
    ids = getattr(args, "item_ids", None)
    if not ids:
        print("  Usage: python main.py use <item-id> [<item-id> ...]")
        return

    used_items = []
    for item_id in ids:
        it = remove(item_id)
        if it is None:
            print(f"  ✗  Item '{item_id}' not found in fridge.")
        else:
            used_items.append(it)
            print(f"  ✓  Used: {it.name} ({it.quantity} {it.unit}) — saved from waste! 🎉")

    if not used_items:
        return

    items_saved = len(used_items)
    profile = models.UserProfile()
    updated_profile, new_badges = record_use(
        profile=profile,
        items_saved=items_saved,
        points_earned=items_saved * 10,
        today=date.today(),
    )

    total_points = items_saved * 10
    print(f"\n  +{total_points} points earned! (10 per item saved)")
    print(f"  🔥  Current streak: {updated_profile.current_streak} day(s)")

    if new_badges:
        print(f"\n  🏅  NEW BADGES EARNED:")
        for badge in new_badges:
            print(f"     {badge.icon}  {badge.name} — {badge.description}")

    # Save profile back (in full app this would persist)
    print(f"\n  📦  Items remaining: {len(list_items())}")


def cmd_status(_args=None):
    """Show current profile stats."""
    profile = models.UserProfile()
    # In real app, load persisted profile; for now show empty default with message
    items = list_items()
    print(f"\n  📋  Fridge Status\n")
    print(f"  Items in inventory: {len(items)}")
    if items:
        now = date.today()
        expiring_items = [it for it in items if it.expiry_date <= now]
        print(f"  Expiring today:     {len(expiring_items)}")
        print()
        for it in items:
            days_left = (it.expiry_date - now).days
            exp_str = f"{days_left}d" if days_left >= 0 else "EXPIRED"
            print(f"    📦 {it.name:30s}  expires {exp_str}")
    print()
    print(summarize(profile))


def cmd_demo(args):
    """Full simulation: scan → challenges → use → status."""
    print("=" * 60)
    print("  FridgeFighter — Zero-Waste Challenge Simulator")
    print("=" * 60)

    # Step 1: Scan
    print("\n📸  1. Scanning fridge...")
    items = cmd_scan(args)
    if not items:
        print("  Nothing detected. Try again!")
        return

    # Step 2: Challenges
    print("\n" + "─" * 60)
    print("🎯  2. Generating challenges...")
    challenges = cmd_challenges(args)

    # Step 3: Use some items
    print("\n" + "─" * 60)
    print("🍽️  3. Using expiring items...")
    expiring = expire_soon(hours=48)
    if expiring:
        # Use the first 1-2 expiring items
        target_ids = [e.id for e in expiring[:2]]
        args.item_ids = target_ids
        cmd_use(args)
    else:
        print("  No items expiring soon — fridge is well managed! 🎉")

    # Step 4: Status
    print("\n" + "─" * 60)
    print("📋  4. Final status...")
    cmd_status(args)

    print("\n" + "=" * 60)
    print("  Keep fighting food waste! 💪🌍")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="FridgeFighter — gamified fridge food tracker"
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Run a full simulation (scan → challenges → use → status)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible output"
    )
    parser.add_argument(
        "--count", type=int, default=8,
        help="Number of items to detect during scan (default: 8)"
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Scan fridge and detect items")
    scan_parser.add_argument("--count", type=int, default=8)

    challenges_parser = subparsers.add_parser("challenges", help="Generate daily challenges")
    use_parser = subparsers.add_parser("use", help="Record used items")
    use_parser.add_argument("item_ids", nargs="+", metavar="item-id")

    status_parser = subparsers.add_parser("status", help="Show profile and fridge status")

    args = parser.parse_args()

    if args.simulate:
        cmd_demo(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "challenges":
        cmd_challenges(args)
    elif args.command == "use":
        cmd_use(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()