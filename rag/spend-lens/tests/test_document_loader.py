"""
tests/test_document_loader.py
──────────────────────────────
Unit tests for the SpendLens document_loader module.
Tests CSV parsing, transaction normalisation, and document chunking.
"""

import io
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_loader import (
    Transaction,
    _clean_description,
    _guess_category,
    _parse_amount,
    _parse_date,
    load_transactions,
    parse_csv_statement,
    transactions_to_documents,
)


# ─── _parse_amount ────────────────────────────────────────────────────────────


def test_parse_amount_positive():
    assert _parse_amount("$1,234.56") == 1234.56


def test_parse_amount_negative_dollar():
    assert _parse_amount("-$45.00") == -45.0


def test_parse_amount_paren_negative():
    assert _parse_amount("(99.99)") == -99.99


def test_parse_amount_plain():
    assert _parse_amount("500") == 500.0


def test_parse_amount_empty():
    assert _parse_amount("") == 0.0


def test_parse_amount_none():
    assert _parse_amount(None) == 0.0


# ─── _parse_date ──────────────────────────────────────────────────────────────


def test_parse_date_iso():
    assert _parse_date("2025-01-15") == "2025-01-15"


def test_parse_date_us_slash():
    assert _parse_date("01/15/2025") == "2025-01-15"


def test_parse_date_us_slash_short_year():
    assert _parse_date("01/15/25") == "2025-01-15"


def test_parse_date_month_name():
    assert _parse_date("Jan 15, 2025") == "2025-01-15"


def test_parse_date_dash():
    assert _parse_date("01-15-2025") == "2025-01-15"


def test_parse_date_invalid():
    assert _parse_date("not a date") == ""


def test_parse_date_empty():
    assert _parse_date("") == ""


# ─── _clean_description ───────────────────────────────────────────────────────


def test_clean_description_strips_prefixes():
    assert _clean_description("DEBIT CARD PURCHASE STARBUCKS") == "STARBUCKS"


def test_clean_description_collapses_whitespace():
    assert _clean_description("  Amazon   Prime   ") == "Amazon Prime"


def test_clean_description_none():
    assert _clean_description(None) == ""


# ─── _guess_category ──────────────────────────────────────────────────────────


def test_guess_category_coffee():
    assert _guess_category("STARBUCKS COFFEE #12345") == "Dining"


def test_guess_category_grocery():
    assert _guess_category("WHOLE FOODS MARKET") == "Groceries"


def test_guess_category_transport():
    assert _guess_category("UBER TRIP") == "Transport"


def test_guess_category_shopping():
    assert _guess_category("AMAZON.COM PURCHASE") == "Shopping"


def test_guess_category_subscription():
    assert _guess_category("NETFLIX SUBSCRIPTION") == "Entertainment"


def test_guess_category_uncategorised():
    assert _guess_category("RANDOM XYZ THING 42") == "Uncategorised"


# ─── Transaction dataclass ────────────────────────────────────────────────────


def test_transaction_to_document_text():
    tx = Transaction(
        date="2025-01-15",
        description="STARBUCKS COFFEE",
        amount=-5.75,
        category="Dining",
    )
    text = tx.to_document_text()
    assert "STARBUCKS COFFEE" in text
    assert "2025-01-15" in text
    assert "$5.75" in text
    assert "debit" in text
    assert "Dining" in text


def test_transaction_to_metadata():
    tx = Transaction(
        date="2025-01-15",
        description="NETFLIX",
        amount=-15.99,
        category="Entertainment",
        source_file="chase.csv",
    )
    meta = tx.to_metadata()
    assert meta["date"] == "2025-01-15"
    assert meta["description"] == "NETFLIX"
    assert meta["amount"] == -15.99
    assert meta["category"] == "Entertainment"
    assert meta["month"] == "2025-01"


# ─── CSV parsing ──────────────────────────────────────────────────────────────


SAMPLE_CSV = """Date,Description,Amount,Category
2025-01-15,STARBUCKS COFFEE,-5.75,Dining
2025-01-16,WHOLE FOODS,-89.42,Groceries
2025-01-17,NETFLIX SUBSCRIPTION,-15.99,Entertainment
2025-01-18,UBER TRIP,-24.50,Transport
2025-01-19,AMAZON PRIME,-14.99,Subscription
2025-01-20,DIRECT DEPOSIT SALARY,3500.00,Income
"""


def test_parse_csv_statement():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(SAMPLE_CSV)
        tmp_path = f.name

    try:
        txs = parse_csv_statement(tmp_path)
        assert len(txs) == 6

        # Check categories were preserved from CSV
        cats = {tx.description: tx.category for tx in txs}
        assert cats["STARBUCKS COFFEE"] == "Dining"
        assert cats["WHOLE FOODS"] == "Groceries"
        assert cats["DIRECT DEPOSIT SALARY"] == "Income"

        # Check amounts
        amounts = {tx.description: tx.amount for tx in txs}
        assert amounts["STARBUCKS COFFEE"] == -5.75
        assert amounts["DIRECT DEPOSIT SALARY"] == 3500.0

        # Check dates
        assert txs[0].date == "2025-01-15"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ─── CSV with different column names ──────────────────────────────────────────


ALT_CSV = """Transaction Date,Merchant,Debit,Credit
2025-02-01,TRADER JOES,45.00,
2025-02-02,PAYPAL DEPOSIT,,200.00
2025-02-03,SHELL GAS,60.00,
"""


def test_parse_csv_alternate_columns():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(ALT_CSV)
        tmp_path = f.name

    try:
        txs = parse_csv_statement(tmp_path)
        assert len(txs) == 3

        # Debit should be negative
        assert txs[0].amount == -45.0

        # Credit should be positive
        assert txs[1].amount == 200.0

        # Auto-category detection
        assert txs[0].category == "Groceries"  # Trader Joes
        assert txs[2].category == "Transport"  # Shell gas
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ─── load_transactions (auto-detect file type) ────────────────────────────────


def test_load_transactions_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(SAMPLE_CSV)
        tmp_path = f.name

    try:
        txs = load_transactions(tmp_path)
        assert len(txs) == 6
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_load_transactions_unsupported():
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_transactions("data.xlsx")


# ─── transactions_to_documents ────────────────────────────────────────────────


def test_transactions_to_documents():
    txs = [
        Transaction(date="2025-01-15", description="STARBUCKS", amount=-5.75, category="Dining"),
        Transaction(date="2025-01-16", description="UBER", amount=-24.50, category="Transport"),
        Transaction(date="2025-02-01", description="NETFLIX", amount=-15.99, category="Entertainment"),
    ]
    docs = transactions_to_documents(txs, group_by_month=True)
    # 3 individual docs + 2 monthly summaries = 5
    assert len(docs) == 5

    # Check monthly summary exists for January
    jan_doc = [d for d in docs if d.metadata.get("type") == "monthly_summary" and d.metadata["month"] == "2025-01"]
    assert len(jan_doc) == 1
    assert jan_doc[0].metadata["transaction_count"] == 2

    # Check individual docs have correct metadata
    individual = [d for d in docs if d.metadata.get("type") != "monthly_summary"]
    assert len(individual) == 3
    for doc in individual:
        assert "date" in doc.metadata
        assert "amount" in doc.metadata
        assert "category" in doc.metadata


def test_transactions_to_documents_no_grouping():
    txs = [
        Transaction(date="2025-01-15", description="TEST", amount=-5.00, category="Test"),
    ]
    docs = transactions_to_documents(txs, group_by_month=False)
    # Just the individual doc, no monthly summary
    assert len(docs) == 1
