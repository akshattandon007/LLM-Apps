"""Pytest fixtures with mock fridge items and fake clients."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest

from src.models import Badge, FridgeItem, UserProfile

TODAY = date.today()


# -- Common mock items --
@pytest.fixture
def mock_items() -> list[FridgeItem]:
    """A reproducible set of fridge items with known expiry dates."""
    return [
        FridgeItem(
            id="item-001",
            name="Milk (whole)",
            category="dairy",
            quantity=1,
            unit="ml",
            expiry_date=TODAY + timedelta(days=2),
            confidence=0.95,
        ),
        FridgeItem(
            id="item-002",
            name="Greek yogurt",
            category="dairy",
            quantity=2,
            unit="g",
            expiry_date=TODAY + timedelta(days=1),  # expiring very soon
            confidence=0.90,
        ),
        FridgeItem(
            id="item-003",
            name="Tomatoes",
            category="produce",
            quantity=4,
            unit="pieces",
            expiry_date=TODAY + timedelta(days=4),
            confidence=0.85,
        ),
        FridgeItem(
            id="item-004",
            name="Chicken breasts",
            category="meat",
            quantity=2,
            unit="g",
            expiry_date=TODAY + timedelta(days=3),
            confidence=0.80,
        ),
        FridgeItem(
            id="item-005",
            name="Lettuce",
            category="produce",
            quantity=1,
            unit="pieces",
            expiry_date=TODAY + timedelta(days=5),
            confidence=0.75,
        ),
        FridgeItem(
            id="item-006",
            name="Avocado",
            category="produce",
            quantity=1,
            unit="pieces",
            expiry_date=TODAY + timedelta(days=1),  # expiring very soon
            confidence=0.88,
        ),
        FridgeItem(
            id="item-007",
            name="Cheddar cheese block",
            category="dairy",
            quantity=1,
            unit="g",
            expiry_date=TODAY + timedelta(days=21),
            confidence=0.92,
        ),
        FridgeItem(
            id="item-008",
            name="Ketchup",
            category="condiment",
            quantity=1,
            unit="ml",
            expiry_date=TODAY + timedelta(days=180),
            confidence=0.97,
        ),
    ]


@pytest.fixture
def expiring_soon_items() -> list[FridgeItem]:
    """Items that expire within 48 hours."""
    return [
        FridgeItem(
            id="item-exp-001",
            name="Bananas",
            category="produce",
            quantity=3,
            unit="pieces",
            expiry_date=TODAY + timedelta(hours=12),
            confidence=0.90,
        ),
        FridgeItem(
            id="item-exp-002",
            name="Sour cream",
            category="dairy",
            quantity=1,
            unit="g",
            expiry_date=TODAY + timedelta(hours=36),
            confidence=0.85,
        ),
    ]


@pytest.fixture
def empty_profile() -> UserProfile:
    """A blank user profile with no activity."""
    return UserProfile()


@pytest.fixture
def veteran_profile() -> UserProfile:
    """A user with a 10-day streak and some badges."""
    return UserProfile(
        current_streak=10,
        longest_streak=14,
        total_points=650,
        total_items_saved=25,
        challenges_completed=4,
        badges=[
            Badge(
                id="first_save",
                name="First Save",
                description="Save your first item",
                icon="🌱",
                earned_date=TODAY - timedelta(days=20),
            ),
            Badge(
                id="day_3",
                name="Weekend Warrior",
                description="3-day streak",
                icon="🔥",
                earned_date=TODAY - timedelta(days=14),
            ),
            Badge(
                id="day_7",
                name="Week Zero",
                description="7-day streak",
                icon="⭐",
                earned_date=TODAY - timedelta(days=7),
            ),
        ],
        last_active_date=TODAY - timedelta(days=1),
    )


# -- set_client() helpers --
@pytest.fixture(autouse=True)
def reset_clients():
    """Reset all module-level _client singletons between tests."""
    import src.vision
    import src.item_db
    import src.challenges
    import src.scoring

    src.vision._client = None
    src.item_db._client = None
    src.item_db._INVENTORY.clear()  # fresh state for every test
    src.challenges._client = None
    src.scoring._client = None