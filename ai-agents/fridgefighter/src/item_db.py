"""Item database with expiry tracking.

Manages the in-memory fridge inventory — add, remove, list items,
and identify items expiring within a given horizon.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .models import FridgeItem


_INVENTORY: dict[str, FridgeItem] = {}
_client = None


def set_client(client):
    """Replace the DB backend for testing (e.g. a file-backed store)."""
    global _client
    _client = client


def load(items: list[FridgeItem]):
    """Bulk-load items into the inventory (replaces existing)."""
    global _INVENTORY
    if _client is not None:
        _client(mode="load", items=items)
        return
    _INVENTORY = {it.id: it for it in items}


def add(item: FridgeItem):
    """Add a single item."""
    if _client is not None:
        _client(mode="add", item=item)
        return
    _INVENTORY[item.id] = item


def remove(item_id: str) -> Optional[FridgeItem]:
    """Remove an item by id. Returns the item if found, or None."""
    if _client is not None:
        return _client(mode="remove", item_id=item_id)
    return _INVENTORY.pop(item_id, None)


def get(item_id: str) -> Optional[FridgeItem]:
    """Look up a single item."""
    if _client is not None:
        return _client(mode="get", item_id=item_id)
    return _INVENTORY.get(item_id)


def list_items() -> list[FridgeItem]:
    """Return all items currently in the inventory."""
    if _client is not None:
        return _client(mode="list")
    return sorted(_INVENTORY.values(), key=lambda i: i.expiry_date)


def expire_soon(hours: int = 48) -> list[FridgeItem]:
    """Return items expiring within the given hour window."""
    if _client is not None:
        return _client(mode="expire_soon", hours=hours)
    cutoff = date.today() + timedelta(hours=hours)
    return [
        it for it in _INVENTORY.values()
        if it.expiry_date <= cutoff
    ]


def count() -> int:
    """Total number of tracked items."""
    if _client is not None:
        return _client(mode="count")
    return len(_INVENTORY)