"""Tests for the Coordinator."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from debtslayer.coordinator import DebtSlayerCoordinator


def test_empty_coordinator():
    coord = DebtSlayerCoordinator()
    result = coord.run_full_analysis()
    assert "error" in result


def test_full_pipeline():
    coord = DebtSlayerCoordinator()
    coord.load_debts([
        {"label": "Visa", "balance": 4500, "apr": 22.99, "min_payment": 50},
        {"label": "MC", "balance": 3200, "apr": 18.0, "min_payment": 40},
    ])
    coord.set_budget(5000, 3000)
    result = coord.run_full_analysis()
    assert "error" not in result
    assert "inventory" in result
    assert result["inventory"]["total_balance"] == 7700
    assert result["spending"]["monthly_surplus"] == 2000
    assert result["strategy_comparison"]["recommendation"] in ("avalanche", "snowball")
    assert result["recommended_plan"] is not None
    assert len(result["letters"]) == 2
    # Interest saved may be 0 if minimums don't cover interest (N/A)
    assert result["interest_saved_vs_minimum_only"] >= 0  # either 0 or positive


def test_letters_generated():
    coord = DebtSlayerCoordinator()
    coord.load_debts([{"label": "Visa", "balance": 1000, "apr": 15.0, "min_payment": 25}])
    coord.set_budget(3000, 2000)
    result = coord.run_full_analysis()
    for letter in result["letters"]:
        assert "Visa" in letter["creditor"]
        assert "APR" in letter["letter_text"] or "apr" in letter["letter_text"]
        assert "DebtSlayer" in letter["letter_text"]