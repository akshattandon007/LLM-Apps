"""Test fixtures with mock companies, issues, and rights."""

from __future__ import annotations

import pytest

from src.models import Country, IssueType


@pytest.fixture
def mock_company_british_airways() -> str:
    return "British Airways"


@pytest.fixture
def mock_company_bank() -> str:
    return "Chase"


@pytest.fixture
def mock_company_unknown() -> str:
    return "WidgetCorp"


@pytest.fixture
def mock_issue_delayed_flight() -> str:
    return (
        "Flight BA123 from London Heathrow to New York JFK on March 1, 2026 "
        "was delayed by 6 hours. The airline provided no meal vouchers or "
        "accommodation. I was rebooked on a later flight and arrived 8 hours late."
    )


@pytest.fixture
def mock_issue_defective_product() -> str:
    return (
        "Purchased a laptop on January 15, 2026 for $1,200. The screen developed "
        "dead pixels within 2 weeks. The manufacturer refuses to repair it, "
        "claiming 'physical damage' which I dispute."
    )


@pytest.fixture
def mock_issue_overcharge() -> str:
    return (
        "My utility company charged me $450 for a month when my typical bill is "
        "$120. They claim it's 'estimated usage' but refuse to provide a meter "
        "reading or correct the bill."
    )


@pytest.fixture
def mock_issue_landlord() -> str:
    return (
        "My landlord has not fixed the boiler for 3 weeks despite multiple "
        "requests. It is mid-winter and I have no heating or hot water. The "
        "property is becoming uninhabitable."
    )


@pytest.fixture
def expected_issue_types() -> list[str]:
    return [member.value for member in IssueType]


@pytest.fixture
def expected_countries() -> list[str]:
    return [member.value for member in Country]
