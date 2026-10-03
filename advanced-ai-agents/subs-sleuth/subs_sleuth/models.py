"""Shared data models for SubsSleuth."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Subscription:
    """A recurring subscription found in email or statements."""

    merchant: str
    amount: float | None = None
    currency: str = "USD"
    billing_url: str | None = None
    billing_phone: str | None = None
    frequency: str = "monthly"  # monthly, yearly, weekly
    last_charge_date: str | None = None
    next_charge_date: str | None = None
    source_email_date: str | None = None  # date of the receipt email
    source_email_subject: str | None = None
    source: str = "email"  # "email" | "statement" | "user_input"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CancellationGuide:
    """Step-by-step cancellation instructions for one subscription."""

    merchant: str
    cancellation_method: str = "website"  # "website" | "phone" | "email" | "app"
    steps: list[str] = field(default_factory=list)
    url: str | None = None
    phone_number: str | None = None
    notes: str | None = None
    difficulty: str = "medium"  # "easy" | "medium" | "hard"
    source: str = "research"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StatementLine:
    """One line from a bank/credit-card statement."""

    date: str
    description: str
    amount: float
    category: str | None = None
    source: str = "statement"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VerificationReport:
    """Comparison of subscriptions against statement charges."""

    merchant: str
    expected_amount: float | None = None
    found_on_statement: bool = False
    statement_amount: float | None = None
    statement_date: str | None = None
    match_confidence: str = "low"  # "high" | "medium" | "low"
    notes: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScanReport:
    """Complete output from a scanning pass."""

    subscriptions: list[Subscription] = field(default_factory=list)
    total_found: int = 0
    scan_date: str = field(default_factory=lambda: datetime.now().isoformat())
    email_count_checked: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FullReport:
    """Combined report from all three agents."""

    scan: ScanReport | None = None
    guides: list[CancellationGuide] = field(default_factory=list)
    verification: list[VerificationReport] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {}
        if self.scan:
            d["scan"] = self.scan.to_dict()
        d["guides"] = [g.to_dict() for g in self.guides]
        d["verification"] = [v.to_dict() for v in self.verification]
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)