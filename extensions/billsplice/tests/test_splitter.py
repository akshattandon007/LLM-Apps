"""Tests for BillSplice splitter logic."""

from decimal import Decimal
from billsplice.models import Bill, Item, Person, SplitResult
from billsplice.splitter import split_bill


def test_single_person_everything():
    """One person, all items assigned to them, no tax/tip."""
    bill = Bill(
        items=[
            Item(name="Pizza", price=Decimal("24.50")),
            Item(name="Fries", price=Decimal("8.00")),
        ],
        people=[Person(name="Alice")],
    )
    bill.people[0].items = bill.items[:]
    results = split_bill(bill)
    assert len(results) == 1
    assert results[0].person_name == "Alice"
    assert results[0].subtotal == Decimal("32.50")
    assert results[0].tax_share == Decimal("0.00")
    assert results[0].tip_share == Decimal("0.00")
    assert results[0].total == Decimal("32.50")


def test_two_people_separate_items():
    """Two people, each with their own items, no tax/tip."""
    bill = Bill(
        items=[
            Item(name="Pizza", price=Decimal("20.00")),
            Item(name="Salad", price=Decimal("12.00")),
        ],
        people=[Person(name="Alice"), Person(name="Bob")],
    )
    bill.people[0].items = [bill.items[0]]
    bill.people[1].items = [bill.items[1]]
    results = split_bill(bill)
    assert len(results) == 2
    assert results[0].subtotal == Decimal("20.00")
    assert results[1].subtotal == Decimal("12.00")
    assert results[0].total == Decimal("20.00")
    assert results[1].total == Decimal("12.00")


def test_with_tax_and_tip():
    """Items split with tax and tip prorated proportionally."""
    bill = Bill(
        items=[
            Item(name="Steak", price=Decimal("45.00")),
            Item(name="Pasta", price=Decimal("22.00")),
        ],
        tax_percent=Decimal("8.875"),
        tip_percent=Decimal("18.0"),
        people=[Person(name="Alice"), Person(name="Bob")],
    )
    bill.people[0].items = [bill.items[0]]
    bill.people[1].items = [bill.items[1]]
    results = split_bill(bill)

    subtotal = Decimal("67.00")
    tax_expected = subtotal * Decimal("0.08875")
    tip_expected = subtotal * Decimal("0.18")
    total_expected = subtotal + tax_expected + tip_expected

    assert bill.subtotal == subtotal
    assert bill.tax_amount == tax_expected.quantize(Decimal("0.01"))
    assert bill.tip_amount == tip_expected.quantize(Decimal("0.01"))

    # Alice had $45 of $67 ≈ 67.16%
    assert results[0].subtotal == Decimal("45.00")
    assert results[0].tax_share > Decimal("0")
    assert results[0].tip_share > Decimal("0")
    assert results[0].total > Decimal("45.00")

    # Bob had $22 of $67 ≈ 32.84%
    assert results[1].subtotal == Decimal("22.00")
    assert results[1].tax_share > Decimal("0")
    assert results[1].tip_share > Decimal("0")
    assert results[1].total > Decimal("22.00")

    # Sum of totals should equal the bill total (within rounding)
    combined_total = results[0].total + results[1].total
    assert combined_total == bill.total or abs(combined_total - bill.total) <= Decimal("0.02")


def test_shared_items():
    """Shared items divided equally among all people."""
    bill = Bill(
        items=[
            Item(name="Pizza", price=Decimal("30.00")),
            Item(name="Shared Fries", price=Decimal("10.00"), shared=True),
        ],
        people=[Person(name="Alice"), Person(name="Bob"), Person(name="Carol")],
    )
    bill.people[0].items = [bill.items[0]]
    bill.people[1].items = []
    bill.people[2].items = []

    results = split_bill(bill)
    assert len(results) == 3

    # Alice: $30 + $3.33 (1/3 of $10) = $33.33
    # Bob: $3.33
    # Carol: $3.34 (rounding makes this $3.34)
    # Total: $33.33 + $3.33 + $3.34 = $40.00
    assert results[0].subtotal == Decimal("33.33"), f"Alice got {results[0].subtotal}"
    # Shared item rounding — 2 people get $3.33, one gets $3.34
    shared_totals = sorted(r.subtotal for r in results)
    assert shared_totals[0] == Decimal("3.33")
    assert shared_totals[1] == Decimal("3.33")
    assert shared_totals[2] == Decimal("33.33")


def test_no_items():
    """Empty bill returns zero results for all people (not empty)."""
    bill = Bill(people=[Person(name="Alice")])
    results = split_bill(bill)
    assert len(results) == 1
    assert results[0].total == Decimal("0.00")


def test_no_people():
    """No people returns empty list."""
    bill = Bill(items=[Item(name="Pizza", price=Decimal("10.00"))])
    assert split_bill(bill) == []


def test_zero_subtotal():
    """Zero-priced items with tax/tip should not cause division errors."""
    bill = Bill(
        items=[Item(name="Water", price=Decimal("0.00"))],
        tax_percent=Decimal("10"),
        tip_percent=Decimal("10"),
        people=[Person(name="Alice")],
    )
    bill.people[0].items = bill.items[:]
    results = split_bill(bill)
    assert len(results) == 1
    assert results[0].total == Decimal("0.00")


def test_three_way_equal_split():
    """Equal split of shared items among three."""
    bill = Bill(
        items=[Item(name="Family Platter", price=Decimal("60.00"), shared=True)],
        people=[Person(name="X"), Person(name="Y"), Person(name="Z")],
    )
    results = split_bill(bill)
    totals = {r.person_name: r.subtotal for r in results}
    # $60 / 3 = $20 each
    assert totals["X"] == Decimal("20.00")
    assert totals["Y"] == Decimal("20.00")
    assert totals["Z"] == Decimal("20.00")