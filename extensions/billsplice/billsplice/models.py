"""
BillSplice data models.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List


@dataclass
class Item:
    """A single menu item ordered."""
    name: str
    price: Decimal
    shared: bool = False  # True if split equally among all


@dataclass
class Person:
    """A person sharing the bill."""
    name: str
    items: List[Item] = field(default_factory=list)

    @property
    def subtotal(self) -> Decimal:
        return sum((i.price for i in self.items), Decimal("0.00"))


@dataclass
class Bill:
    """The full bill to split."""
    items: List[Item] = field(default_factory=list)
    tax_percent: Decimal = Decimal("0.00")
    tip_percent: Decimal = Decimal("0.00")
    people: List[Person] = field(default_factory=list)

    @property
    def subtotal(self) -> Decimal:
        return sum((i.price for i in self.items), Decimal("0.00"))

    @property
    def tax_amount(self) -> Decimal:
        return (self.subtotal * self.tax_percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def tip_amount(self) -> Decimal:
        return (self.subtotal * self.tip_percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax_amount + self.tip_amount


@dataclass
class SplitResult:
    """Result of splitting a bill among people."""
    person_name: str
    items: List[Item]
    subtotal: Decimal
    tax_share: Decimal
    tip_share: Decimal
    total: Decimal