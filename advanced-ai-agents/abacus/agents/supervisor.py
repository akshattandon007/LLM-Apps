"""Supervisor — orchestrates the multi-agent loop.

Coordinates: IncomeAgent → ExpenseAgent → ScenarioEngine → GoalTracker → Report
Supports iterative refinement rounds (propose → compute → check → refine)."""

import sys
import json
from models import (FinancialProfile, IncomeStream, Expense, Goal, GoalType,
                    ScenarioResult, FinancialEncoder, IncomeType, ExpenseCategory)
from agents.income_agent import IncomeAgent
from agents.expense_agent import ExpenseAgent
from agents.scenario_engine import ScenarioEngine
from agents.goal_tracker import GoalTracker

from llm import llm_call


class Supervisor:
    """Chief orchestrator — runs the full multi-agent pipeline."""

    def __init__(self):
        self.income_agent = IncomeAgent()
        self.expense_agent = ExpenseAgent()
        self.engine = ScenarioEngine()
        self.goal_tracker = GoalTracker()
        self.profile: FinancialProfile | None = None
        self.goal: Goal | None = None

    def run(self, profile: FinancialProfile, goal: Goal | None = None,
            what_if: str | None = None) -> dict:
        """Execute the full multi-agent financial planning pipeline."""
        self.profile = profile
        self.goal = goal or Goal(name="Build savings", target_amount=profile.savings * 3)

        print("\n══════════════ abacus — Multi-Agent Financial Planner ══════════════\n")

        # ── Round 1: Income Analysis ──
        print("◆ Round 1: Income Agent analyzing streams...")
        self.income_agent.process(self.profile)

        # ── Round 2: Expense Analysis ──
        print("◆ Round 2: Expense Agent categorizing spending...")
        self.expense_agent.process(self.profile)

        # ── Round 3: Baseline scenario ──
        print("◆ Round 3: Scenario Engine — baseline projection...")
        baseline = self.engine.project(self.profile, self.goal, years=5)

        # ── Round 4: Goal Tracker check ──
        print("◆ Round 4: Goal Tracker assessing feasibility...")
        tracking = self.goal_tracker.process(
            self.profile, self.goal, baseline.projected_surplus_5y
        )

        # ── Round 5: What-if scenarios ──
        scenarios_to_run = self._suggest_scenarios(what_if, tracking)
        print(f"◆ Round 5: Running {len(scenarios_to_run)} what-if scenario(s)...")
        all_results = [baseline]
        for name, adj in scenarios_to_run:
            result = self.engine.project(self.profile, self.goal, adjustments=adj)
            all_results.append(result)

        # ── Round 6: Supervisor synthesis ──
        print("◆ Round 6: Supervisor synthesizing final report...\n")
        report = self._synthesize(all_results, tracking, self.goal)
        return report

    def _suggest_scenarios(self, what_if: str | None,
                           tracking: dict) -> list[tuple[str, dict]]:
        """Generate scenarios to run. If user specified a what-if, parse it."""
        scenarios = []

        if what_if:
            # Parse the what-if query into adjustments
            parsed = self._parse_what_if(what_if)
            scenarios.append((what_if[:40], parsed))
        else:
            # Default scenarios
            surplus = self.profile.monthly_surplus
            if surplus > 0:
                scenarios.append((
                    "Save 20% more monthly",
                    {"save_more": round(surplus * 0.2, 2)}
                ))
            if self.profile.debt > 0:
                scenarios.append((
                    "Pay down 50% of debt",
                    {"debt_paydown": round(self.profile.debt * 0.5, 2)}
                ))
            if any(not e.essential for e in self.profile.expenses):
                scenarios.append((
                    "Cut discretionary spending 30%",
                    {"cut_expenses": "30%"}
                ))

        return scenarios[:3]  # max 3 scenario runs

    def _parse_what_if(self, query: str) -> dict:
        """Parse a 'what-if' natural language query into adjustment dict."""
        q = query.lower()
        adjustments = {}

        # Income boost patterns
        if any(w in q for w in ['raise', 'promotion', 'bonus', 'salary increase',
                                'income boost', 'more income', 'new job']):
            import re
            amounts = re.findall(r'\$?([\d,]+)', q.replace(',', ''))
            if amounts:
                adjustments["income_boost"] = float(amounts[0])
            else:
                adjustments["income_boost"] = 10000

        # Save more patterns
        if any(w in q for w in ['save more', 'save extra', 'increase saving',
                                'higher saving']):
            adjustments["save_more"] = 500

        # Cut expenses patterns
        if any(w in q for w in ['cut', 'reduce', 'save on', 'lower expense',
                                'less spend']):
            if "30%" in q or "twenty" in q:
                adjustments["cut_expenses"] = "30%"
            else:
                adjustments["cut_expenses"] = "20%"

        # Debt paydown
        if any(w in q for w in ['pay debt', 'debt payoff', 'pay off debt']):
            import re
            amounts = re.findall(r'\$?([\d,]+)', q.replace(',', ''))
            if amounts and len(amounts) > 0:
                adjustments["debt_paydown"] = float(amounts[0]) if float(amounts[0]) > 100 else float(amounts[0]) * 1000
            else:
                adjustments["debt_paydown"] = 5000

        if not adjustments:
            # Default: boost income
            adjustments["income_boost"] = 10000

        return adjustments

    def _synthesize(self, results: list[ScenarioResult], tracking: dict,
                    goal: Goal) -> dict:
        """Synthesize all results into a final report."""
        if not results:
            return {"error": "No scenarios were run"}

        baseline = results[0]
        alternatives = results[1:]

        # Find best scenario
        best = max(results, key=lambda r: r.total_savings_5y)

        return {
            "profile_summary": {
                "income_streams": len(self.profile.income_streams),
                "total_net_monthly": round(self.profile.total_income_net_monthly(), 2),
                "total_expenses_monthly": round(self.profile.total_expenses_monthly(), 2),
                "monthly_surplus": round(self.profile.compute_surplus(), 2),
                "savings": round(self.profile.savings, 2),
                "debt": round(self.profile.debt, 2),
            },
            "goal": {
                "name": goal.name,
                "target": goal.target_amount,
                "target_date_years": goal.target_date_years,
                "feasible": tracking["feasible"],
                "monthly_needed": tracking["monthly_needed"],
                "gap_per_month": tracking.get("gap_per_month", 0),
            },
            "baseline": {
                "surplus_5y": baseline.projected_surplus_5y,
                "savings_5y": baseline.total_savings_5y,
                "goal_met": baseline.goal_met,
                "goal_progress": baseline.goal_progress_pct,
                "risk": baseline.risk_level,
            },
            "scenarios": [
                {
                    "name": r.scenario_name,
                    "savings_5y": r.total_savings_5y,
                    "goal_met": r.goal_met,
                    "goal_progress": r.goal_progress_pct,
                    "risk": r.risk_level,
                    "summary": r.summary,
                }
                for r in alternatives
            ],
            "recommendation": {
                "best_scenario": best.scenario_name,
                "best_savings_5y": best.total_savings_5y,
                "best_goal_met": best.goal_met,
                "suggested_monthly_contribution": round(
                    max(0, tracking.get("monthly_needed", 0) - tracking.get("gap_per_month", 0)),
                    2
                ),
            },
            "planner_message": self._planner_message(baseline, best),
        }

    def _planner_message(self, baseline: ScenarioResult, best: ScenarioResult) -> str:
        """Generate a human-friendly closing recommendation."""
        if baseline.goal_met:
            return (
                "✅ Your finances are on track to meet your goal within 5 years "
                "without any changes. Keep up the good work!"
            )
        if best.goal_met:
            return (
                f"✅ Your goal is achievable! The '{best.scenario_name}' scenario "
                f"puts you on track with ${best.total_savings_5y:,.0f} saved. "
                "Consider implementing the suggested adjustments."
            )
        return (
            "⚠️ Your goal may not be reachable within the target timeframe "
            "with current projections. Consider extending your timeline or "
            "exploring income/expense adjustments beyond what's modeled here."
        )