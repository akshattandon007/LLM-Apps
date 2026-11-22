"""TabCalc CLI — parse expenses and print settlement plans."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List

from .core import (
    Expense,
    SettlementPlan,
    compute_settlement,
)


def parse_expense_line(line: str) -> Expense:
    """Parse a single expense line in the format:

        description | paid_by | amount | person1,person2,...

    Example:
        Dinner | Alice | 45.00 | Alice,Bob,Charlie
    """
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 4:
        raise ValueError(
            f"Invalid expense line: {line!r}. "
            f"Expected: description | paid_by | amount | person1,person2,..."
        )

    description = parts[0]
    paid_by = parts[1]
    try:
        amount = Decimal(parts[2])
    except InvalidOperation:
        raise ValueError(f"Invalid amount in: {line!r}")

    split_among = [p.strip() for p in parts[3].split(",") if p.strip()]
    if not split_among:
        raise ValueError(f"No participants in split: {line!r}")

    return Expense(
        description=description,
        paid_by=paid_by,
        amount=amount,
        split_among=split_among,
    )


def parse_expense_file(path: Path) -> List[Expense]:
    """Read expenses from a file (one line per expense)."""
    text = path.read_text(encoding="utf-8")
    return parse_expense_text(text)


def parse_expense_text(text: str) -> List[Expense]:
    """Parse multiple expense lines from a string."""
    expenses: List[Expense] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        expenses.append(parse_expense_line(line))
    return expenses


def format_settlement(plan: SettlementPlan) -> str:
    """Format the settlement plan as a human-readable string."""
    lines: List[str] = []
    lines.append("=" * 50)
    lines.append("  TAB CALC — SETTLEMENT PLAN")
    lines.append("=" * 50)
    lines.append("")

    # Summary
    lines.append(f"  Total spent:  ${plan.total_spent:.2f}")
    lines.append(f"  Per person:   ${plan.per_person:.2f}")
    lines.append("")

    # Balances
    lines.append("  Balances:")
    for p in plan.participants:
        if p.net_balance > 0:
            lines.append(f"    {p.name:>12}  is owed ${p.net_balance:.2f}")
        elif p.net_balance < 0:
            lines.append(f"    {p.name:>12}  owes     ${-p.net_balance:.2f}")
        else:
            lines.append(f"    {p.name:>12}  is settled  $0.00")
    lines.append("")

    # Transfers
    if plan.transfers:
        lines.append("  Transfers (minimum):")
        for t in plan.transfers:
            lines.append(f"    {t.from_person:>12}  pays ${t.amount:.2f}  →  {t.to_person}")
    else:
        lines.append("  No transfers needed — everyone is settled.")
    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)


def format_json(plan: SettlementPlan) -> str:
    """Format the settlement plan as JSON."""
    return json.dumps(
        {
            "total_spent": float(plan.total_spent),
            "per_person": float(plan.per_person),
            "balances": {
                p.name: float(p.net_balance) for p in plan.participants
            },
            "transfers": [
                {
                    "from": t.from_person,
                    "to": t.to_person,
                    "amount": float(t.amount),
                }
                for t in plan.transfers
            ],
        },
        indent=2,
    )


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Build and parse the argument parser."""
    parser = argparse.ArgumentParser(
        prog="tabcalc",
        description="Split group expenses and settle debts with minimum transfers.",
    )

    # Input sources (mutually exclusive)
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "-f", "--file",
        type=Path,
        help="Read expenses from a file (one line per expense)",
    )
    source.add_argument(
        "-e", "--expense",
        action="append",
        dest="inline_expenses",
        help="Add an expense inline: \"Dinner|Alice|45|Alice,Bob,Charlie\" "
             "(can be used multiple times)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
    )

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    """CLI entry point. Returns exit code."""
    args = parse_args(argv)

    expenses: List[Expense] = []

    if args.file:
        expenses = parse_expense_file(args.file)
    elif args.inline_expenses:
        for line in args.inline_expenses:
            expenses.append(parse_expense_line(line))
    else:
        # Read from stdin
        print("Enter expenses (one per line, Ctrl+D to finish):", file=sys.stderr)
        lines = sys.stdin.read()
        expenses = parse_expense_text(lines)

    if not expenses:
        print("No expenses provided.", file=sys.stderr)
        return 1

    plan = compute_settlement(expenses)

    if args.json:
        print(format_json(plan))
    else:
        print(format_settlement(plan))

    return 0


if __name__ == "__main__":
    sys.exit(main())