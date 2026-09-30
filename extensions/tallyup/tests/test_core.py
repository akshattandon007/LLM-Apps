"""
Tests for TallyUp core logic.
"""

from decimal import Decimal
from tallyup.core import Expense, compute_balances, settle_debts, format_report


def test_balances_simple():
    """Two people, one expense split equally."""
    expenses = [
        Expense(
            description="Dinner",
            amount=Decimal("40.00"),
            paid_by="Alice",
            participants=["Alice", "Bob"],
        )
    ]
    balances = compute_balances(expenses)
    assert balances["Alice"] == Decimal("20.00"), f"Expected 20.00, got {balances['Alice']}"
    assert balances["Bob"] == Decimal("-20.00"), f"Expected -20.00, got {balances['Bob']}"


def test_balances_three_people():
    """Three people, one expense split equally."""
    expenses = [
        Expense(
            description="Pizza",
            amount=Decimal("30.00"),
            paid_by="Alice",
            participants=["Alice", "Bob", "Carol"],
        )
    ]
    balances = compute_balances(expenses)
    assert balances["Alice"] == Decimal("20.00"), f"Expected 20.00, got {balances['Alice']}"
    assert balances["Bob"] == Decimal("-10.00"), f"Expected -10.00, got {balances['Bob']}"
    assert balances["Carol"] == Decimal("-10.00"), f"Expected -10.00, got {balances['Carol']}"


def test_settle_simple():
    """Alice paid for Bob — Bob owes Alice."""
    expenses = [
        Expense(
            description="Lunch",
            amount=Decimal("15.00"),
            paid_by="Alice",
            participants=["Bob"],
        )
    ]
    settlements = settle_debts(expenses)
    assert len(settlements) == 1
    assert settlements[0].from_person == "Bob"
    assert settlements[0].to_person == "Alice"
    assert settlements[0].amount == Decimal("15.00")


def test_settle_balanced():
    """Everyone paid their own share — no transfer needed."""
    expenses = [
        Expense(
            description="Coffee",
            amount=Decimal("5.00"),
            paid_by="Alice",
            participants=["Alice"],
        ),
        Expense(
            description="Tea",
            amount=Decimal("5.00"),
            paid_by="Bob",
            participants=["Bob"],
        ),
    ]
    settlements = settle_debts(expenses)
    assert len(settlements) == 0, f"Expected 0 settlements, got {len(settlements)}"


def test_settle_multiple_expenses():
    """Multiple expenses, cross-owed."""
    expenses = [
        Expense(
            description="Dinner",
            amount=Decimal("60.00"),
            paid_by="Alice",
            participants=["Alice", "Bob", "Carol"],
            id="e1",
        ),
        Expense(
            description="Groceries",
            amount=Decimal("30.00"),
            paid_by="Bob",
            participants=["Alice", "Bob"],
            id="e2",
        ),
        Expense(
            description="Uber",
            amount=Decimal("18.00"),
            paid_by="Carol",
            participants=["Alice", "Bob", "Carol"],
            id="e3",
        ),
    ]
    settlements = settle_debts(expenses)

    # Alice paid 60, owes (60/3=20) + (30/2=15) + (18/3=6) = 41, net: 60-41 = +19
    # Bob paid 30, owes 20 + 15 + 6 = 41, net: 30-41 = -11
    # Carol paid 18, owes 20 + 0 + 6 = 26, net: 18-26 = -8
    # Bob owes 11, Carol owes 8, so Bob owes Alice 11, Carol owes Alice 8

    total_owed = sum(s.amount for s in settlements)
    assert total_owed == Decimal("19.00"), f"Expected total 19.00, got {total_owed}"

    # Verify every settlement goes to Alice
    for s in settlements:
        assert s.to_person == "Alice", f"Expected Alice, got {s.to_person}"


def test_settle_uneven_split():
    """Alice paid for dinner but Carol wasn't eating — only split between Alice and Bob."""
    expenses = [
        Expense(
            description="Sushi",
            amount=Decimal("50.00"),
            paid_by="Alice",
            participants=["Alice", "Bob"],
        )
    ]
    settlements = settle_debts(expenses)
    assert len(settlements) == 1
    assert settlements[0].from_person == "Bob"
    assert settlements[0].amount == Decimal("25.00")


def test_format_report():
    """Report formatting works."""
    expenses = [
        Expense(
            description="Dinner",
            amount=Decimal("40.00"),
            paid_by="Alice",
            participants=["Alice", "Bob"],
        )
    ]
    settlements = settle_debts(expenses)
    report = format_report(expenses, settlements)
    assert "Dinner" in report
    assert "Bob owes Alice" in report
    assert "$20.00" in report


def test_balances_rounding():
    """Verify rounding doesn't create phantom debts for small amounts."""
    # Three people splitting $10.00 — each owes $3.333...
    expenses = [
        Expense(
            description="Snacks",
            amount=Decimal("10.00"),
            paid_by="Alice",
            participants=["Alice", "Bob", "Carol"],
        )
    ]
    settlements = settle_debts(expenses)
    # Each of Bob and Carol owes Alice approx $3.33
    total = sum(s.amount for s in settlements)
    # Should be very close to $6.67 (what Alice is owed)
    assert abs(total - Decimal("6.67")) < Decimal("0.02"), f"Total off: {total}"


def test_no_expenses():
    """Empty list returns empty settlements."""
    assert settle_debts([]) == []


def test_single_person_pays_self():
    """Paying for yourself creates no settlement."""
    expenses = [
        Expense(
            description="My coffee",
            amount=Decimal("5.00"),
            paid_by="Alice",
            participants=["Alice"],
        )
    ]
    assert settle_debts(expenses) == []