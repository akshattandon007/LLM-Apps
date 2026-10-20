"""Tests for the Strategy Agent."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from debtslayer.models import Debt
from debtslayer.agents.strategy_agent import StrategyAgent


def test_avalanche_order():
    agent = StrategyAgent()
    debts = [
        Debt("HighAPR", 1000, 24.0, 25),
        Debt("LowAPR", 1000, 5.0, 25),
        Debt("MidAPR", 1000, 12.0, 25),
    ]
    plan = agent.compute_plan(debts, monthly_surplus=500, method="avalanche")
    # First debt in ordered list should be highest APR
    assert plan.debts[0].label == "HighAPR"
    assert plan.debts[2].label == "LowAPR"


def test_snowball_order():
    agent = StrategyAgent()
    debts = [
        Debt("Big", 5000, 12.0, 50),
        Debt("Small", 500, 18.0, 25),
        Debt("Medium", 2000, 15.0, 40),
    ]
    plan = agent.compute_plan(debts, monthly_surplus=500, method="snowball")
    assert plan.debts[0].label == "Small"
    assert plan.debts[2].label == "Big"


def test_single_debt_payoff():
    agent = StrategyAgent()
    debts = [Debt("Visa", 1200, 18.0, 50)]
    plan = agent.compute_plan(debts, monthly_surplus=200, method="avalanche")
    assert plan.months_to_payoff > 0
    assert plan.months_to_payoff < 12  # 1200 at 250/mo = ~5 months
    assert plan.total_interest > 0


def test_zero_surplus():
    """With zero surplus, minimum payments only — should still pay off eventually."""
    agent = StrategyAgent()
    debts = [Debt("Visa", 500, 18.0, 25)]
    plan = agent.compute_plan(debts, monthly_surplus=0, method="avalanche")
    assert plan.months_to_payoff > 0
    assert plan.total_interest > 0


def test_compare_strategies_avalanche_wins():
    """High APR difference should favor avalanche."""
    agent = StrategyAgent()
    debts = [
        Debt("HighAPR", 5000, 29.99, 100),
        Debt("LowAPR", 5000, 6.0, 100),
    ]
    comparison = agent.compare_strategies(debts, monthly_surplus=500)
    assert comparison["recommendation"] == "avalanche"
    assert comparison["avalanche"]["total_interest"] <= comparison["snowball"]["total_interest"]  # avalanche never worse


def test_compare_strategies_small_surplus():
    """Very small surplus should still work."""
    agent = StrategyAgent()
    debts = [Debt("Test", 1000, 10.0, 10)]
    comparison = agent.compare_strategies(debts, monthly_surplus=10)
    assert comparison["recommendation"] in ("avalanche", "snowball", "none")