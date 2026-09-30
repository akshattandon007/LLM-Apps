"""
JSON-based persistence for expenses.
"""

from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List

from .core import Expense


class DecimalEncoder(json.JSONEncoder):
    """Serialize Decimal to float for JSON."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def expense_to_dict(e: Expense) -> dict:
    return {
        "id": e.id,
        "description": e.description,
        "amount": float(e.amount),
        "paid_by": e.paid_by,
        "participants": e.participants,
        "date": e.date,
    }


def dict_to_expense(d: dict) -> Expense:
    return Expense(
        id=d["id"],
        description=d.get("description", ""),
        amount=Decimal(str(d["amount"])),
        paid_by=d["paid_by"],
        participants=d.get("participants", []),
        date=d.get("date", date.today().isoformat()),
    )


def load_expenses(path: str | os.PathLike) -> List[Expense]:
    """Load expenses from a JSON file. Returns empty list if file doesn't exist."""
    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r") as f:
        data = json.load(f)
    return [dict_to_expense(item) for item in data]


def save_expenses(path: str | os.PathLike, expenses: List[Expense]) -> None:
    """Save expenses to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [expense_to_dict(e) for e in expenses]
    with open(p, "w") as f:
        json.dump(data, f, indent=2, cls=DecimalEncoder)