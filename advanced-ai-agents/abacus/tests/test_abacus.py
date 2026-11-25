"""Tests for abacus financial planner."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models import (FinancialProfile, IncomeStream, Expense, Goal, GoalType,
                    IncomeType, ExpenseCategory)
from agents.income_agent import IncomeAgent
from agents.expense_agent import ExpenseAgent
from agents.scenario_engine import ScenarioEngine
from agents.goal_tracker import GoalTracker


class TestModels:
    def test_income_stream_net(self):
        s = IncomeStream("salary", 85000, income_type=IncomeType.SALARY, tax_rate=0.22)
        assert abs(s.net_annual - 66300) < 1
        assert abs(s.net_monthly - 5525) < 1

    def test_expense_categories(self):
        e = Expense("rent", 1800, category=ExpenseCategory.HOUSING)
        assert e.essential is True
        assert e.amount == 1800

    def test_profile_compute_surplus(self):
        profile = FinancialProfile(
            income_streams=[IncomeStream("salary", 85000, tax_rate=0.22)],
            expenses=[Expense("rent", 1800), Expense("food", 600)],
        )
        surplus = profile.compute_surplus()
        # net monthly = 85000 * 0.78 / 12 = 5525
        # expenses = 1800 + 600 = 2400
        # surplus = 5525 - 2400 = 3125
        assert abs(surplus - 3125) < 2

    def test_goal_amount_needed(self):
        g = Goal("buy house", target_amount=60000, current_progress=5000)
        assert g.amount_needed() == 55000

    def test_goal_already_met(self):
        g = Goal("save", target_amount=5000, current_progress=10000)
        assert g.amount_needed() == 0


class TestIncomeAgent:
    def test_parse_salary(self):
        agent = IncomeAgent()
        s = agent.parse_income_line("salary 85000")
        assert s.amount == 85000
        assert s.income_type == IncomeType.SALARY

    def test_parse_freelance(self):
        agent = IncomeAgent()
        s = agent.parse_income_line("freelance web dev 45000")
        assert s.amount == 45000
        assert s.income_type == IncomeType.FREELANCE

    def test_parse_without_amount(self):
        agent = IncomeAgent()
        s = agent.parse_income_line("side hustle")
        assert s.amount == 0  # no amount found

    def test_empty_raises(self):
        agent = IncomeAgent()
        with pytest.raises(ValueError):
            agent.parse_income_line("")


class TestExpenseAgent:
    def test_parse_rent(self):
        agent = ExpenseAgent()
        e = agent.parse_expense_line("rent 1800")
        assert e.amount == 1800
        assert e.category == ExpenseCategory.HOUSING
        assert e.essential is True

    def test_parse_groceries(self):
        agent = ExpenseAgent()
        e = agent.parse_expense_line("groceries 600")
        assert e.amount == 600
        assert e.category == ExpenseCategory.FOOD

    def test_parse_entertainment(self):
        agent = ExpenseAgent()
        e = agent.parse_expense_line("netflix 15")
        assert e.category == ExpenseCategory.ENTERTAINMENT
        assert e.essential is False

    def test_empty_raises(self):
        agent = ExpenseAgent()
        with pytest.raises(ValueError):
            agent.parse_expense_line("")


class TestScenarioEngine:
    def test_baseline_projection(self):
        engine = ScenarioEngine()
        profile = FinancialProfile(
            income_streams=[IncomeStream("salary", 85000, tax_rate=0.22)],
            expenses=[Expense("rent", 1800), Expense("food", 600)],
            savings=10000,
        )
        goal = Goal("buy house", target_amount=60000, target_date_years=5)
        result = engine.project(profile, goal)
        assert result.scenario_name == "Baseline"
        assert result.total_savings_5y > 0
        assert isinstance(result.goal_met, bool)
        assert result.risk_level in ("low", "medium", "high")

    def test_income_boost_scenario(self):
        engine = ScenarioEngine()
        profile = FinancialProfile(
            income_streams=[IncomeStream("salary", 50000, tax_rate=0.22)],
            expenses=[Expense("rent", 1500), Expense("food", 500)],
            savings=5000,
        )
        goal = Goal("save", target_amount=30000)
        baseline = engine.project(profile, goal, adjustments={})
        boosted = engine.project(profile, goal, adjustments={"income_boost": 10000})
        assert boosted.total_savings_5y >= baseline.total_savings_5y

    def test_debt_impact(self):
        engine = ScenarioEngine()
        profile = FinancialProfile(
            income_streams=[IncomeStream("salary", 60000, tax_rate=0.22)],
            expenses=[Expense("rent", 1200)],
            savings=2000,
            debt=15000,
            debt_interest=0.05,
        )
        goal = Goal("save", target_amount=20000)
        result = engine.project(profile, goal)
        assert result.total_savings_5y >= 0  # should still be positive


class TestGoalTracker:
    def test_feasible_goal(self):
        tracker = GoalTracker()
        goal = Goal("buy house", target_amount=60000, target_date_years=5)
        result = tracker.process(
            FinancialProfile(
                income_streams=[IncomeStream("salary", 100000, tax_rate=0.22)],
                expenses=[Expense("rent", 2000)],
                savings=20000,
            ),
            goal,
            projected_surplus=4000,
        )
        assert result["feasible"] is True

    def test_infeasible_goal(self):
        tracker = GoalTracker()
        goal = Goal("retire", target_amount=2000000, target_date_years=5)
        result = tracker.process(
            FinancialProfile(
                income_streams=[IncomeStream("salary", 50000, tax_rate=0.22)],
                expenses=[Expense("rent", 1800)],
                savings=5000,
            ),
            goal,
            projected_surplus=500,
        )
        assert result["feasible"] is False or result["gap_per_month"] > 0

    def test_suggest_contribution(self):
        tracker = GoalTracker()
        goal = Goal("save", target_amount=12000, target_date_years=1)
        result = tracker.suggest_contribution(goal, 2000)
        assert result["suggested_monthly"] > 0
        assert "estimated_years" in result