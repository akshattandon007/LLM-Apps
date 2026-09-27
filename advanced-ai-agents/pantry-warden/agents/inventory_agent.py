"""InventoryAgent — tracks and manages pantry contents."""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

from pydantic import BaseModel


class PantryItem(BaseModel):
    """A single item in the pantry."""
    name: str
    quantity: float
    unit: str
    category: str = "other"
    added_date: str = ""
    expiry_date: str = ""
    min_quantity: float = 0.0  # auto-reorder threshold


class InventoryAgent:
    """Specialized agent that manages pantry inventory.

    Capabilities:
    - Track current pantry contents
    - Detect low-stock items needing restock
    - Flag expiring items
    - Add/remove/update items
    - Answer queries about what's available
    """

    def __init__(self, data_path: str = ""):
        self.items: Dict[str, PantryItem] = {}
        self.data_path = data_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "pantry_data.json"
        )
        self._load()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add_item(self, name: str, quantity: float, unit: str = "unit",
                 category: str = "other",
                 expiry_days: int = 0) -> PantryItem:
        """Add a new item or increase quantity of existing item."""
        name = name.lower().strip()
        now = datetime.now().strftime("%Y-%m-%d")
        expiry = ""
        if expiry_days > 0:
            expiry = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")

        if name in self.items:
            item = self.items[name]
            item.quantity += quantity
            if expiry and (not item.expiry_date or expiry < item.expiry_date):
                item.expiry_date = expiry
        else:
            item = PantryItem(
                name=name, quantity=quantity, unit=unit,
                category=category, added_date=now, expiry_date=expiry,
                min_quantity=0.5
            )
            self.items[name] = item
        self._save()
        return item

    def remove_item(self, name: str, quantity: float) -> bool:
        """Remove quantity from pantry. Returns False if insufficient."""
        name = name.lower().strip()
        if name not in self.items:
            return False
        item = self.items[name]
        if item.quantity < quantity:
            return False
        item.quantity -= quantity
        if item.quantity <= 0:
            del self.items[name]
        self._save()
        return True

    def get_item(self, name: str) -> PantryItem | None:
        return self.items.get(name.lower().strip())

    def list_items(self) -> List[PantryItem]:
        return sorted(self.items.values(), key=lambda x: x.name)

    # ── Smart queries ─────────────────────────────────────────────────────────

    def get_low_stock_items(self) -> List[PantryItem]:
        """Items below their reorder threshold."""
        return [i for i in self.items.values()
                if i.quantity <= i.min_quantity and i.min_quantity > 0]

    def get_expiring_items(self, within_days: int = 7) -> List[PantryItem]:
        """Items expiring within N days."""
        if not within_days:
            return []
        now = datetime.now()
        cutoff = now + timedelta(days=within_days)
        results = []
        for item in self.items.values():
            if item.expiry_date:
                try:
                    exp = datetime.strptime(item.expiry_date, "%Y-%m-%d")
                    if now <= exp <= cutoff:
                        results.append(item)
                except ValueError:
                    pass
        return results

    def available_ingredients(self, needed: List[str]) -> Dict[str, float]:
        """Check which needed ingredients are available and their quantity."""
        found = {}
        for ing in needed:
            ing_lower = ing.lower().strip()
            if ing_lower in self.items:
                found[ing] = self.items[ing_lower].quantity
        return found

    def get_category_summary(self) -> Dict[str, int]:
        """Count of items per category."""
        summary: Dict[str, int] = {}
        for item in self.items.values():
            summary[item.category] = summary.get(item.category, 0) + 1
        return summary

    def estimate_meal_coverage(self, recipe_ingredients: List[str]) -> float:
        """What fraction of recipe ingredients are in stock (0.0–1.0)."""
        if not recipe_ingredients:
            return 0.0
        matched = sum(1 for ing in recipe_ingredients
                      if ing.lower().strip() in self.items)
        return matched / len(recipe_ingredients)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path) as f:
                    data = json.load(f)
                self.items = {k: PantryItem(**v) for k, v in data.items()}
            except (json.JSONDecodeError, KeyError):
                self.items = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w") as f:
            data = {k: v.model_dump() for k, v in self.items.items()}
            json.dump(data, f, indent=2)