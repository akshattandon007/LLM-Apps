"""Fixtures with mock bank data for testing Subscription Slayer."""

import csv
import io
from datetime import date, timedelta
from typing import Any

import pytest

from src.models import Charge, CategorizedSub, Category, Frequency, Subscription


SAMPLE_CSV_HEADER = "Date,Description,Amount"
SAMPLE_CSV_DATA = """\
Date,Description,Amount
2025-01-01,SPOTIFY PREMIUM,10.99
2025-02-01,SPOTIFY PREMIUM,10.99
2025-03-01,SPOTIFY PREMIUM,10.99
2025-01-15,NETFLIX,15.49
2025-02-15,NETFLIX,15.49
2025-03-15,NETFLIX,15.49
2025-01-10,DISNEY PLUS,7.99
2025-02-10,DISNEY PLUS,7.99
2025-03-10,DISNEY PLUS,7.99
2025-01-05,AMAZON PRIME,14.99
2025-02-05,AMAZON PRIME,14.99
2025-03-05,AMAZON PRIME,14.99
2025-01-20,APPLE MUSIC,10.99
2025-02-20,APPLE MUSIC,10.99
2025-03-20,APPLE MUSIC,10.99
2025-01-03,Grocery Store - Weekly,45.30
2025-01-10,Grocery Store - Weekly,52.10
2025-02-15,Gas Station,38.50
2025-01-22,GOOGLE DRIVE,1.99
2025-02-22,GOOGLE DRIVE,1.99
2025-03-22,GOOGLE DRIVE,1.99
2025-01-08,HULU,7.99
2025-02-08,HULU,7.99
2025-01-08,One-off purchase - headphones,89.99
"""

MULTI_COL_CSV = """\
Transaction Date,Description,Debit,Credit
01/05/2025,SPOTIFY PREMIUM,10.99,
02/05/2025,SPOTIFY PREMIUM,10.99,
03/05/2025,SPOTIFY PREMIUM,10.99,
01/15/2025,NETFLIX,15.49,
02/15/2025,NETFLIX,15.49,
01/07/2025,Salary,,4500.00
"""


@pytest.fixture
def sample_csv_path(tmp_path):
    """Create a sample CSV file for testing."""
    path = tmp_path / "test_statement.csv"
    path.write_text(SAMPLE_CSV_DATA)
    return str(path)


@pytest.fixture
def sample_csv_content() -> str:
    return SAMPLE_CSV_DATA


@pytest.fixture
def multi_col_csv_path(tmp_path):
    """Multi-column format (Date, Description, Debit, Credit)."""
    path = tmp_path / "multi_col.csv"
    path.write_text(MULTI_COL_CSV)
    return str(path)


@pytest.fixture
def sample_charges() -> list[Charge]:
    """Pre-built charge list for testing detection/categorization."""
    today = date.today()
    return [
        Charge(date=today - timedelta(days=60), description="Spotify Premium", amount=10.99, merchant="spotify"),
        Charge(date=today - timedelta(days=30), description="Spotify Premium", amount=10.99, merchant="spotify"),
        Charge(date=today, description="Spotify Premium", amount=10.99, merchant="spotify"),
        Charge(date=today - timedelta(days=60), description="Netflix", amount=15.49, merchant="netflix"),
        Charge(date=today - timedelta(days=30), description="Netflix", amount=15.49, merchant="netflix"),
        Charge(date=today, description="Netflix", amount=15.49, merchant="netflix"),
        Charge(date=today - timedelta(days=60), description="Disney+", amount=7.99, merchant="disney+"),
        Charge(date=today - timedelta(days=30), description="Disney+", amount=7.99, merchant="disney+"),
        Charge(date=today - timedelta(days=60), description="Gas Station", amount=38.50),
        Charge(date=today, description="Grocery Store", amount=52.10),
    ]


@pytest.fixture
def sample_subscriptions() -> list[Subscription]:
    return [
        Subscription(merchant="Spotify", amount=10.99, frequency=Frequency.MONTHLY,
                     first_seen=date(2025, 1, 1), last_seen=date(2025, 3, 1), occurrences=3),
        Subscription(merchant="Netflix", amount=15.49, frequency=Frequency.MONTHLY,
                     first_seen=date(2025, 1, 15), last_seen=date(2025, 3, 15), occurrences=3),
        Subscription(merchant="Disney+", amount=7.99, frequency=Frequency.MONTHLY,
                     first_seen=date(2025, 1, 10), last_seen=date(2025, 3, 10), occurrences=3),
    ]


@pytest.fixture
def sample_categorized() -> list[CategorizedSub]:
    return [
        CategorizedSub(merchant="Spotify", amount=10.99, frequency=Frequency.MONTHLY,
                       category=Category.MUSIC, annual_cost=131.88),
        CategorizedSub(merchant="Netflix", amount=15.49, frequency=Frequency.MONTHLY,
                       category=Category.STREAMING, annual_cost=185.88),
        CategorizedSub(merchant="Disney+", amount=7.99, frequency=Frequency.MONTHLY,
                       category=Category.STREAMING, annual_cost=95.88),
        CategorizedSub(merchant="Apple Music", amount=10.99, frequency=Frequency.MONTHLY,
                       category=Category.MUSIC, annual_cost=131.88),
    ]