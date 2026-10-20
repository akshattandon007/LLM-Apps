"""DebtSlayer — CLI Entry Point.

Usage:
    python3 -m debtslayer --debt "Label:Balance:APR:MinPayment" [--debt ...] --income N --expenses N
    python3 -m debtslayer letter --creditor "Name" --balance N --apr N --hardship "reason"
    python3 -m debtslayer progress --plan plan.json
"""
from __future__ import annotations
import sys
import json
import argparse
from .coordinator import DebtSlayerCoordinator
from . import __version__


def parse_debt_spec(raw: str) -> dict:
    """Parse 'Label:Balance:APR:MinPayment' into a dict."""
    parts = raw.split(":")
    if len(parts) < 4:
        print(f"ERROR: Invalid debt format '{raw}'. Use Label:Balance:APR:MinPayment", file=sys.stderr)
        sys.exit(1)
    label = parts[0].strip()
    try:
        balance = float(parts[1])
        apr = float(parts[2])
        min_pmt = float(parts[3])
    except ValueError:
        print(f"ERROR: Numeric values in '{raw}' are invalid.", file=sys.stderr)
        sys.exit(1)
    return {"label": label, "balance": balance, "apr": apr, "min_payment": min_pmt}


def cmd_analyze(args):
    """Full analysis pipeline."""
    coord = DebtSlayerCoordinator()

    # Load debts
    specs = [parse_debt_spec(d) for d in args.debt]
    coord.load_debts(specs)
    coord.set_budget(args.income, args.expenses)

    result = coord.run_full_analysis()

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    # Print the report
    print()
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║              DEBTSLAYER — DEBT PAYOFF OPTIMIZER              ║")
    print("╠════════════════════════════════════════════════════════════════╣")

    # Inventory
    inv = result["inventory"]
    for d in inv["debts"]:
        print(f"║ {d['label']:15s}  ${d['balance']:>8,.2f} @ {d['apr']:.2f}%  (min ${d['min_payment']:.2f}/mo)  ║")
    print("╠════════════════════════════════════════════════════════════════╣")
    print(f"║ Total Debt: ${inv['total_balance']:>8,.2f}  |  Min Payments: ${inv['total_min_payments']:.2f}/mo  ║")
    print(f"║ Income: ${result['spending']['monthly_income']:.2f}/mo  |  Expenses: ${result['spending']['monthly_expenses']:.2f}/mo  ║")
    print(f"║ Surplus: ${result['spending']['monthly_surplus']:.2f}/mo                              ║")
    print("╚════════════════════════════════════════════════════════════════╝")

    # Strategy
    comp = result["strategy_comparison"]
    if comp["recommendation"] != "none":
        av = comp["avalanche"]
        sb = comp["snowball"]
        print(f"\n📊 STRATEGY COMPARISON:")
        print(f"   Avalanche: {av['months']} mo  |  ${av['total_interest']:.2f} interest")
        print(f"   Snowball:  {sb['months']} mo  |  ${sb['total_interest']:.2f} interest")
        print(f"\n🏆 RECOMMENDED: {comp['recommendation'].upper()} — {comp['reason']}")

        plan = result["recommended_plan"]
        if plan:
            print(f"\n📅 PAYOFF PLAN ({plan['method']} method):")
            print(f"   Duration: {plan['months_to_payoff']} months")
            print(f"   Total Interest: ${plan['total_interest']:.2f}")
            saved_label = result.get("interest_saved_label")
            if saved_label:
                print(f"   Interest Saved vs Minimum Only: {saved_label}")
            else:
                print(f"   Interest Saved vs Minimum Only: ${result['interest_saved_vs_minimum_only']:.2f}")
    else:
        print(f"\n⚠️  {comp['reason']}")

    # Tips
    print(f"\n💡 SUGGESTIONS:")
    for tip in result["savings_tips"]:
        print(f"   • {tip}")

    # Letters
    print(f"\n📄 GENERATED LETTERS:")
    for l in result["letters"]:
        print(f"   • {l['creditor']} — {len(l['letter_text'])} chars")
        print(f"     (View with: cat /tmp/{l['creditor'].lower()}_letter.txt)")

    # Save letters
    for l in result["letters"]:
        letter_path = f"/tmp/{l['creditor'].lower()}_letter.txt"
        with open(letter_path, "w") as f:
            f.write(l["letter_text"])

    print()
    return True


def cmd_letter(args):
    """Generate a single creditor letter."""
    from .agents.letter_agent import LetterAgent
    agent = LetterAgent()
    letter = agent.draft_letter(
        creditor=args.creditor,
        balance=args.balance,
        apr=args.apr,
        hardship_reason=args.hardship,
    )
    print(letter.to_text())
    return True


def cmd_progress(args):
    """Show progress from a saved plan."""
    from .agents.progress_agent import ProgressAgent
    try:
        with open(args.plan) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Cannot read plan '{args.plan}': {e}")
        sys.exit(1)

    from .models import Debt
    debts = [Debt.from_json(d) for d in data.get("debts", [])]
    from .models import PayoffPlan
    plan = PayoffPlan(
        debts=debts,
        monthly_surplus=data.get("monthly_surplus", 0),
        method=data.get("method", "avalanche"),
        months_to_payoff=data.get("months_to_payoff", 0),
        total_interest=data.get("total_interest", 0),
    )
    summary = ProgressAgent.progress_summary(plan)
    print(f"\n📊 PROGRESS REPORT")
    print(f"   Method: {summary['method'].title()}")
    print(f"   Total Plan: {summary['total_months']} months")
    print(f"   Completed: {summary['months_completed']} ({summary['percent_complete']}%)")
    print(f"   Remaining: {summary['months_remaining']} months")
    print(f"   Projected Completion: {summary['projected_completion']}")
    print(f"   On Track: {'✅' if summary['on_track'] else '⚠️ Needs attention'}")
    print()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="DebtSlayer — Multi-Agent Debt Payoff Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    # Top-level args for the default analyze command
    parser.add_argument("--debt", "-d", action="append", default=None,
                        help="Debt spec: Label:Balance:APR:MinPayment")
    parser.add_argument("--income", "-i", type=float, default=None)
    parser.add_argument("--expenses", "-e", type=float, default=None)
    parser.add_argument("--date", default=None, help="Date suffix for output file")

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Analyze subcommand (also reachable via top-level args)
    analyze_parser = subparsers.add_parser("analyze", help="Run full debt analysis")
    analyze_parser.add_argument("--debt", "-d", action="append", required=True,
                                help="Debt spec: Label:Balance:APR:MinPayment")
    analyze_parser.add_argument("--income", "-i", type=float, required=True)
    analyze_parser.add_argument("--expenses", "-e", type=float, required=True)
    analyze_parser.add_argument("--date", default=None, help="Date suffix for output file")

    # Letter command
    letter_parser = subparsers.add_parser("letter", help="Generate a creditor letter")
    letter_parser.add_argument("--creditor", required=True)
    letter_parser.add_argument("--balance", type=float, required=True)
    letter_parser.add_argument("--apr", type=float, required=True)
    letter_parser.add_argument("--hardship", default="unexpected financial difficulties")

    # Progress command
    progress_parser = subparsers.add_parser("progress", help="Show payoff progress")
    progress_parser.add_argument("--plan", required=True, help="Path to saved plan JSON")

    args = parser.parse_args()

    if args.command == "letter":
        return cmd_letter(args)
    elif args.command == "progress":
        return cmd_progress(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    elif args.debt is not None and args.income is not None:
        # Top-level shorthand — run analyze
        return cmd_analyze(args)
    else:
        parser.print_help()
        return False


if __name__ == "__main__":
    main()