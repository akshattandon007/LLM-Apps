"""
Command-line interface for TallyUp.
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List

from .core import Expense, settle_debts, format_report, compute_balances
from .storage import load_expenses, save_expenses

DEFAULT_DATA_FILE = Path.home() / ".tallyup" / "expenses.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tallyup",
        description="Group expense splitter — split shared costs and settle debts.",
        epilog="Example: tallyup add -d 'Dinner' -a 42.00 -p Alice -s Alice Bob Carol",
    )

    sub = parser.add_subparsers(dest="command", help="Command")

    # Add expense
    add_p = sub.add_parser("add", help="Record a new expense")
    add_p.add_argument("--description", "-d", required=True, help="What was it for?")
    add_p.add_argument("--amount", "-a", required=True, type=str, help="Total amount paid (e.g. 42.50)")
    add_p.add_argument("--paid-by", "-p", required=True, help="Who paid?")
    add_p.add_argument("--split-with", "-s", nargs="+", required=True,
                       help="Who shares the cost? Include the payer if they split too")
    add_p.add_argument("--date", default=date.today().isoformat(), help="Date (YYYY-MM-DD, default: today)")

    # List expenses
    sub.add_parser("list", help="Show all recorded expenses")

    # Settle
    settle_p = sub.add_parser("settle", help="Calculate who owes whom")
    settle_p.add_argument("--file", "-f", type=str, help="Data file path (default: ~/.tallyup/expenses.json)")

    # Clear
    clear_p = sub.add_parser("clear", help="Clear all expenses")
    clear_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # Summary
    sub.add_parser("summary", help="Show net balance for each person")

    return parser


def cmd_add(args: argparse.Namespace) -> None:
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: '{args.amount}' is not a valid amount.")
        return

    if amount <= 0:
        print("Error: Amount must be positive.")
        return

    expenses = load_expenses(DEFAULT_DATA_FILE)

    expense = Expense(
        description=args.description,
        amount=amount,
        paid_by=args.paid_by,
        participants=args.split_with,
        date=args.date,
    )
    expenses.append(expense)
    save_expenses(DEFAULT_DATA_FILE, expenses)
    print(f"✓ Recorded: {args.paid_by} paid ${amount:.2f} for {args.description}")
    print(f"  Split between: {', '.join(args.split_with)}")


def cmd_list(_args: argparse.Namespace) -> None:
    expenses = load_expenses(DEFAULT_DATA_FILE)
    if not expenses:
        print("No expenses recorded yet.")
        print("  Start: tallyup add -d 'Dinner' -a 42.00 -p Alice -s Alice Bob Carol")
        return

    print(f"{'ID':<10} {'Date':<12} {'Description':<25} {'Amount':<8} {'Paid by':<12} {'Split with'}")
    print("-" * 90)
    for e in expenses:
        participants = ", ".join(e.participants) if e.participants else "(none)"
        print(f"{e.id:<10} {e.date:<12} {e.description:<25} ${e.amount:<6.2f} {e.paid_by:<12} {participants}")


def cmd_settle(args: argparse.Namespace) -> None:
    file_path = Path(args.file) if args.file else DEFAULT_DATA_FILE
    expenses = load_expenses(file_path)
    if not expenses:
        print("No expenses to settle. Add some first: tallyup add -d ...")
        return

    settlements = settle_debts(expenses)
    print(format_report(expenses, settlements))


def cmd_clear(args: argparse.Namespace) -> None:
    if not args.yes:
        resp = input("Clear ALL expenses? This cannot be undone. [y/N] ")
        if resp.lower() not in ("y", "yes"):
            print("Cancelled.")
            return

    save_expenses(DEFAULT_DATA_FILE, [])
    print("✓ All expenses cleared.")


def cmd_summary(_args: argparse.Namespace) -> None:
    expenses = load_expenses(DEFAULT_DATA_FILE)
    if not expenses:
        print("No expenses recorded yet.")
        return

    balances = compute_balances(expenses)
    if not balances:
        print("No balances to show.")
        return

    print(f"{'Person':<20} {'Net Balance':<12}")
    print("-" * 35)
    for person, bal in sorted(balances.items(), key=lambda x: x[1]):
        sign = "+" if bal >= 0 else ""
        print(f"{person:<20} {sign}${bal:<8.2f}")
    print()
    print("Positive = owed money. Negative = owes money.")


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    cmd_map = {
        "add": cmd_add,
        "list": cmd_list,
        "settle": cmd_settle,
        "clear": cmd_clear,
        "summary": cmd_summary,
    }

    cmd = cmd_map.get(args.command)
    if cmd:
        cmd(args)


if __name__ == "__main__":
    main()