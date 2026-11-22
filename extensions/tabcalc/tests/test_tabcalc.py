"""Tests for TabCalc core logic and CLI."""

from __future__ import annotations

from decimal import Decimal

import pytest

from tabcalc.core import (
    Expense,
    compute_balances,
    compute_minimum_transfers,
    compute_settlement,
)
from tabcalc.cli import parse_expense_line, format_settlement, format_json


# ---------------------------------------------------------------------------
# Core: compute_balances
# ---------------------------------------------------------------------------

class TestComputeBalances:
    def test_single_expense_equal_split(self):
        expenses = [
            Expense(
                description="Dinner",
                paid_by="Alice",
                amount=Decimal("60"),
                split_among=["Alice", "Bob", "Charlie"],
            )
        ]
        balances = compute_balances(expenses)
        bal = {p.name: p.net_balance for p in balances}

        # Each person's share = 20. Alice paid 60 so she's owed 40
        assert bal["Alice"] == Decimal("40.00")  # 60 - 20
        assert bal["Bob"] == Decimal("-20.00")
        assert bal["Charlie"] == Decimal("-20.00")

    def test_multiple_expenses_across_people(self):
        expenses = [
            Expense("Dinner", "Alice", Decimal("45"), ["Alice", "Bob", "Charlie"]),
            Expense("Drinks", "Bob", Decimal("30"), ["Alice", "Bob", "Charlie"]),
            Expense("Taxi", "Charlie", Decimal("15"), ["Alice", "Bob", "Charlie"]),
        ]
        balances = compute_balances(expenses)
        bal = {p.name: p.net_balance for p in balances}

        # Total = 90, per person = 30
        # Alice paid 45 → net +15
        # Bob paid 30 → net 0
        # Charlie paid 15 → net -15
        assert bal["Alice"] == Decimal("15.00")
        assert bal["Bob"] == Decimal("0.00")
        assert bal["Charlie"] == Decimal("-15.00")

    def test_uneven_splits(self):
        """Some expenses split among a subset of the group."""
        expenses = [
            Expense("Dinner", "Alice", Decimal("30"), ["Alice", "Bob"]),
            Expense("Movie", "Bob", Decimal("20"), ["Bob", "Charlie"]),
        ]
        balances = compute_balances(expenses)
        bal = {p.name: p.net_balance for p in balances}

        # Dinner: share=15, Alice paid 30 so +15, Bob owes 15
        # Movie: share=10, Bob paid 20 so +10 (net from dinner: -15+10=-5), Charlie owes 10
        assert bal["Alice"] == Decimal("15.00")
        assert bal["Bob"] == Decimal("-5.00")
        assert bal["Charlie"] == Decimal("-10.00")

    def test_empty_expenses_returns_empty(self):
        assert compute_balances([]) == []


# ---------------------------------------------------------------------------
# Core: compute_minimum_transfers
# ---------------------------------------------------------------------------

class TestComputeMinimumTransfers:
    def test_simple_two_person(self):
        balances = compute_balances([
            Expense("Coffee", "Alice", Decimal("10"), ["Alice", "Bob"]),
        ])
        transfers = compute_minimum_transfers(balances)
        assert len(transfers) == 1
        assert transfers[0].from_person == "Bob"
        assert transfers[0].to_person == "Alice"
        assert transfers[0].amount == Decimal("5.00")

    def test_three_person_chain(self):
        balances = compute_balances([
            Expense("Dinner", "Alice", Decimal("90"), ["Alice", "Bob", "Charlie"]),
        ])
        transfers = compute_minimum_transfers(balances)
        # Each owes 30. Alice paid 90 → is owed 60
        # Should have 2 transfers: Bob→Alice 30, Charlie→Alice 30
        assert len(transfers) == 2
        assert sum(t.amount for t in transfers) == Decimal("60.00")

    def test_balanced_expenses_no_transfers(self):
        balances = compute_balances([
            Expense("Dinner", "Alice", Decimal("30"), ["Alice", "Bob"]),
            Expense("Drinks", "Bob", Decimal("30"), ["Alice", "Bob"]),
        ])
        transfers = compute_minimum_transfers(balances)
        assert len(transfers) == 0

    def test_rounding_edge_case(self):
        """Amounts that don't divide evenly ($10 split 3 ways)."""
        balances = compute_balances([
            Expense("Pizza", "Alice", Decimal("10"), ["Alice", "Bob", "Charlie"]),
        ])
        transfers = compute_minimum_transfers(balances)
        # Each share = 3.33 (rounded). 3 * 3.33 = 9.99, so there's a 0.01 remainder
        assert len(transfers) == 2
        # $10 split 3 ways leaves a $0.01 remainder in quantized math;
        # the sum of transfers accounts for the rounding (6.66 not 6.67).
        assert sum(t.amount for t in transfers) in {Decimal("6.66"), Decimal("6.67")}


# ---------------------------------------------------------------------------
# Core: compute_settlement (integration)
# ---------------------------------------------------------------------------

class TestComputeSettlement:
    def test_full_pipeline(self):
        expenses = [
            Expense("Hotel", "Alice", Decimal("200"), ["Alice", "Bob", "Charlie"]),
            Expense("Gas", "Bob", Decimal("60"), ["Alice", "Bob"]),
            Expense("Food", "Charlie", Decimal("90"), ["Alice", "Bob", "Charlie"]),
        ]
        plan = compute_settlement(expenses)
        assert plan.total_spent == Decimal("350.00")
        assert len(plan.participants) == 3
        assert len(plan.transfers) >= 1  # at least one transfer needed


# ---------------------------------------------------------------------------
# CLI: parse_expense_line
# ---------------------------------------------------------------------------

class TestParseExpenseLine:
    def test_basic_line(self):
        exp = parse_expense_line("Dinner | Alice | 45.00 | Alice,Bob,Charlie")
        assert exp.description == "Dinner"
        assert exp.paid_by == "Alice"
        assert exp.amount == Decimal("45.00")
        assert exp.split_among == ["Alice", "Bob", "Charlie"]

    def test_line_with_whitespace(self):
        exp = parse_expense_line("  Lunch  |  Bob  |  12.50  |  Bob, Charlie ")
        assert exp.description == "Lunch"
        assert exp.paid_by == "Bob"
        assert exp.amount == Decimal("12.50")
        assert exp.split_among == ["Bob", "Charlie"]

    def test_invalid_line_too_few_parts(self):
        with pytest.raises(ValueError):
            parse_expense_line("Dinner | Alice | 45")

    def test_invalid_amount(self):
        with pytest.raises(ValueError):
            parse_expense_line("Dinner | Alice | abc | Alice,Bob")


# ---------------------------------------------------------------------------
# CLI: formatting
# ---------------------------------------------------------------------------

class TestFormatting:
    def test_format_settlement_contains_names(self):
        expenses = [
            Expense("Dinner", "Alice", Decimal("45"), ["Alice", "Bob"]),
        ]
        plan = compute_settlement(expenses)
        text = format_settlement(plan)
        assert "Alice" in text
        assert "Bob" in text
        assert "$22.50" in text
        assert "SETTLEMENT PLAN" in text

    def test_format_json_valid(self):
        expenses = [
            Expense("Dinner", "Alice", Decimal("45"), ["Alice", "Bob"]),
        ]
        plan = compute_settlement(expenses)
        data = format_json(plan)
        import json
        parsed = json.loads(data)
        assert "transfers" in parsed
        assert "balances" in parsed
        assert parsed["total_spent"] == 45.0