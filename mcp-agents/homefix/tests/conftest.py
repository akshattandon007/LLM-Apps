"""Pytest fixtures with mock professional data, reviews, and pricing."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from src.models import Pro, ServiceType


@pytest.fixture
def sample_pro():
    """A typical licensed pro fixture."""
    return Pro(
        name="Rapid Rooter Plumbing",
        company="Rapid Rooter LLC",
        service_types=[ServiceType.plumber],
        phone="+1-555-0101",
        zip_code="10001",
        rating=4.7,
        review_count=203,
        years_in_business=12,
        licensed=True,
        insured=True,
        bonded=True,
        available_now=True,
    )


@pytest.fixture
def sample_electrician():
    return Pro(
        name="BrightSpark Electric",
        company="BrightSpark Co",
        service_types=[ServiceType.electrician],
        phone="+1-555-0103",
        zip_code="10001",
        rating=4.8,
        review_count=312,
        years_in_business=18,
        licensed=True,
        insured=True,
        bonded=True,
        available_now=True,
    )


@pytest.fixture
def sample_handyman():
    return Pro(
        name="Ace Handyman Services",
        company="Ace Handyman LLC",
        service_types=[ServiceType.handyman],
        phone="+1-555-0107",
        zip_code="10001",
        rating=4.4,
        review_count=95,
        years_in_business=7,
        licensed=False,
        insured=True,
        bonded=False,
        available_now=False,
    )


@pytest.fixture
def all_pros():
    """Full list of mock pros."""
    from src.service_db import MOCK_PROS
    return list(MOCK_PROS)


@pytest.fixture
def sample_zip_code():
    return "10001"


@pytest.fixture
def sample_description():
    return "Burst pipe in basement, need emergency repair"