"""Simulated fridge item detection.

No real camera or vision API needed for MVP. The simulator returns
a reproducible set of fridge items based on a seed or random state.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

from .models import FridgeItem


# -- Seed inventory templates --
_CATEGORIES = {
    "dairy": [
        ("Milk (whole)", "ml", 1000, 7),
        ("Greek yogurt", "g", 500, 10),
        ("Cheddar cheese block", "g", 250, 21),
        ("Butter", "g", 250, 30),
        ("Cream cheese", "g", 200, 14),
        ("Sour cream", "g", 300, 10),
    ],
    "produce": [
        ("Lettuce", "pieces", 1, 5),
        ("Tomatoes", "pieces", 4, 4),
        ("Cucumber", "pieces", 2, 7),
        ("Bananas", "pieces", 5, 3),
        ("Apples (red)", "pieces", 3, 10),
        ("Avocado", "pieces", 1, 2),
        ("Spinach bag", "g", 200, 5),
        ("Bell peppers", "pieces", 2, 7),
    ],
    "condiment": [
        ("Ketchup", "ml", 500, 180),
        ("Mustard (Dijon)", "ml", 200, 180),
        ("Soy sauce", "ml", 300, 365),
        ("Olive oil", "ml", 750, 365),
        ("Hot sauce", "ml", 150, 365),
    ],
    "meat": [
        ("Chicken breasts", "g", 500, 4),
        ("Ground beef", "g", 400, 3),
        ("Bacon", "g", 200, 7),
        ("Sausages", "pieces", 6, 7),
    ],
    "beverage": [
        ("Orange juice", "ml", 900, 10),
        ("Sparkling water", "ml", 750, 365),
        ("Beer (IPA)", "ml", 355, 180),
    ],
    "frozen": [
        ("Frozen peas", "g", 500, 180),
        ("Ice cream (vanilla)", "ml", 500, 90),
        ("Frozen pizza", "pieces", 1, 180),
    ],
    "pantry": [
        ("Pasta (spaghetti)", "g", 500, 365),
        ("Rice (basmati)", "g", 1000, 365),
        ("Canned tomatoes", "ml", 400, 365),
        ("Peanut butter", "g", 250, 90),
        ("Honey", "g", 500, 365),
    ],
}


def _pick_items(
    seed: Optional[int] = None,
    count: int = 8,
    expiring_bias: float = 0.3,
) -> list[FridgeItem]:
    """Return a simulated fridge inventory.

    Parameters
    ----------
    seed : int or None
        Random seed for reproducibility.
    count : int
        Number of items to return.
    expiring_bias : float
        Probability (0-1) an item is near expiry. Higher = more
        expiring items, making challenges more interesting.

    Returns
    -------
    list[FridgeItem]
    """
    rng = random.Random(seed)

    # Flatten all items with category
    all_templates = []
    for category, items in _CATEGORIES.items():
        for name, unit, qty, days in items:
            all_templates.append((category, name, unit, qty, days))

    rng.shuffle(all_templates)
    selected = all_templates[: min(count, len(all_templates))]

    items: list[FridgeItem] = []
    today = date.today()

    for idx, (category, name, unit, qty, default_days) in enumerate(selected):
        # Decide if this item is expiring soon
        if rng.random() < expiring_bias:
            # 2-7 days
            days_until_expiry = rng.randint(1, 7)
        else:
            # Default shelf life but vary slightly
            days_until_expiry = max(1, default_days + rng.randint(-3, 3))

        expiry_date = today + timedelta(days=days_until_expiry)

        items.append(
            FridgeItem(
                id=f"item-{idx + 1:03d}",
                name=name,
                category=category,
                quantity=rng.randint(1, 3),
                unit=unit if unit in ("pieces",) else unit,
                expiry_date=expiry_date,
                confidence=round(rng.uniform(0.75, 0.99), 2),
                added_date=today - timedelta(days=rng.randint(0, days_until_expiry)),
            )
        )

    return items


# -- Injected _client for testability (future: real API client) --
_client = None


def set_client(client):
    """Replace the vision client for testing.

    Accepts any callable ``client(**kwargs) -> list[FridgeItem]``.
    """
    global _client
    _client = client


def scan(
    image_path: Optional[str] = None,
    seed: Optional[int] = None,
    count: int = 8,
) -> list[FridgeItem]:
    """Scan a fridge image and return detected items.

    In simulated mode (default), returns a reproducible set of
    mock items.  Pass a real ``set_client(client)`` to use a
    production vision API.

    Parameters
    ----------
    image_path : str or None
        Not used in simulated mode.
    seed : int or None
        Random seed for reproducibility.
    count : int
        Approximate number of items to detect.

    Returns
    -------
    list[FridgeItem]
    """
    if _client is not None:
        return _client(image_path=image_path, count=count)

    return _pick_items(seed=seed, count=count)