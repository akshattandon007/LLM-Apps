"""Tests for DebtSlayer data models."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from debtslayer.models import Debt, PayoffPlan, SpendingProfile, CreditorLetter


def test_debt_creation():
    d = Debt(label="Visa", balance=4500, apr=22.99, min_payment=50)
    assert d.label == "Visa"
    assert d.balance == 4500
    assert d.apr == 22.99
    assert d.min_payment == 50


def test_debt_monthly_interest():
    d = Debt(label="MC", balance=3200, apr=18.0, min_payment=40)
    expected = 3200 * (18.0 / 100 / 12)
    assert abs(d.monthly_interest - expected) < 0.01


def test_debt_validation():
    import pytest
    Debt(label="Test", balance=0, apr=5, min_payment=0)  # zero balance ok
    Debt(label="Test", balance=100, apr=0, min_payment=10)  # 0% APR ok
    with pytest.raises(AssertionError):
        Debt(label="Neg", balance=-1, apr=5, min_payment=10)


def test_debt_json_roundtrip():
    d = Debt(label="StudentLoan", balance=15000, apr=5.5, min_payment=200)
    data = d.to_json()
    d2 = Debt.from_json(data)
    assert d == d2


def test_spending_profile_surplus():
    sp = SpendingProfile(income=5000, expenses=3000)
    assert sp.surplus == 2000


def test_spending_profile_deficit():
    sp = SpendingProfile(income=2000, expenses=2500)
    assert sp.deficit is True
    assert sp.surplus == 0


def test_creditor_letter_text():
    letter = CreditorLetter(
        creditor_name="Visa",
        balance=4500,
        apr=22.99,
        hardship_reason="reduced hours",
        body="Test body content",
    )
    text = letter.to_text()
    assert "Visa" in text
    assert "Test body content" in text
    assert "DebtSlayer" in text