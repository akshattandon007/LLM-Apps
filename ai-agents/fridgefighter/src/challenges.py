"""Daily challenge generation.

Challenges are generated based on the user's current inventory,
prioritising items that are expiring soon.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

from .item_db import expire_soon, list_items
from .models import Challenge, FridgeItem


_client = None


def set_client(client):
    """Replace the challenge generator for testing."""
    global _client
    _client = client


_CHALLENGE_TEMPLATES = [
    {
        "title": "Emergency Use-Up",
        "description": "Use {count} item(s) expiring in the next 48 hours. "
        "Every item saved from the bin counts!",
        "points": 50,
        "min_expiring": 1,
        "uses_count": True,
    },
    {
        "title": "Zero-Waste Chef",
        "description": "Combine {count} expiring item(s) into a single meal. "
        "Bonus creativity points — make a stir-fry, frittata, or soup!",
        "points": 75,
        "min_expiring": 2,
        "uses_count": True,
        "combine": True,
    },
    {
        "title": "Freeze & Save",
        "description": "Freeze at least {count} item(s) that are about to expire. "
        "Extending shelf life counts as a save!",
        "points": 40,
        "min_expiring": 1,
        "uses_count": True,
    },
    {
        "title": "Leftover Remix",
        "description": "Use an already-opened item nearing expiry in a new recipe.",
        "points": 60,
        "min_expiring": 1,
        "uses_count": False,
    },
    {
        "title": "The Clean Plate",
        "description": "Finish everything in a single category ({category}) "
        "before anything expires.",
        "points": 80,
        "min_expiring": 0,
        "uses_count": False,
        "category": True,
    },
    {
        "title": "Triple Threat",
        "description": "Use three different items expiring within 48 hours. "
        "Maximum waste reduction!",
        "points": 100,
        "min_expiring": 3,
        "uses_count": False,
    },
    {
        "title": "Morning Routine",
        "description": "Use a breakfast item that's about to expire "
        "(fruit, dairy, juice) before it goes bad.",
        "points": 30,
        "min_expiring": 1,
        "uses_count": False,
        "breakfast": True,
    },
]


def generate(seed: Optional[int] = None) -> list[Challenge]:
    """Generate a set of challenges based on current fridge inventory.

    Returns a list of 1–3 challenges. At least one will target
    items expiring soon where possible.

    Parameters
    ----------
    seed : int or None
        Seed for deterministic generation (testing).
    """
    if _client is not None:
        return _client(seed=seed)

    rng = random.Random(seed)
    today = date.today()

    expiring = expire_soon(hours=48)
    all_items = list_items()

    # Pick candidate templates that match available inventory
    candidates = []
    for tpl in _CHALLENGE_TEMPLATES:
        if tpl["min_expiring"] > 0 and len(expiring) < tpl["min_expiring"]:
            continue  # not enough expiring items
        candidates.append(tpl)

    # Pick 1–3 challenges
    pick_count = min(rng.randint(1, 3), len(candidates))
    chosen = rng.sample(candidates, pick_count)

    challenges: list[Challenge] = []
    for idx, tpl in enumerate(chosen):
        # Pick target items from expiring list
        target_items = _pick_targets(expiring, tpl, rng)

        title = tpl["title"]
        description = tpl["description"]

        # Fill template variables
        if tpl.get("uses_count", False):
            count = min(len(target_items), max(1, len(target_items)))
            description = description.replace("{count}", str(count))
            title = title  # keep as-is
        else:
            description = description.replace("{count}", str(max(1, len(expiring))))

        # Fill category if template uses it
        if tpl.get("category"):
            cats = list({it.category for it in all_items})
            if cats:
                cat = rng.choice(cats)
                description = description.replace("{category}", cat)

        challenges.append(
            Challenge(
                id=f"challenge-{today.isoformat()}-{idx + 1:02d}",
                title=title,
                description=description.strip(),
                criteria={
                    "item_ids": [it.id for it in target_items],
                    "action": "use",
                    "count": len(target_items),
                    "combine": tpl.get("combine", False),
                },
                points=tpl["points"],
                date_assigned=today,
            )
        )

    return challenges


def _pick_targets(
    expiring: list[FridgeItem],
    template: dict,
    rng: random.Random,
) -> list[FridgeItem]:
    """Pick items from the expiring list matching the template."""
    if not expiring:
        return []

    count = min(rng.randint(1, len(expiring)), 5)

    # Pick items from different categories for variety
    items_by_cat: dict[str, list[FridgeItem]] = {}
    for it in expiring:
        items_by_cat.setdefault(it.category, []).append(it)

    available_cats = list(items_by_cat.keys())
    rng.shuffle(available_cats)

    picked: list[FridgeItem] = []
    cat_idx = 0
    while len(picked) < count and cat_idx < len(available_cats):
        cat = available_cats[cat_idx]
        item = rng.choice(items_by_cat[cat])
        if item not in picked:
            picked.append(item)
        cat_idx += 1
        if cat_idx >= len(available_cats):
            cat_idx = 0  # wrap around

    return picked[:count]