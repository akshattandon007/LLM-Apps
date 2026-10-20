"""Coordinator Agent — orchestrates the multi-agent debt payoff system."""
from __future__ import annotations
import json
from typing import Optional
from .models import Debt, PayoffPlan
from .agents.creditor_agent import CreditorAgent
from .agents.spending_agent import SpendingAgent
from .agents.strategy_agent import StrategyAgent
from .agents.letter_agent import LetterAgent
from .agents.progress_agent import ProgressAgent


class DebtSlayerCoordinator:
    """Central coordinator that manages the team of specialist agents."""

    def __init__(self):
        self.creditor_agent = CreditorAgent()
        self.spending_agent = SpendingAgent()
        self.strategy_agent = StrategyAgent()
        self.letter_agent = LetterAgent()
        self.progress_agent = ProgressAgent()

    def load_debts(self, debt_specs: list[dict]) -> list[Debt]:
        """Load debt accounts from dict specs (e.g. parsed CLI args)."""
        for spec in debt_specs:
            self.creditor_agent.add_debt(
                label=spec["label"],
                balance=spec["balance"],
                apr=spec["apr"],
                min_payment=spec["min_payment"],
            )
        return self.creditor_agent.debts

    def set_budget(self, income: float, expenses: float) -> None:
        self.spending_agent.set_profile(income, expenses)

    def run_full_analysis(self) -> dict:
        """Run the complete multi-agent pipeline.

        Returns a structured result with inventory, strategy comparison,
        recommended plan, and letters.
        """
        debts = self.creditor_agent.debts
        if not debts:
            return {"error": "No debts loaded. Use --debt or interactive mode."}

        surplus = self.spending_agent.surplus
        total_min = self.creditor_agent.total_min_payments()
        total_balance = self.creditor_agent.total_balance()

        # Step 1: Spending analysis
        spending = self.spending_agent.analyze()
        tips = self.spending_agent.suggestions()

        # Step 2: Strategy comparison
        comparison = self.strategy_agent.compare_strategies(debts, surplus)

        # Step 3: Generate the recommended plan
        rec = comparison["recommendation"]
        if rec == "none":
            plan = None
        else:
            plan = self.strategy_agent.compute_plan(debts, surplus, rec)

        # Step 4: Draft letters
        letters = []
        for debt in debts:
            letter = self.letter_agent.draft_letter(
                creditor=debt.label,
                balance=debt.balance,
                apr=debt.apr,
                hardship_reason="high APR and current financial situation",
            )
            letters.append({
                "creditor": debt.label,
                "letter_text": letter.to_text(),
            })

        # Step 5: Calculate interest saved vs minimum-only payments
        # Minimum-only simulation: if minimums don't cover interest (debt grows),
        # show N/A instead of an absurd number.
        interest_saved = 0.0
        interest_saved_label = None
        if surplus > 0 and plan:
            min_only_plan = self.strategy_agent.compute_plan(
                debts, 0.0, "avalanche"
            )
            # If min-only took 1200 months, it's essentially never paying off
            if min_only_plan.months_to_payoff < 1200:
                interest_saved = round(min_only_plan.total_interest - plan.total_interest, 2)
            else:
                interest_saved_label = "N/A (minimums don't cover interest)"

        return {
            "inventory": {
                "debts": [
                    {"label": d.label, "balance": d.balance, "apr": d.apr,
                     "min_payment": d.min_payment}
                    for d in debts
                ],
                "total_balance": total_balance,
                "total_min_payments": total_min,
            },
            "spending": spending,
            "savings_tips": tips,
            "strategy_comparison": comparison,
            "recommended_plan": plan.to_json() if plan else None,
            "interest_saved_vs_minimum_only": interest_saved,
            "interest_saved_label": interest_saved_label,
            "letters": letters,
        }

    def save_plan(self, plan: PayoffPlan, path: str) -> str:
        """Save a payoff plan to a JSON file."""
        with open(path, "w") as f:
            json.dump(plan.to_json(), f, indent=2)
        return path