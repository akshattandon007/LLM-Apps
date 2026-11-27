"""
BillSplice CLI — interactive bill splitting from the terminal.
"""

import argparse
import sys
from decimal import Decimal, InvalidOperation
from typing import List

from .models import Bill, Item, Person
from .splitter import split_bill


def run_interactive() -> None:
    """Run the interactive bill-splitting wizard."""
    print("\n🧾 BillSplice — Bill Splitter")
    print("=" * 50)

    bill = Bill()

    # Enter items
    print("\n📋 Enter items (one per line). Blank line to finish.")
    print("   Format: ItemName,Price  (e.g. Pizza,24.50)")
    print("   Add ! at end for shared items (e.g. Fries,8.00!)")
    while True:
        line = input("   Item: ").strip()
        if not line:
            break
        shared = line.endswith("!")
        name_part = line.rstrip("!").strip()
        if "," not in name_part:
            print("   ⚠  Use format: ItemName,Price")
            continue
        try:
            item_name, price_str = name_part.rsplit(",", 1)
            price = Decimal(price_str.strip())
            bill.items.append(Item(name=item_name.strip(), price=price, shared=shared))
            print(f"   ✓ {item_name.strip()} — ${price:.2f}" + (" (shared)" if shared else ""))
        except InvalidOperation:
            print("   ⚠  Invalid price. Try again.")

    if not bill.items:
        print("\n No items entered. Exiting.")
        return

    # Enter people
    print("\n👥 Enter people's names (one per line). Blank to finish.")
    while True:
        name = input("   Name: ").strip()
        if not name:
            break
        bill.people.append(Person(name=name))

    if not bill.people:
        print("\n No people entered. Exiting.")
        return

    # Assign items to people
    personal_items = {p.name: [] for p in bill.people}
    shared_items_names = {i.name for i in bill.items if i.shared}

    print("\n🔗 Assign NON-SHARED items to people:")
    for item in bill.items:
        if item.shared:
            continue
        print(f"\n   Who had \"{item.name}\" (${item.price:.2f})?")
        for i, p in enumerate(bill.people, 1):
            print(f"   {i}. {p.name}")
        choice = input("   Enter number or name: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(bill.people):
                personal_items[bill.people[idx].name].append(item)
            else:
                print("   ⚠  Invalid. Skipping.")
        except ValueError:
            # Try matching by name
            matched = [p for p in bill.people if p.name.lower() == choice.lower()]
            if matched:
                personal_items[matched[0].name].append(item)
            else:
                print("   ⚠  Person not found. Skipping.")

    # Build Person objects with their items
    for person in bill.people:
        person.items = personal_items[person.name]

    # Tax & tip
    print("\n💰 Tax & Tip")
    while True:
        try:
            tax_str = input("   Tax % (e.g. 8.875, or 0): ").strip() or "0"
            bill.tax_percent = Decimal(tax_str)
            break
        except InvalidOperation:
            print("   ⚠  Enter a number.")
    while True:
        try:
            tip_str = input("   Tip % (e.g. 18, or 0): ").strip() or "0"
            bill.tip_percent = Decimal(tip_str)
            break
        except InvalidOperation:
            print("   ⚠  Enter a number.")

    # Calculate!
    results = split_bill(bill)

    # Display
    print("\n" + "=" * 50)
    print("📊 SPLIT RESULT")
    print("=" * 50)
    print(f"  Bill subtotal:  ${bill.subtotal:.2f}")
    if bill.tax_percent > 0:
        print(f"  Tax ({bill.tax_percent}%):     ${bill.tax_amount:.2f}")
    if bill.tip_percent > 0:
        print(f"  Tip ({bill.tip_percent}%):     ${bill.tip_amount:.2f}")
    print(f"  Total:          ${bill.total:.2f}")
    print("—" * 50)

    for r in results:
        items_list = ", ".join(i.name for i in r.items) if r.items else "(shared only)"
        print(f"\n  {r.person_name}")
        print(f"    Items:    {items_list}")
        print(f"    Subtotal: ${r.subtotal:.2f}")
        if bill.tax_percent > 0:
            print(f"    Tax:      ${r.tax_share:.2f}")
        if bill.tip_percent > 0:
            print(f"    Tip:      ${r.tip_share:.2f}")
        print(f"    ▶ TOTAL:  ${r.total:.2f}")

    print("\n" + "=" * 50)


def run_quick(args: argparse.Namespace) -> None:
    """Run the quick non-interactive mode with command-line args."""
    from .models import Bill, Item, Person
    bill = Bill()
    bill.tax_percent = Decimal(str(args.tax))
    bill.tip_percent = Decimal(str(args.tip))

    # Items from args
    names = args.names.split(",")
    prices = [Decimal(p) for p in args.prices.split(",")]
    if len(names) != len(prices):
        print("Error: --names and --prices must have the same number of items.", file=sys.stderr)
        sys.exit(1)
    for n, p in zip(names, prices):
        bill.items.append(Item(name=n.strip(), price=p))

    # People
    person_names = [s.strip() for s in args.people.split(",")]
    people = {n: Person(name=n) for n in person_names}

    # Assign items to people
    assign = args.assign.split(",") if args.assign else []
    if assign:
        for i, person_name in enumerate(assign):
            if i < len(bill.items) and person_name in people:
                people[person_name].items.append(bill.items[i])
    else:
        # Equal split
        for item in bill.items:
            item.shared = True

    bill.people = list(people.values())
    results = split_bill(bill)

    for r in results:
        print(f"{r.person_name}: ${r.total:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BillSplice — Split restaurant/group bills effortlessly.",
    )
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode (non-interactive)")
    parser.add_argument("--names", help="Comma-separated item names (quick mode)")
    parser.add_argument("--prices", help="Comma-separated item prices (quick mode)")
    parser.add_argument("--people", help="Comma-separated person names (quick mode)")
    parser.add_argument("--assign", help="Comma-separated person-per-item assignments (quick mode)")
    parser.add_argument("--tax", type=float, default=0.0, help="Tax percent")
    parser.add_argument("--tip", type=float, default=0.0, help="Tip percent")
    args = parser.parse_args()

    if args.quick:
        run_quick(args)
    else:
        run_interactive()


if __name__ == "__main__":
    main()