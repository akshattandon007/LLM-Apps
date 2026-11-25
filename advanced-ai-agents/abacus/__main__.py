"""CLI entry point for abacus — Multi-Agent Financial Scenario Planner.

Usage:
    python -m abacus --income "salary 85000" --expenses "rent 1800" --goal "buy house"
    python -m abacus --income "salary 85000,freelance 12000" --expenses "rent 1800,groceries 600" --what-if "what if I get a 15k raise"
    python -m abacus --interactive
"""

import sys
import os
# Allow running from the project directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from models import FinancialProfile, IncomeStream, Expense, Goal, GoalType, IncomeType, ExpenseCategory
from agents.income_agent import IncomeAgent
from agents.expense_agent import ExpenseAgent
from agents.supervisor import Supervisor


def build_profile(args) -> FinancialProfile:
    """Build a FinancialProfile from CLI args or interactive input."""
    profile = FinancialProfile()
    income_agent = IncomeAgent()
    expense_agent = ExpenseAgent()

    # Parse income
    if args.income:
        for part in args.income.split(","):
            part = part.strip()
            if part:
                try:
                    stream = income_agent.parse_income_line(part)
                    profile.income_streams.append(stream)
                except ValueError:
                    print(f"  [Warning] Could not parse income: '{part}'", file=sys.stderr)

    # Parse expenses
    if args.expenses:
        for part in args.expenses.split(","):
            part = part.strip()
            if part:
                try:
                    exp = expense_agent.parse_expense_line(part)
                    profile.expenses.append(exp)
                except ValueError:
                    print(f"  [Warning] Could not parse expense: '{part}'", file=sys.stderr)

    # Direct fields
    if args.savings:
        profile.savings = args.savings
    if args.debt:
        profile.debt = args.debt
    if args.age:
        profile.age = args.age
    if args.location:
        profile.location = args.location

    return profile


def build_goal(args) -> Goal | None:
    """Build a Goal from CLI args."""
    if args.goal:
        g = args.goal.lower()
        if "house" in g or "down payment" in g:
            goal_type = GoalType.HOUSE_DOWN_PAYMENT
        elif "retire" in g or "retirement" in g:
            goal_type = GoalType.RETIREMENT
        elif "emergency" in g or "fund" in g:
            goal_type = GoalType.EMERGENCY_FUND
        elif "debt" in g or "free" in g:
            goal_type = GoalType.DEBT_FREEDOM
        elif "vacation" in g or "trip" in g:
            goal_type = GoalType.VACATION
        elif "car" in g or "vehicle" in g:
            goal_type = GoalType.CAR
        else:
            goal_type = GoalType.CUSTOM

        return Goal(
            name=g,
            goal_type=goal_type,
            target_amount=args.target or 0,
            target_date_years=args.years or 5,
        )
    return None


def interactive_mode():
    """Run in interactive mode — guide user through data entry."""
    print("\n══════════ abacus — Interactive Setup ══════════\n")
    print("Enter your financial info. Press Enter with no value to skip.\n")

    profile = FinancialProfile()
    income_agent = IncomeAgent()
    expense_agent = ExpenseAgent()

    # Income
    print("── Income Streams ──")
    print("(e.g., 'salary 85000', 'freelance web 15000', or blank to finish)")
    while True:
        inp = input("  Income: ").strip()
        if not inp:
            break
        try:
            stream = income_agent.parse_income_line(inp)
            profile.income_streams.append(stream)
            print(f"  → Added: ${stream.amount:,.0f}/yr ({stream.income_type.value})")
        except ValueError as e:
            print(f"  {e}")

    # Expenses
    print("\n── Monthly Expenses ──")
    print("(e.g., 'rent 1800', 'groceries 600', or blank to finish)")
    while True:
        inp = input("  Expense: ").strip()
        if not inp:
            break
        try:
            exp = expense_agent.parse_expense_line(inp)
            profile.expenses.append(exp)
            print(f"  → Added: ${exp.amount:,.0f}/mo ({exp.category.value})")
        except ValueError as e:
            print(f"  {e}")

    # Savings & debt
    inp = input("\nCurrent savings ($): ").strip()
    if inp:
        try:
            profile.savings = float(inp.replace("$", "").replace(",", ""))
        except ValueError:
            pass

    inp = input("Current debt ($): ").strip()
    if inp:
        try:
            profile.debt = float(inp.replace("$", "").replace(",", ""))
        except ValueError:
            pass

    inp = input("Your age: ").strip()
    if inp:
        try:
            profile.age = int(inp)
        except ValueError:
            pass

    # Goal
    print("\n── Your Financial Goal ──")
    goal = None
    inp = input("Goal (e.g., 'buy house in 5 years', or blank to skip): ").strip()
    if inp:
        target = input("  Target amount ($): ").strip()
        target_amt = float(target.replace("$", "").replace(",", "")) if target else 0
        years = input("  Years to achieve: ").strip()
        goal = Goal(
            name=inp,
            target_amount=target_amt,
            target_date_years=int(years) if years else 5,
        )

    # What-if
    what_if = input("\nWhat-if scenario (optional, e.g., 'what if I get a 10k raise'): ").strip()

    return profile, goal, what_if


def main():
    parser = argparse.ArgumentParser(
        description="abacus — Multi-Agent Financial Scenario Planner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m abacus --income "salary 85000" --expenses "rent 1800,groceries 600" --goal "buy house" --target 60000
  python -m abacus --income "salary 85000,freelance 12000" --expenses "rent 1800" --debt 15000 --what-if "what if I pay off half my debt"
  python -m abacus --interactive
        """,
    )
    parser.add_argument("--income", help="Comma-separated income streams (e.g., 'salary 85000,freelance 12000')")
    parser.add_argument("--expenses", help="Comma-separated monthly expenses (e.g., 'rent 1800,groceries 600')")
    parser.add_argument("--savings", type=float, help="Current savings amount ($)")
    parser.add_argument("--debt", type=float, help="Current total debt ($)")
    parser.add_argument("--age", type=int, help="Your age")
    parser.add_argument("--location", help="Your location (for tax estimates)")
    parser.add_argument("--goal", help="Your financial goal (e.g., 'buy house', 'retire early')")
    parser.add_argument("--target", type=float, help="Goal target amount ($)")
    parser.add_argument("--years", type=int, default=5, help="Years to achieve goal (default: 5)")
    parser.add_argument("--what-if", help="What-if scenario to model (e.g., 'what if I get a 15k raise')")
    parser.add_argument("--interactive", action="store_true", help="Interactive data entry mode")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if args.interactive:
        profile, goal, what_if = interactive_mode()
    else:
        if not args.income and not args.expenses:
            parser.print_help()
            print("\nError: Provide --income and --expenses, or use --interactive")
            sys.exit(1)
        profile = build_profile(args)
        goal = build_goal(args)
        what_if = args.what_if

    if not profile.income_streams:
        print("Error: At least one income stream is required.")
        sys.exit(1)

    # Run the multi-agent pipeline
    supervisor = Supervisor()
    report = supervisor.run(profile, goal, what_if=what_if)

    # ── Output ──
    print("\n" + "═" * 70)
    print("📊  ABACUS — FINANCIAL SCENARIO REPORT")
    print("═" * 70)

    p = report["profile_summary"]
    print(f"\n📋 PROFILE")
    print(f"   Income:     {p['income_streams']} stream(s) · ${p['total_net_monthly']:,.0f}/mo net")
    print(f"   Expenses:   ${p['total_expenses_monthly']:,.0f}/mo")
    print(f"   Surplus:    ${p['monthly_surplus']:,.0f}/mo")
    print(f"   Savings:    ${p['savings']:,.0f}  |  Debt: ${p['debt']:,.0f}")

    g = report["goal"]
    print(f"\n🎯 GOAL: {g['name']}")
    print(f"   Target:     ${g['target']:,.0f} in {g['target_date_years']} yr(s)")
    print(f"   Needed/mo:  ${g['monthly_needed']:,.0f}  |  {'✅ Feasible' if g['feasible'] else '⚠️ Needs adjustment'}")

    b = report["baseline"]
    print(f"\n📈 BASELINE (5-year projection)")
    print(f"   Surplus:    ${b['surplus_5y']:,.0f}/mo")
    print(f"   Savings:    ${b['savings_5y']:,.0f}")
    print(f"   Goal met:   {'Yes ✅' if b['goal_met'] else 'No ❌'} ({b['goal_progress']:.0f}%)")
    print(f"   Risk:       {b['risk'].upper()}")

    if report["scenarios"]:
        print(f"\n🔄 SCENARIOS")
        for s in report["scenarios"]:
            print(f"   • {s['name']}: ${s['savings_5y']:,.0f} savings | "
                  f"{'✅ Met' if s['goal_met'] else '❌ Missed'} | "
                  f"Risk: {s['risk'].upper()}")

    r = report["recommendation"]
    print(f"\n⭐ RECOMMENDATION")
    print(f"   Best path:  {r['best_scenario']}")
    print(f"   Savings:    ${r['best_savings_5y']:,.0f}")
    print(f"   Suggested monthly contribution: ${r['suggested_monthly_contribution']:,.0f}")
    print(f"\n   {report['planner_message']}")
    print("\n" + "═" * 70)

    if args.json:
        import json
        print(json.dumps(report, indent=2, cls=type('Encoder', (),
            {'encode': lambda self, o: json.dumps(o, indent=2, default=str)})))

    return report


if __name__ == "__main__":
    main()